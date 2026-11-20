"""Historical Validation & Metrics for Banking — B4.

So khớp dự đoán của AI / Scoring với Ground Truth thực tế của ngân hàng ở kỳ tiếp theo.
"""

from typing import Dict, List
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support


def derive_ground_truth(ratios_period_n: dict, ratios_period_n_plus_1: dict) -> dict:
    """Tạo nhãn Ground Truth thực tế từ 2 kỳ liên tiếp của ngân hàng.
    - trend_actual: Dựa trên xu hướng biến động của ROE năm hóa (tăng/giảm >5%).
    - risk_actual: Dựa trên LDR và Lãi dự thu (ACCRUED_INT).
    - profitability_actual: Dựa trên NIM và ROA.
    """
    def calc_trend(prev: float, curr: float) -> str:
        if prev is None or curr is None:
            return "stable"
        if curr > prev * 1.05:
            return "improve"
        if curr < prev * 0.95:
            return "decline"
        return "stable"

    def calc_risk(ratios: dict) -> str:
        ldr = ratios.get("LDR", 80.0)
        acc_int = ratios.get("ACCRUED_INT", 1.0)
        # Rủi ro cao nếu căng thẳng thanh khoản hoặc lãi dự thu cao bất thường
        if ldr > 90.0 or acc_int > 1.8:
            return "high"
        if ldr < 80.0 and acc_int < 0.8:
            return "low"
        return "moderate"

    # Lấy ROE và NIM
    roe_n = ratios_period_n.get("ROE") or ratios_period_n.get("ROE_%")
    roe_next = ratios_period_n_plus_1.get("ROE") or ratios_period_n_plus_1.get("ROE_%")

    nim_n = ratios_period_n.get("NIM") or ratios_period_n.get("NIM_%")
    nim_next = ratios_period_n_plus_1.get("NIM") or ratios_period_n_plus_1.get("NIM_%")

    return {
        "trend_actual": calc_trend(roe_n, roe_next),
        "risk_actual": calc_risk(ratios_period_n_plus_1),
        "profitability_actual": calc_trend(nim_n, nim_next),
    }


def classification_metrics(y_true: List[str], y_pred: List[str]) -> Dict[str, float]:
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    return {
        "accuracy": float(acc),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
    }


def mae(y_true_scores: List[float], y_pred_scores: List[float]) -> float:
    return float(np.mean(np.abs(np.array(y_true_scores) - np.array(y_pred_scores))))
