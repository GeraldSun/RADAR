import json
import argparse
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score


def normalize_labels(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    s = s.replace({
        "partial": "partially agree",
        "partially_agree": "partially agree",
        "partially-agree": "partially agree",
    })
    return s


def accuracy(y_true: pd.Series, y_pred: pd.Series) -> float:
    mask = y_true.notna() & y_pred.notna()
    if not mask.any():
        return float("nan")
    return float(accuracy_score(y_true[mask], y_pred[mask]))


def agreement_fuzzy_match(y_true: pd.Series, y_pred: pd.Series) -> pd.Series:
    fuzzy_set = {"agree", "partially agree"}

    exact = y_true == y_pred
    fuzzy = y_true.isin(fuzzy_set) & y_pred.isin(fuzzy_set)

    return exact | fuzzy


def composite_score(df: pd.DataFrame) -> float:
    """
    Per-row score: 1 if agreement fuzzy matches AND both severity and edit_type match, else 0.
    Returns mean over rows where all required labels are present.
    """
    req = (
        df["agreement"].notna()
        & df["agreement_pred"].notna()
        & df["severity"].notna()
        & df["severity_pred"].notna()
        & df["edit_type"].notna()
        & df["edit_type_pred"].notna()
    )
    dfc = df.loc[req].copy()
    if len(dfc) == 0:
        return float("nan")

    agree_match = agreement_fuzzy_match(dfc["agreement"], dfc["agreement_pred"])
    sev_match = dfc["severity"] == dfc["severity_pred"]
    typ_match = dfc["edit_type"] == dfc["edit_type_pred"]

    comp = (agree_match & sev_match & typ_match).astype(int)
    return float(comp.mean())


def main():
    parser = argparse.ArgumentParser(description="RADAR evaluation script")
    parser.add_argument(
        "--submission",
        default="example_submission.csv",
        help="Path to the submission CSV (edit_id, agreement_pred, severity_pred, edit_type_pred)",
    )
    parser.add_argument(
        "--groundtruth",
        default="groundtruth_dev.csv",
        help="Path to the ground-truth CSV (edit_id, agreement, severity, edit_type)",
    )
    parser.add_argument(
        "--output",
        default="example_eval_results.json",
        help="Path for the output JSON file",
    )
    args = parser.parse_args()

    submission = pd.read_csv(args.submission)
    groundtruth = pd.read_csv(args.groundtruth)

    df = groundtruth.merge(submission, on="edit_id", how="inner")

    for col in ["agreement", "agreement_pred"]:
        df[col] = normalize_labels(df[col])
    for col in ["severity", "severity_pred", "edit_type", "edit_type_pred"]:
        df[col] = df[col].astype(str).str.strip().str.lower()

    results = {
        "agreement_accuracy": accuracy(df["agreement"], df["agreement_pred"]),
        "severity_accuracy": accuracy(df["severity"], df["severity_pred"]),
        "edit_type_accuracy": accuracy(df["edit_type"], df["edit_type_pred"]),
        "composite_score": composite_score(df),
    }

    print(json.dumps(results, indent=2))

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()