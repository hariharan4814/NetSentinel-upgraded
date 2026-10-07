"""Evaluation arithmetic; injected scenario roles are not malware labels."""
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix


def ratio(numerator, denominator):
    return float(numerator / denominator) if denominator else None


def classification_metrics(model, actual, predicted, labels):
    matrix = confusion_matrix(actual, predicted, labels=labels)
    rows = []
    for index, label in enumerate(labels):
        true_positive = int(matrix[index, index])
        support = int(matrix[index].sum())
        precision = ratio(true_positive, int(matrix[:, index].sum())) or 0.0
        recall = ratio(true_positive, support) or 0.0
        f1 = ratio(2 * precision * recall, precision + recall) or 0.0
        rows.append({"label": label, "precision": precision, "recall": recall,
                     "f1": f1, "support": support})
    supported = [row["recall"] for row in rows if row["support"]]
    return {"model": model, "labels": list(labels), "confusion_matrix": matrix.tolist(),
            "accuracy": ratio(int(np.trace(matrix)), int(matrix.sum())),
            "balanced_accuracy": float(np.mean(supported)) if supported else None,
            "macro_f1": float(np.mean([row["f1"] for row in rows])), "per_class": rows}


def anomaly_metrics(actual, scores, threshold, *, unscored_windows=0):
    actual, scores = np.asarray(actual, dtype=bool), np.asarray(scores, dtype=float)
    flagged = scores > threshold
    true_positive = int(np.sum(flagged & actual))
    false_positive = int(np.sum(flagged & ~actual))
    positives, benign = int(actual.sum()), int((~actual).sum())
    return {"threshold": float(threshold), "precision": ratio(true_positive, int(flagged.sum())),
            "recall": ratio(true_positive, positives),
            "false_positive_rate": ratio(false_positive, benign),
            "average_precision": float(average_precision_score(actual, scores)) if positives and benign else None,
            "false_alerts_per_hour": ratio(false_positive, benign * 10 / 3600),
            "scored_windows": len(actual), "unscored_windows": int(unscored_windows)}
