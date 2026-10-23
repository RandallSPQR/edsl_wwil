# Steering scale at the selected layer: meta-llama/llama-3.1-8b-instruct, layer 12

||v|| (alpha = 1 step, section 6) = 0.280. Frozen training items, last prompt token.

| persona | pairs | residual norm median [10%, 90%] | gap on unit v mean (median) [10%, 90%] | own shift norm | cos(own shift, v) | level full / reversed | ||v|| / median norm |
|---|---|---|---|---|---|---|---|
| P1 | 40 | 7.519 [7.458, 7.563] | 0.311 (0.310) [0.299, 0.324] | 0.377 | 0.824 | -0.177 / -0.487 | 0.0373 |
| P2 | 40 | 7.549 [7.489, 7.596] | 0.271 (0.272) [0.262, 0.282] | 0.325 | 0.835 | -0.166 / -0.437 | 0.0371 |
| P3 | 40 | 7.505 [7.448, 7.556] | 0.290 (0.292) [0.280, 0.298] | 0.352 | 0.822 | -0.131 / -0.420 | 0.0374 |
| P5 | 40 | 7.517 [7.458, 7.562] | 0.241 (0.242) [0.227, 0.251] | 0.282 | 0.855 | -0.148 / -0.389 | 0.0373 |
| P6 | 40 | 7.515 [7.454, 7.563] | 0.290 (0.291) [0.277, 0.300] | 0.337 | 0.859 | -0.142 / -0.432 | 0.0373 |
| all | 200 | 7.522 [7.458, 7.572] | 0.280 (0.286) [0.242, 0.309] | 0.280 | 1.000 | -0.153 / -0.433 | 0.0373 |

Max / min across the five personas: median residual norm 1.01x, mean gap 1.29x, own shift norm 1.34x.
