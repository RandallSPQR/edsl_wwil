"""EDSL adapter layer for Two Truths and a Lie game.

This module wraps all EDSL interactions, providing:
- Consistent interface for model interactions
- Retry logic with exponential backoff
- Result parsing into domain objects
- Raw response preservation
- Direct API access for models not supported by EDSL proxy
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import wraps

from edsl import Agent, Model, QuestionFreeText
from dotenv import load_dotenv

from .config.schema import ModelConfig
from .logging_config import get_logger

# Load environment variables for direct API access
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


logger = get_logger("edsl_adapter")


class StoryGenerationError(Exception):
    """Error during story generation."""
    pass


class VerdictParsingError(Exception):
    """Error parsing verdict from LLM response."""
    pass


class QuestionGenerationError(Exception):
    """Error during question generation."""
    pass


class AnswerGenerationError(Exception):
    """Error during answer generation."""
    pass


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying operations with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")
            raise last_error
        return wrapper
    return decorator


class EDSLAdapter:
    """Adapter layer for all EDSL operations."""

    def __init__(self, config: Optional[ModelConfig] = None):
        """Initialize the adapter.

        Args:
            config: Default model configuration
        """
        self.default_config = config or ModelConfig()
        self._anthropic_client = None

    def _should_use_direct_api(self, model_name: str) -> bool:
        """Check if model should use direct API instead of EDSL proxy.

        Args:
            model_name: Name of the model

        Returns:
            True if should use direct API, False otherwise
        """
        # Models that fail with EDSL proxy but work with direct API
        direct_api_models = [
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-5-20250929",
        ]
        return model_name in direct_api_models

    def _should_skip_agent_traits(self, model_name: Optional[str] = None) -> bool:
        """Check if model doesn't work with EDSL agent traits.

        Args:
            model_name: Name of the model (optional, uses default if None)

        Returns:
            True if should skip agent traits, False otherwise
        """
        effective_model_name = model_name or self.default_config.name
        return any([
            "gemini" in effective_model_name.lower(),
            "llama" in effective_model_name.lower(),
            "meta-llama" in effective_model_name.lower(),
            "gpt-5" in effective_model_name.lower(),
            "o3" in effective_model_name.lower(),
            "o1" in effective_model_name.lower(),
            "opus-4-5" in effective_model_name.lower(),
            "claude-opus-4-5" in effective_model_name.lower(),
        ])

    def _get_anthropic_client(self):
        """Get or create Anthropic client for direct API access."""
        if self._anthropic_client is None:
            try:
                import anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")
                self._anthropic_client = anthropic.Anthropic(api_key=api_key)
                logger.info("Initialized Anthropic client for direct API access")
            except ImportError:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
        return self._anthropic_client

    def _call_anthropic_direct(
        self,
        prompt_text: str,
        model_name: str,
        temperature: float,
        agent_traits: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """Call Anthropic API directly, bypassing EDSL proxy.

        Args:
            prompt_text: The prompt text
            model_name: Claude model name
            temperature: Temperature setting
            agent_traits: Optional agent traits (will be prepended to prompt)

        Returns:
            Tuple of (response_text, metadata)
        """
        logger.info(f"Using direct Anthropic API for {model_name}")

        client = self._get_anthropic_client()

        # If agent traits provided, prepend them to the prompt
        if agent_traits:
            persona = agent_traits.get("persona", "")
            if persona:
                prompt_text = f"{persona}\n\n{prompt_text}"

        start_time = time.time()

        # Call Anthropic API
        message = client.messages.create(
            model=model_name,
            max_tokens=4096,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )

        end_time = time.time()

        response_text = message.content[0].text

        metadata = {
            "model": message.model,
            "usage": {
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            },
            "api_type": "direct_anthropic",
            "duration_seconds": end_time - start_time
        }

        logger.info(f"Direct API call completed in {metadata['duration_seconds']:.2f}s")

        return response_text, metadata

    def _create_model(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Model:
        """Create an EDSL Model instance.

        Args:
            model_name: Model name (uses default if not specified)
            temperature: Temperature (uses default if not specified)

        Returns:
            Configured Model instance
        """
        name = model_name or self.default_config.name
        temp = temperature if temperature is not None else self.default_config.temperature

        return Model(name, temperature=temp)

    def _create_agent(self, traits: Dict) -> Agent:
        """Create an EDSL Agent instance.

        Args:
            traits: Agent traits dictionary

        Returns:
            Configured Agent instance
        """
        return Agent(traits=traits)

    def _run_question(
        self,
        prompt_text: str,
        question_name: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        agent_traits: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """Run a single question through EDSL and get the response.

        Args:
            prompt_text: The prompt text
            question_name: Name for the question (for EDSL tracking)
            model_name: Model to use
            temperature: Temperature setting
            agent_traits: Optional agent traits

        Returns:
            Tuple of (response_text, metadata)
        """
        # Check if this model should use direct API instead of EDSL proxy
        effective_model_name = model_name or self.default_config.name
        effective_temperature = temperature if temperature is not None else self.default_config.temperature

        if self._should_use_direct_api(effective_model_name):
            return self._call_anthropic_direct(
                prompt_text=prompt_text,
                model_name=effective_model_name,
                temperature=effective_temperature,
                agent_traits=agent_traits
            )

        # Use EDSL proxy for other models
        model = self._create_model(model_name, temperature)

        question = QuestionFreeText(
            question_text=prompt_text,
            question_name=question_name
        )

        start_time = time.time()

        # Check if this model doesn't work with agent traits
        # Gemini, Llama, GPT-5, o3, and Opus 4.5 models fail with agent traits, so skip them
        effective_model_name = model_name or self.default_config.name
        skip_agent_traits = any([
            "gemini" in effective_model_name.lower(),
            "llama" in effective_model_name.lower(),
            "meta-llama" in effective_model_name.lower(),
            "gpt-5" in effective_model_name.lower(),
            "o3" in effective_model_name.lower(),
            "o1" in effective_model_name.lower(),
            "opus-4-5" in effective_model_name.lower(),
            "claude-opus-4-5" in effective_model_name.lower(),
        ])

        logger.info(f"Model: {effective_model_name}, skip_agent_traits: {skip_agent_traits}, has_agent_traits: {agent_traits is not None}")

        # Some models fail with agent traits, so skip them
        if agent_traits and not skip_agent_traits:
            logger.info("Using agent traits with compatible model")
            agent = self._create_agent(agent_traits)
            results = question.by(agent).by(model).run(
                use_api_proxy=True,
                offload_execution=False,
                progress_bar=False
            )
        else:
            # Either no agent traits or this model doesn't support them
            if skip_agent_traits and agent_traits:
                logger.info(f"Skipping agent traits for incompatible model: {effective_model_name}")
            elif not agent_traits:
                logger.info("No agent traits provided")

            results = question.by(model).run(
                use_api_proxy=True,
                offload_execution=False,
                progress_bar=False
            )

        end_time = time.time()

        # Extract the answer
        answer_key = f"answer.{question_name}"
        response_text = results.select(answer_key).first()

        # Handle None response - this can happen with some models
        if response_text is None:
            logger.warning(f"Model returned None response for {question_name}. Attempting alternative extraction.")

            # Try alternative methods to extract the response
            try:
                # Try getting the raw result
                raw_result = results.to_dict()
                logger.debug(f"Raw results keys: {list(raw_result.keys()) if isinstance(raw_result, dict) else 'not a dict'}")

                # Try different answer key formats
                alternative_keys = [
                    question_name,
                    f"{question_name}.answer",
                    "answer",
                ]

                for alt_key in alternative_keys:
                    try:
                        alt_response = results.select(alt_key).first()
                        if alt_response is not None:
                            logger.info(f"Found response using alternative key: {alt_key}")
                            response_text = alt_response
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Alternative extraction failed: {e}")

            # If still None, raise an error with more context
            if response_text is None:
                raise ValueError(
                    f"Model {model_name or self.default_config.name} returned None/empty response. "
                    f"Question: {question_name}. This may indicate an API issue or model incompatibility."
                )

        # Build metadata
        metadata = {
            "latency_ms": int((end_time - start_time) * 1000),
            "model": model_name or self.default_config.name,
            "temperature": temperature if temperature is not None else self.default_config.temperature,
        }

        return response_text, metadata

    @retry_with_backoff(max_retries=3)
    def generate_story(
        self,
        prompt_text: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        storyteller_id: str = "unknown"
    ) -> Dict:
        """Generate a story from a storyteller prompt.

        Args:
            prompt_text: The storyteller prompt
            model_name: Model to use
            temperature: Temperature setting
            storyteller_id: ID of the storyteller (for logging)

        Returns:
            Dict with keys: content, raw_response, word_count, latency_ms, source_cited

        Raises:
            StoryGenerationError: If story generation fails
        """
        logger.info(f"Generating story for storyteller {storyteller_id}")

        try:
            response_text, metadata = self._run_question(
                prompt_text=prompt_text,
                question_name=f"story_{storyteller_id}",
                model_name=model_name,
                temperature=temperature,
                agent_traits=None if self._should_skip_agent_traits(model_name) else {"role": "storyteller", "storyteller_id": storyteller_id}
            )

            # Extract source if mentioned (simple heuristic)
            source_cited = self._extract_source(response_text)

            return {
                "content": response_text,
                "raw_response": response_text,
                "word_count": len(response_text.split()),
                "source_cited": source_cited,
                **metadata
            }

        except Exception as e:
            logger.error(f"Story generation failed for {storyteller_id}: {e}")
            raise StoryGenerationError(f"Failed to generate story: {e}") from e

    def _extract_source(self, text: str) -> Optional[str]:
        """Extract source citation from text (simple heuristic).

        Args:
            text: The story text

        Returns:
            Extracted source or None
        """
        # Look for common source patterns
        patterns = [
            r"(?:according to|source:|cited in|published in|from)\s+([^.]+)",
            r"(?:I (?:read|learned|heard) (?:this |about this )?(?:in|from))\s+([^.]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    @retry_with_backoff(max_retries=3)
    def generate_question(
        self,
        prompt_text: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        target_storyteller_id: str = "unknown",
        question_number: int = 1
    ) -> Dict:
        """Generate a question from the judge.

        Args:
            prompt_text: The judge question prompt
            model_name: Model to use
            temperature: Temperature setting
            target_storyteller_id: ID of storyteller being questioned
            question_number: Which question this is

        Returns:
            Dict with keys: content, raw_response, latency_ms

        Raises:
            QuestionGenerationError: If question generation fails
        """
        logger.info(
            f"Generating question {question_number} for storyteller {target_storyteller_id}"
        )

        try:
            response_text, metadata = self._run_question(
                prompt_text=prompt_text,
                question_name=f"question_{target_storyteller_id}_{question_number}",
                model_name=model_name,
                temperature=temperature,
                agent_traits=None if self._should_skip_agent_traits(model_name) else {"role": "judge"}
            )

            # Clean up the response (remove any preamble)
            question_text = self._clean_question(response_text)

            return {
                "content": question_text,
                "raw_response": response_text,
                **metadata
            }

        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            raise QuestionGenerationError(f"Failed to generate question: {e}") from e

    def _clean_question(self, text: str) -> str:
        """Clean up question text, removing any preamble.

        Args:
            text: Raw question text

        Returns:
            Cleaned question text
        """
        # Handle None or empty text
        if text is None:
            raise ValueError("Cannot clean None text - model returned empty response")

        if not isinstance(text, str):
            text = str(text)

        # Remove common preambles
        text = text.strip()

        # If it starts with quotes, extract the quoted part
        if text.startswith('"') and '"' in text[1:]:
            end_quote = text.index('"', 1)
            return text[1:end_quote]

        # Remove phrases like "My question is:" or "I would ask:"
        preambles = [
            r"^(?:my question (?:is|would be)[:\s]+)",
            r"^(?:i (?:would |want to )?ask[:\s]+)",
            r"^(?:question[:\s]+)",
        ]
        for pattern in preambles:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text.strip()

    @retry_with_backoff(max_retries=3)
    def generate_answer(
        self,
        prompt_text: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        storyteller_id: str = "unknown",
        question_number: int = 1
    ) -> Dict:
        """Generate an answer from a storyteller.

        Args:
            prompt_text: The answer prompt
            model_name: Model to use
            temperature: Temperature setting
            storyteller_id: ID of the storyteller
            question_number: Which question this answers

        Returns:
            Dict with keys: content, raw_response, word_count, latency_ms

        Raises:
            AnswerGenerationError: If answer generation fails
        """
        logger.info(
            f"Generating answer from storyteller {storyteller_id} "
            f"to question {question_number}"
        )

        try:
            response_text, metadata = self._run_question(
                prompt_text=prompt_text,
                question_name=f"answer_{storyteller_id}_{question_number}",
                model_name=model_name,
                temperature=temperature,
                agent_traits=None if self._should_skip_agent_traits(model_name) else {"role": "storyteller", "storyteller_id": storyteller_id}
            )

            return {
                "content": response_text,
                "raw_response": response_text,
                "word_count": len(response_text.split()),
                **metadata
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise AnswerGenerationError(f"Failed to generate answer: {e}") from e

    @retry_with_backoff(max_retries=3)
    def generate_verdict(
        self,
        prompt_text: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict:
        """Generate a verdict from the judge.

        Args:
            prompt_text: The verdict prompt
            model_name: Model to use
            temperature: Temperature setting

        Returns:
            Dict with keys: accused_id, confidence, reasoning, raw_response,
                           frame_break_attempted, latency_ms

        Raises:
            VerdictParsingError: If verdict parsing fails
        """
        logger.info("Generating verdict from judge")

        try:
            response_text, metadata = self._run_question(
                prompt_text=prompt_text,
                question_name="verdict",
                model_name=model_name,
                temperature=temperature,
                agent_traits=None if self._should_skip_agent_traits(model_name) else {"role": "judge"}
            )

            # Parse the verdict
            parsed = self._parse_verdict(response_text)

            return {
                **parsed,
                "raw_response": response_text,
                **metadata
            }

        except VerdictParsingError:
            raise
        except Exception as e:
            logger.error(f"Verdict generation failed: {e}")
            raise VerdictParsingError(f"Failed to generate verdict: {e}") from e

    def _parse_verdict(self, text: str) -> Dict:
        """Parse verdict from LLM response.

        Args:
            text: Raw verdict text

        Returns:
            Dict with accused_id, confidence, reasoning, frame_break_attempted

        Raises:
            VerdictParsingError: If parsing fails
        """
        text = text.strip()

        # Check for frame-breaking (judge refuses to accuse)
        frame_break_patterns = [
            r"cannot (?:determine|identify|accuse)",
            r"all (?:of the )?(?:stories )?(?:seem|appear)(?: to be)? (?:true|genuine)",
            r"none of them (?:seem|appear)",
            r"refuse to (?:accuse|identify)",
        ]
        frame_break_attempted = any(
            re.search(p, text, re.IGNORECASE) for p in frame_break_patterns
        )

        # Extract accused ID
        accused_match = re.search(
            r"(?:accused|liar|fibber|lying)[:\s]*(?:storyteller\s*)?([ABC])",
            text,
            re.IGNORECASE
        )
        if not accused_match:
            # Try alternative patterns
            accused_match = re.search(
                r"storyteller\s*([ABC])\s*(?:is|was|seems)",
                text,
                re.IGNORECASE
            )
        if not accused_match:
            # Last resort: find any standalone A, B, or C after "ACCUSED:"
            accused_match = re.search(r"ACCUSED[:\s]*(?:storyteller\s*)?([ABC])", text, re.IGNORECASE)

        if not accused_match:
            if frame_break_attempted:
                # If frame break, default to A
                accused_id = "A"
            else:
                raise VerdictParsingError(f"Could not parse accused ID from: {text[:200]}")
        else:
            accused_id = accused_match.group(1).upper()

        # Extract confidence
        confidence_match = re.search(
            r"(?:confidence)[:\s]*(\d+)",
            text,
            re.IGNORECASE
        )
        if confidence_match:
            confidence = int(confidence_match.group(1))
            confidence = max(1, min(10, confidence))  # Clamp to 1-10
        else:
            confidence = 5  # Default to middle confidence

        # Extract reasoning
        reasoning_match = re.search(
            r"(?:reasoning|because|reason)[:\s]*(.+?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
        else:
            # Use the whole text as reasoning
            reasoning = text[:500]

        return {
            "accused_id": accused_id,
            "confidence": confidence,
            "reasoning": reasoning,
            "frame_break_attempted": frame_break_attempted
        }

    @retry_with_backoff(max_retries=3)
    def generate_intermediate_guess(
        self,
        prompt_text: str,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        after_qa_number: int = 1
    ) -> Dict:
        """Generate an intermediate guess from the judge after some Q&A exchanges.

        This enables tracking one-shot, two-shot, n-shot performance.

        Args:
            prompt_text: The intermediate guess prompt
            model_name: Model to use
            temperature: Temperature setting
            after_qa_number: Number of Q&A exchanges completed

        Returns:
            Dict with keys: accused_id, confidence, reasoning, raw_response, latency_ms

        Raises:
            VerdictParsingError: If parsing fails
        """
        logger.info(f"Generating intermediate guess after {after_qa_number} Q&A exchanges")

        try:
            response_text, metadata = self._run_question(
                prompt_text=prompt_text,
                question_name=f"intermediate_guess_{after_qa_number}",
                model_name=model_name,
                temperature=temperature,
                agent_traits=None if self._should_skip_agent_traits(model_name) else {"role": "judge"}
            )

            # Parse the guess (similar to verdict but simpler)
            parsed = self._parse_intermediate_guess(response_text)

            return {
                **parsed,
                "raw_response": response_text,
                **metadata
            }

        except VerdictParsingError:
            raise
        except Exception as e:
            logger.error(f"Intermediate guess generation failed: {e}")
            raise VerdictParsingError(f"Failed to generate intermediate guess: {e}") from e

    def _parse_intermediate_guess(self, text: str) -> Dict:
        """Parse intermediate guess from LLM response.

        Args:
            text: Raw guess text

        Returns:
            Dict with accused_id, confidence, reasoning

        Raises:
            VerdictParsingError: If parsing fails
        """
        text = text.strip()

        # Extract accused ID (using similar patterns to verdict)
        accused_match = re.search(
            r"(?:current_guess|guess|accused|suspect)[:\s]*([ABC])",
            text,
            re.IGNORECASE
        )
        if not accused_match:
            # Try alternative patterns
            accused_match = re.search(
                r"storyteller\s*([ABC])",
                text,
                re.IGNORECASE
            )

        if not accused_match:
            raise VerdictParsingError(f"Could not parse accused ID from intermediate guess: {text[:200]}")

        accused_id = accused_match.group(1).upper()

        # Extract confidence
        confidence_match = re.search(
            r"(?:confidence)[:\s]*(\d+)",
            text,
            re.IGNORECASE
        )
        if confidence_match:
            confidence = int(confidence_match.group(1))
            confidence = max(1, min(10, confidence))  # Clamp to 1-10
        else:
            confidence = 5  # Default to middle confidence

        # Reasoning is optional for intermediate guesses (keep it short)
        reasoning_match = re.search(
            r"(?:reasoning|because)[:\s]*(.+?)(?:\n\n|\Z)",
            text,
            re.IGNORECASE | re.DOTALL
        )
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""

        return {
            "accused_id": accused_id,
            "confidence": confidence,
            "reasoning": reasoning
        }


# ---------------------------------------------------------------------------
# The Perfect Lie: private-block channel (PERFECT_LIE.md §2, invariant 1)
# ---------------------------------------------------------------------------
#
# The existing story path (generate_story -> _run_question) cannot carry a
# private block safely: it silently drops agent traits for several model
# families (_should_skip_agent_traits) and, on the direct-Anthropic path,
# prepends traits to the USER prompt. Either would let B_hat_j vanish or leak
# into E_t without any error. This method is the one channel the study uses.
# It is additive; nothing above changes.

PERFECT_LIE_AGENT_TRAITS = {"role": "storyteller"}  # constant; EDSL ignores `instruction` on a trait-less agent

# Constant traits per study role. Each is identical in every condition, so the rendered
# system prompt differs across conditions only by the private note (tested).
PERFECT_LIE_ROLE_TRAITS = {
    "liar": PERFECT_LIE_AGENT_TRAITS,
    "target": {"role": "listener"},
    "grader": {"role": "annotator"},
    "trace_probe": {"role": "annotator"},
}

# Every live call runs locally against the service key. All four flags are needed:
# with use_api_proxy=False and disable_remote_inference left at its default (False),
# EDSL sets offload_execution=True and, whenever EXPECTED_PARROT_API_KEY is set, ships
# the whole job to Expected Parrot's servers. Their code has neither the `reasoning`
# passthrough nor the OpenRouter key, so every reasoning level would silently run at
# the provider default. disable_remote_cache keeps responses out of the shared cache.
PERFECT_LIE_RUN_FLAGS = dict(
    use_api_proxy=False,
    disable_remote_inference=True,
    offload_execution=False,
    disable_remote_cache=True,
    progress_bar=False,
    stop_on_exception=False,
)


class PrivateBlockChannelError(RuntimeError):
    """Raised when the rendered prompts do not carry the private block as intended."""


class PerfectLieCallError(RuntimeError):
    """A live call returned no usable answer."""


def fold_system_into_user(system_prompt: str, user_prompt: str) -> str:
    """How Gemma 3's chat template delivers a system message: prepended to the first user
    turn, separated by a blank line. Doing it ourselves makes the delivered text exact and
    recorded, instead of depending on each provider's handling of a system role."""
    return f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt


def _perfect_lie_build_job(user_prompt: str, system_prompt: str, model_name: str,
                           temperature: float, replicate: int, service_name: str,
                           question_name: str = "story", skip_api_key_check: bool = False,
                           reasoning: Optional[Dict] = None, max_output_tokens: Optional[int] = None,
                           role: str = "liar", run_namespace: str = "", attempt: int = 0,
                           provider: Optional[Dict] = None, system_role: bool = True,
                           draw_key: str = "", response_format: Optional[Dict] = None,
                           top_p: Optional[float] = None):
    """Build (but do not run) the EDSL job for one call and verify its rendered prompts.

    reasoning: OpenRouter's unified `reasoning` request field for this cell's budget level
    (e.g. {"enabled": False}, {"max_tokens": 2048}, {"effort": "low"}). It is stored in
    model.parameters so it enters the cache key, and the open_router service forwards it to
    the request (see edsl/inference_services/services/open_ai_service.py,
    _filter_parameters_for_service). max_output_tokens is sent as max_completion_tokens and
    must exceed thinking + story.

    replicate, run_namespace and attempt are cache-key fields only; none is sent to the API.
    replicate separates independent draws. run_namespace ("smoke", "pilot", "full") keeps a
    pilot response from being served back from cache inside the full run, where pilot data
    would otherwise leak into inference. attempt lets a retry after a malformed answer
    reach the model again instead of the cached malformed answer.
    """
    model_kwargs = dict(temperature=temperature)
    if top_p is not None:
        model_kwargs["top_p"] = float(top_p)
    if max_output_tokens is not None:
        model_kwargs["max_tokens"] = int(max_output_tokens)
    if skip_api_key_check:
        model_kwargs["skip_api_key_check"] = True
    if service_name:
        model = Model(model_name, service_name=service_name, **model_kwargs)
    else:
        model = Model(model_name, **model_kwargs)
    model.parameters["replicate"] = replicate
    # draw_key separates draws whose prompts are identical by design: in `none` and
    # `placebo` the liar sees the same input for both targets of a pair, and without this
    # the second lie is the first one served from cache (found in the C1 pilot: all 48
    # such units held one lie twice, forcing T = 0). Cache-key only; never sent.
    if draw_key:
        model.parameters["draw"] = draw_key
    if run_namespace:
        model.parameters["run_namespace"] = run_namespace
    if attempt:
        model.parameters["attempt"] = attempt
    if reasoning is not None:
        model.parameters["reasoning"] = dict(reasoning)
    if provider:
        model.parameters["provider"] = dict(provider)
    if response_format:
        model.parameters["response_format"] = dict(response_format)

    if system_role:
        traits = dict(PERFECT_LIE_ROLE_TRAITS[role])
        agent = Agent(traits=traits, instruction=system_prompt)
        question = QuestionFreeText(question_text=user_prompt, question_name=question_name)
        job = question.by(agent).by(model)
        expected_user = user_prompt
    else:
        # No system role (Gemma): one user turn, private block first, exactly as the model's
        # chat template would place a system message. No agent, so EDSL sends no system message.
        expected_user = fold_system_into_user(system_prompt, user_prompt)
        question = QuestionFreeText(question_text=expected_user, question_name=question_name)
        job = question.by(model)

    rendered = job.prompts().to_dicts()[0]
    rendered_user = str(rendered["user_prompt"])
    rendered_system = str(rendered["system_prompt"])
    if rendered_user != expected_user:
        raise PrivateBlockChannelError("rendered user prompt differs from what this model must receive")
    if system_role and not rendered_system.startswith(system_prompt):
        raise PrivateBlockChannelError("rendered system prompt does not begin with the private block")
    if not system_role and rendered_system != "":
        raise PrivateBlockChannelError("a model without a system role must receive no system message")
    return job, rendered_user, rendered_system


def delivered_messages(rendered_user: str, rendered_system: str) -> List[Dict[str, str]]:
    """The chat messages EDSL sends (it drops an empty system message). Stored with every
    call so the pod can replay the exact sequence through the same weights."""
    msgs = [{"role": "system", "content": rendered_system}] if rendered_system else []
    return msgs + [{"role": "user", "content": rendered_user}]


def _perfect_lie_parse_results(results, question_name: str) -> Dict:
    """Pull answer, raw response, usage, finish reason and any thinking trace out of Results."""
    text = results.select(f"answer.{question_name}").first()
    try:
        raw = results.select(f"raw_model_response.{question_name}_raw_model_response").first()
    except Exception:
        raw = None
    usage, finish_reason = {}, None
    if isinstance(raw, dict):
        u = raw.get("usage") or {}
        details = u.get("completion_tokens_details") or {}
        usage = {
            "prompt_tokens": u.get("prompt_tokens"),
            "completion_tokens": u.get("completion_tokens"),
            "reasoning_tokens": details.get("reasoning_tokens"),
        }
        choices = raw.get("choices") or []
        if choices and isinstance(choices[0], dict):
            finish_reason = choices[0].get("finish_reason")
    trace, trace_kind = _perfect_lie_extract_trace_from_raw(raw)
    generation_id = raw.get("id") if isinstance(raw, dict) else None
    served_provider = raw.get("provider") if isinstance(raw, dict) else None
    return {"text": text, "raw": raw, "usage": usage, "finish_reason": finish_reason,
            "thinking_trace": trace, "thinking_trace_kind": trace_kind,
            # OpenRouter's id for this call; GET /api/v1/generation?id=... returns its billed cost.
            "generation_id": generation_id,
            # Which upstream provider OpenRouter used; checked against the pin.
            "served_provider": served_provider}


def _perfect_lie_extract_trace_from_raw(raw) -> Tuple[Optional[str], Optional[str]]:
    """Return (trace_text, kind) from an OpenAI-shaped raw response.

    kind is "text" for a readable trace, "summary" for a provider summary (typical for
    OpenAI reasoning models), "encrypted" when only an opaque blob came back, None when
    nothing came back. Only "text" and "summary" yield trace text for the trace probe.
    """
    try:
        message = raw["choices"][0]["message"]
    except Exception:
        return None, None
    if not isinstance(message, dict):
        return None, None
    for key in ("reasoning", "reasoning_content"):
        if message.get(key):
            return str(message[key]), "text"
    details = [d for d in (message.get("reasoning_details") or []) if isinstance(d, dict)]
    texts = [d["text"] for d in details if d.get("text")]
    if texts:
        return "\n".join(texts), "text"
    summaries = [d["summary"] for d in details if d.get("summary")]
    if summaries:
        return "\n".join(str(x) for x in summaries), "summary"
    if any(d.get("data") or "encrypted" in str(d.get("type", "")) for d in details):
        return None, "encrypted"
    return None, None


def _perfect_lie_extract_trace(results) -> Optional[str]:
    """Backward-compatible helper: trace text from a Results object, or None."""
    try:
        raw = results.select("raw_model_response.story_raw_model_response").first()
    except Exception:
        return None
    return _perfect_lie_extract_trace_from_raw(raw)[0]


class PerfectLieAdapter:
    """One call = (system_prompt private, user_prompt public), always executed locally."""

    def __init__(self, service_name: Optional[str] = "open_router"):
        self.service_name = service_name

    def render(self, user_prompt: str, system_prompt: str, model_name: str,
               temperature: float, replicate: int, skip_api_key_check: bool = True,
               reasoning: Optional[Dict] = None, max_output_tokens: Optional[int] = None,
               role: str = "liar", provider: Optional[Dict] = None, system_role: bool = True) -> Dict:
        """Return the exact prompts and request parameters EDSL would send, without calling any model."""
        job, u, s = _perfect_lie_build_job(user_prompt, system_prompt, model_name, temperature, replicate,
                                           self.service_name, skip_api_key_check=skip_api_key_check,
                                           reasoning=reasoning, max_output_tokens=max_output_tokens, role=role,
                                           provider=provider, system_role=system_role)
        model = job.models[0]
        params = {"model": model_name, "messages": [], "max_completion_tokens": getattr(model, "max_tokens", None),
                  "logprobs": False, "top_logprobs": 3}
        if hasattr(model, "_filter_parameters_for_service"):
            params = model._filter_parameters_for_service(params)
        return {"user_prompt": u, "system_prompt": s, "request_params": params,
                "delivered_messages": delivered_messages(u, s)}

    async def acall(self, *, role: str, user_prompt: str, system_prompt: str, model_name: str,
                    temperature: float, replicate: int, run_namespace: str,
                    reasoning: Optional[Dict] = None, max_output_tokens: Optional[int] = None,
                    attempt: int = 0, cache=None, provider: Optional[Dict] = None,
                    system_role: bool = True, draw_key: str = "",
                    response_format: Optional[Dict] = None, top_p: Optional[float] = None) -> Dict:
        """Run one live call locally. Never invoked by --dry-run or by the offline tests' render paths."""
        qname = {"liar": "story", "target": "verdict", "grader": "annotation", "trace_probe": "probe"}[role]
        job, u, s = _perfect_lie_build_job(user_prompt, system_prompt, model_name, temperature, replicate,
                                           self.service_name, question_name=qname, reasoning=reasoning,
                                           max_output_tokens=max_output_tokens, role=role,
                                           run_namespace=run_namespace, attempt=attempt,
                                           skip_api_key_check=self.service_name is None,
                                           provider=provider, system_role=system_role,
                                           draw_key=draw_key, response_format=response_format,
                                           top_p=top_p)
        start = time.time()
        kwargs = dict(PERFECT_LIE_RUN_FLAGS)
        if cache is not None:
            kwargs["cache"] = cache
        results = await job.run_async(**kwargs)
        out = _perfect_lie_parse_results(results, qname)
        if out["text"] is None:
            raise PerfectLieCallError(f"{role} call to {model_name} returned no answer: {_perfect_lie_exception_text(results)}")
        out.update({
            "latency_ms": int((time.time() - start) * 1000),
            "model": model_name, "temperature": temperature, "replicate": replicate,
            "reasoning": reasoning, "max_output_tokens": max_output_tokens,
            "attempt": attempt, "run_namespace": run_namespace,
            "system_prompt": s, "user_prompt": u, "delivered_messages": delivered_messages(u, s),
            "provider_pin": provider, "system_role": system_role, "top_p": top_p,
        })
        return out

    def generate(self, user_prompt: str, system_prompt: str, model_name: str,
                 temperature: float, replicate: int,
                 reasoning: Optional[Dict] = None, max_output_tokens: Optional[int] = None,
                 run_namespace: str = "adhoc", cache=None) -> Tuple[str, Dict]:
        """Synchronous single liar call (kept for ad-hoc use). Same local-only flags."""
        import asyncio
        out = asyncio.run(self.acall(role="liar", user_prompt=user_prompt, system_prompt=system_prompt,
                                     model_name=model_name, temperature=temperature, replicate=replicate,
                                     run_namespace=run_namespace, reasoning=reasoning,
                                     max_output_tokens=max_output_tokens, cache=cache))
        if out["text"] is None:
            raise StoryGenerationError(f"{model_name} returned no answer")
        return out["text"], {k: v for k, v in out.items() if k not in ("text", "raw")}


def _perfect_lie_exception_text(results) -> str:
    """Best-effort: the underlying exception EDSL caught, so a failed call records its cause."""
    try:
        th = results.task_history
        for interview in getattr(th, "total_interviews", []) or []:
            for qname, excs in (getattr(interview, "exceptions", {}) or {}).items():
                for e in excs:
                    exc = getattr(e, "exception", None)
                    if exc is not None:
                        return f"{type(exc).__name__}: {exc}"[:800]
                    return str(e)[:800]
    except Exception:
        pass
    return "no exception detail available"
