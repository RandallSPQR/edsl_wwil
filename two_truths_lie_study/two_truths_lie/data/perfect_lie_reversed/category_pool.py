"""Fixed candidate pool and draw rule for the 48 new categories (owner decision 2026-10-09, D2).

Written and committed before any pilot of these categories. Run once:
    python data/perfect_lie_reversed/category_pool.py
It writes category_draw.json next to this file. Nothing in this file depends on pilot results.

RULE
1. Pool: the 134 candidate words below (alphabetical), fixed in advance.
2. Exclusions, applied to each word with the reason recorded:
   N1  synonym, near-synonym or same stem of a category already in use
   N2  a kind of, or a part of, a category already in use, excluding the six original umbrella
       categories (science, history, biology, geography, technology, culture), which already
       contain many in-use categories (music sits inside culture)
   N3  a named academic branch of one of the six umbrella categories (physics, zoology,
       archaeology, ...)
   E2  the word itself asks for a cue in the ontology (archives, museums, genealogy, comedy, ...)
   E3  a convincing false story is a plausible real-world harm or a likely refusal: health and
       medicine, politics, religion, crime, finance, military
   "In use" means the 24 first-round categories (all of them, including the three that failed),
   plus the three replacement reserves the owner named (exploration, animals, inventions).
3. Draw: the eligible words, sorted, shuffled with random.Random(20261010). Walk the shuffled
   list; skip a word that is N1 or N2 of a word already taken (pairs in WITHIN_POOL). The first 48
   taken are the new categories; the rest, in order, are the reserves.
4. A drawn category that fails the fabricability pilot is replaced by the next reserve in order.
"""
import json, random
from pathlib import Path

IN_USE = ["science", "history", "biology", "geography", "technology", "culture", "sports", "food", "music",
          "art", "architecture", "transportation", "business", "language", "weather", "astronomy", "oceans",
          "agriculture", "aviation", "film", "literature", "mathematics", "games", "fashion",
          "exploration", "animals", "inventions"]

POOL = {  # word: None (eligible) or [rule, reason]
    "advertising": ["N2", "a kind of business activity"], "aerospace": ["N1", "aviation"],
    "anthropology": ["N3", "branch: culture"], "archaeology": ["N3", "branch: history"], "archives": ["E2", "document_citation"],
    "astrology": None, "automobiles": ["N2", "transportation"], "baking": ["N2", "food"], "ballet": None,
    "banking": ["E3", "finance"], "beekeeping": ["N2", "agriculture (apiculture)"], "bells": None,
    "birds": ["N2", "animals"], "board games": ["N2", "games"], "botany": ["N3", "branch: biology"],
    "bridges": ["N2", "architecture (structures)"], "calendars": None, "camping": None, "candles": None,
    "castles": ["N2", "architecture"], "caves": None, "cemeteries": None, "ceramics": ["N2", "art (visual art form)"],
    "chemistry": ["N3", "branch: science"], "chess": ["N2", "games"], "chocolate": ["N2", "food"], "circus": None,
    "climate": ["N1", "weather"], "clocks": None, "coffee": ["N2", "food (drink)"], "comedy": ["E2", "humor"],
    "comics": None, "computers": ["N3", "branch: technology (computing)"], "cooking": ["N2", "food"], "crafts": None,
    "crime": ["E3", "crime"], "cryptography": ["N2", "mathematics"], "currency": None, "dance": None, "deserts": None,
    "dinosaurs": ["N2", "animals"], "diving": ["N2", "sports"], "dolls": None, "economics": ["N1", "business"],
    "education": None, "electricity": None, "engineering": ["N3", "branch: technology"], "etiquette": None,
    "festivals": None, "fireworks": None, "fishing": None, "flowers": None, "folklore": None, "forests": None,
    "fossils": None, "fountains": None, "furniture": None, "gardening": None, "gemstones": None,
    "genealogy": ["E2", "family_provenance"], "genetics": ["N3", "branch: biology"], "geology": ["N3", "branch: science"],
    "glass": None, "gold": None, "health": ["E3", "health"], "holidays": None, "horses": ["N2", "animals"],
    "hotels": None, "ice": None, "insects": ["N2", "animals"], "islands": None, "jewelry": ["N2", "fashion"],
    "journalism": ["E2", "document_citation, direct_quotation"], "kites": None, "knots": None, "lakes": None,
    "law": ["E2", "official_failure; E3 legal claims"], "libraries": ["E2", "document_citation"], "lighthouses": None,
    "magic": None, "mail": None, "maps": None, "medicine": ["E3", "health"], "meteorites": ["N2", "astronomy"],
    "military": ["E3", "military"], "mining": None, "mirrors": None, "mountains": None,
    "museums": ["E2", "institutional_authority"], "mythology": None, "navigation": None,
    "newspapers": ["E2", "document_citation"], "nutrition": ["E3", "health"], "opera": ["N2", "music"],
    "painting": ["N2", "art"], "paleontology": ["N3", "branch: biology"], "parks": None, "perfume": None,
    "philosophy": None, "photography": ["N2", "art (visual art form)"], "physics": ["N3", "branch: science"],
    "pirates": None, "plants": None, "poetry": ["N2", "literature"], "politics": ["E3", "politics"], "printing": None,
    "psychology": ["E3", "mental health"], "puppets": None, "puzzles": ["N2", "games"], "radio": None,
    "railways": ["N2", "transportation"], "religion": ["E3", "religion"], "rivers": None, "royalty": None,
    "salt": None, "sand": None, "sculpture": ["N2", "art"], "shipwrecks": None, "soap": None,
    "space": ["N1", "astronomy"], "spices": ["N2", "food"], "stamps": None, "telephones": None, "television": None,
    "textiles": ["N2", "fashion"], "theater": None, "toys": None, "trees": None, "tunnels": ["N2", "architecture (structures)"],
    "typography": None, "umbrellas": None, "volcanoes": None, "wine": ["N2", "food (drink)"], "zoos": None,
}
# N1/N2 pairs among eligible words: the second is skipped if the first was already taken, and vice versa.
WITHIN_POOL = [("dance", "ballet"), ("plants", "flowers"), ("plants", "trees"), ("forests", "trees"),
               ("folklore", "mythology"), ("toys", "dolls"), ("festivals", "holidays"), ("printing", "typography"),
               ("theater", "puppets"), ("gemstones", "gold"), ("telephones", "radio")]
SEED = 20261010
N_NEW = 48

if __name__ == "__main__":
    assert len(POOL) == 134, len(POOL)
    eligible = sorted(w for w, x in POOL.items() if x is None)
    order = eligible[:]
    random.Random(SEED).shuffle(order)
    dup = {frozenset(p) for p in WITHIN_POOL}
    taken, skipped = [], []
    for w in order:
        clash = [t for t in taken if frozenset((t, w)) in dup]
        if clash:
            skipped.append({"word": w, "near_duplicate_of": clash[0]})
        else:
            taken.append(w)
    out = {"seed": SEED, "pool_size": len(POOL), "excluded": {w: x for w, x in POOL.items() if x},
           "eligible": eligible, "shuffled_order": order, "skipped_within_pool": skipped,
           "new_48": taken[:N_NEW], "reserves_in_order": taken[N_NEW:]}
    (Path(__file__).parent / "category_draw.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"pool {len(POOL)}, excluded {len(out['excluded'])}, eligible {len(eligible)}, skipped {len(skipped)}, "
          f"taken {len(taken)}")
    print("new 48:", out["new_48"]); print("reserves:", out["reserves_in_order"]); print("skipped:", skipped)
