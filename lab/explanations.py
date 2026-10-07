"""Real SHAP attributions with independent additivity checks and exact fallback."""
import numpy as np

from sensor.features import FEATURE_NAMES
from .contracts import check_cancel
from .models import vectors


def checked_values(values, bases, probabilities, window_count):
    values, bases = np.asarray(values), np.asarray(bases)
    if values.shape != (window_count, len(FEATURE_NAMES), probabilities.shape[1]):
        raise ValueError("unsupported SHAP result dimensions")
    if bases.shape == (probabilities.shape[1],):
        bases = np.tile(bases, (window_count, 1))
    if bases.shape != probabilities.shape:
        raise ValueError("unsupported SHAP base dimensions")
    errors = np.abs(bases + values.sum(axis=1) - probabilities)
    if not np.all(np.isfinite(values)) or not np.all(np.isfinite(errors)) or np.any(errors > 1e-5):
        raise ValueError("SHAP additivity check failed")
    return values, bases, errors


def explain_windows(bundle, windows, *, cancelled=None):
    if not windows:
        return [], []
    check_cancel(cancelled)
    try:
        import shap
        if len(windows) > 8 or len(bundle["shap_background"]) > 64:
            raise ValueError("SHAP workload exceeds eight cases or 64 reference rows")
        x = vectors([window["features"] for window in windows])
        probabilities = bundle["random_forest"].predict_proba(x)
        warnings = []
        method = "TreeSHAP interventional class probability; training-only background"
        try:
            explainer = shap.TreeExplainer(bundle["random_forest"], data=bundle["shap_background"],
                                           feature_perturbation="interventional", model_output="probability")
            values, bases, errors = checked_values(explainer.shap_values(x, check_additivity=True),
                explainer.expected_value, probabilities, len(windows))
        except (ValueError, TypeError, AttributeError, RuntimeError, AssertionError):
            # Some supported library combinations disagree at tree boundaries.
            # Never relax the guard, repair/rescale attributions or explain a
            # surrogate. With seven features exact enumeration is bounded and
            # evaluates the actual classifier through its public predict API.
            check_cancel(cancelled)
            method = "Exact SHAP interventional class probability; training-only background"
            masker = shap.maskers.Independent(bundle["shap_background"], max_samples=64)
            exact = shap.ExactExplainer(bundle["random_forest"].predict_proba, masker)
            rows = []
            for index in range(len(x)):
                check_cancel(cancelled)
                rows.append(exact(x[index:index + 1], max_evals=2 ** len(FEATURE_NAMES), silent=True))
            values, bases, errors = checked_values(np.concatenate([row.values for row in rows]),
                np.concatenate([row.base_values for row in rows]), probabilities, len(windows))
            warnings.append("TreeSHAP could not satisfy the output check; exact SHAP enumeration of the actual classifier was used with the same training-only background.")
        result = []
        for index, window in enumerate(windows):
            check_cancel(cancelled)
            class_index = int(np.argmax(probabilities[index]))
            contributions = values[index, :, class_index]
            base, output = float(bases[index, class_index]), float(probabilities[index, class_index])
            error = float(errors[index, class_index])
            features = [{"feature": name, "value": float(x[index, feature_index]),
                         "reference_p95": bundle["references"][name]["p95"],
                         "contribution": float(contributions[feature_index])}
                        for feature_index, name in enumerate(FEATURE_NAMES)]
            features.sort(key=lambda item: abs(item["contribution"]), reverse=True)
            result.append({"window_id": window["id"],
                           "method": method,
                           "predicted_family": str(bundle["random_forest"].classes_[class_index]),
                           "base_value": base, "output_value": output,
                           "additivity_error": error, "features": features})
        return result, warnings
    except (ImportError, ValueError, TypeError, AttributeError, RuntimeError, AssertionError) as error:
        return [], [f"SHAP unavailable ({type(error).__name__}); no attribution contributions were fabricated."]
