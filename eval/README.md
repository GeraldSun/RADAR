# RADAR Evaluation

This folder contains the official evaluation script and supporting files for the RADAR benchmark.

The evaluator computes **four metrics** on the **mixed dev set**, which contains both naturally occurring edits and augmented edits. The `composite_score` is the primary ranking metric on the shared task leaderboard. In addition to scoring on the mixed set, submissions in the shared task will also be evaluated on a **hidden natural subset** (naturally occurring edits only) using the same four metrics.

## Contents

| File | Description |
|---|---|
| `eval.py` | Official evaluation script |
| `eval.sh` | Shell wrapper for quick local runs |
| `groundtruth_dev.csv` | Ground-truth labels for the dev set |
| `example_submission.csv` | Example submission file showing the required format |
| `example_eval_results.json` | Example output produced by `eval.py` |

---

## Submission Format

A valid submission is a CSV file with one row per edit and four columns:

```
edit_id, agreement_pred, severity_pred, edit_type_pred
```

Valid label values:

| Column | Allowed values |
|---|---|
| `agreement_pred` | `agree`, `partially agree`, `disagree` |
| `severity_pred` | `negligible`, `moderate`, `critical` |
| `edit_type_pred` | `addition`, `correction`, `clarification` |

See `example_submission.csv` for a concrete example.

---

## Running the Evaluator

```bash
python eval/eval.py \
  --submission  your_submission.csv \
  --groundtruth eval/groundtruth_dev.csv \
  --output      results.json
```

Or from inside the `eval/` directory using the shell wrapper:

```bash
bash eval.sh
```

### Arguments

| Argument | Default | Description |
|---|---|---|
| `--submission` | `example_submission.csv` | Path to the submission CSV |
| `--groundtruth` | `groundtruth_dev.csv` | Path to the ground-truth CSV |
| `--output` | `example_eval_results.json` | Path for the output JSON file |

---

## Output Format

`eval.py` prints results to stdout and writes a JSON file:

```json
{
  "agreement_accuracy": 0.0,
  "severity_accuracy": 0.0,
  "edit_type_accuracy": 0.0,
  "composite_score": 0.0
}
```

### Metric Definitions

- **agreement_accuracy** — Exact-match accuracy on the `agreement` label (`agree`, `partially agree`, and `disagree` are treated as distinct classes).
- **severity_accuracy** — Exact-match accuracy on the `severity` label.
- **edit_type_accuracy** — Exact-match accuracy on the `edit_type` label.
- **composite_score** — Fraction of rows where the agreement fuzzy-matches *and* both severity and edit type exactly match. This is the primary metric for the shared task leaderboard.

---

## Dependencies

```
pandas
scikit-learn
numpy
```
