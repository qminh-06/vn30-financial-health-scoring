"""Historical Validation + Accuracy/Precision/Recall/F1/MAE — B4.

Also hosts the 3-model benchmark (ratios-only vs ratios+scoring vs
ratios+scoring+AI) that makes the "AI actually adds value" case in the report.
"""

from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import numpy as np


def derive_ground_truth(ratios_year_n: dict, ratios_year_n_plus_1: dict) -> dict:
    """Turns two years of ratios into the same 3-axis labels the AI predicts,
    so predictions and ground truth are directly comparable."""

    def trend(prev, curr):
        if curr > prev * 1.05:
            return "improve"
        if curr < prev * 0.95:
            return "decline"
        return "stable"

    def risk(prev_de, curr_de):
        if curr_de > prev_de * 1.1:
            return "high"
        if curr_de < prev_de * 0.9:
            return "low"
        return "moderate"

    return {
        "trend_actual": trend(ratios_year_n["roe"], ratios_year_n_plus_1["roe"]),
        "risk_actual": risk(ratios_year_n["debt_to_equity"], ratios_year_n_plus_1["debt_to_equity"]),
        "profitability_actual": trend(
            ratios_year_n["net_profit_margin"], ratios_year_n_plus_1["net_profit_margin"]
        ),
    }


def classification_metrics(y_true: list[str], y_pred: list[str]) -> dict:
    """Accuracy/Precision/Recall/F1 for one categorical axis (e.g. trend_prediction)."""
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {"accuracy": acc, "precision": precision, "recall": recall, "f1": f1}


def mae(y_true_scores: list[float], y_pred_scores: list[float]) -> float:
    """For runs where the model predicts a continuous Financial Health Score
    rather than a category."""
    return float(np.mean(np.abs(np.array(y_true_scores) - np.array(y_pred_scores))))


def run_benchmark(samples: list[dict]) -> list[dict]:
    """samples: list of dicts, each with keys:
        - model1_pred, model2_pred, model3_pred (category labels)
        - ground_truth (category label)

    Returns one evaluation_results-shaped row per model, ready to insert into DB
    and to render as the Model 1/2/3 comparison table in the report.
    """
    results = []
    for label in ["model1_pred", "model2_pred", "model3_pred"]:
        y_true = [s["ground_truth"] for s in samples]
        y_pred = [s[label] for s in samples]
        metrics = classification_metrics(y_true, y_pred)
        results.append({
            "run_label": label,
            "n_samples": len(samples),
            **metrics,
        })
    return results
