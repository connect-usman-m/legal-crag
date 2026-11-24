# Calibration

Dev set only. The frozen test set was not used for tuning.

Prompt version: V3
Thresholds: LOWER=0.5, KEEP=0.7, UPPER=0.9

## Score histogram

### relevant

- 0.0-0.2:  (0)
- 0.2-0.4:  (0)
- 0.4-0.6:  (0)
- 0.6-0.8:  (0)
- 0.8-1.0: ####### (7)

### partial

- 0.0-0.2:  (0)
- 0.2-0.4: # (1)
- 0.4-0.6: ####### (7)
- 0.6-0.8: ########### (11)
- 0.8-1.0: ##### (5)

### irrelevant

- 0.0-0.2: ################### (19)
- 0.2-0.4: ####### (7)
- 0.4-0.6: ## (2)
- 0.6-0.8:  (0)
- 0.8-1.0: # (1)

## Outcome

- Branch accuracy: 9/10
- Irrelevant chunks below LOWER: 28/29
- V1 reached 6/10; V2 failed with Groq tool-use errors; V3 with strict JSON schema was selected.
- UPPER 0.9 keeps partial cross-instrument chunks out of CORRECT; LOWER 0.5 captures the remaining high-scoring irrelevant chunks.
