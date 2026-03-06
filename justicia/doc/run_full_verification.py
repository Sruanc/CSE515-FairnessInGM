import argparse
import json
import statistics as stats
import sys
from pathlib import Path
import importlib

# Ensure imports work when running from either `justicia/` or `justicia/doc/`.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Compatibility shim for feature_engine API renames used by Justicia/pyrulelearn.
try:
    discretisation_mod = importlib.import_module("feature_engine.discretisation")
    sys.modules.setdefault("feature_engine.discretisers", discretisation_mod)
except Exception:
    pass
try:
    discretisers_mod = importlib.import_module("feature_engine.discretisers")
    sys.modules.setdefault("feature_engine.discretisation", discretisers_mod)
except Exception:
    pass

from data.objects.adult import Adult
from data.objects.compas import Compas
from justicia import linear_classifier_wrap
from justicia.metrics import Metric


def extract_probability_bounds(metric):
    # In Learn/Learn-efficient modes, statistics usually contains max and min groups.
    probs = []
    for item in metric.sensitive_group_statistics:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            probs.append(float(item[1]))

    if probs:
        return max(probs), min(probs)

    # Fallback: derive from DI=min/max and SPD=max-min if needed.
    di = float(metric.disparate_impact_ratio)
    spd = float(metric.statistical_parity_difference)
    if abs(1.0 - di) < 1e-12:
        return None, None
    p_max = spd / (1.0 - di)
    p_min = di * p_max
    return p_max, p_min


def main():
    parser = argparse.ArgumentParser(
        description="Run full fairness verification on Adult or COMPAS."
    )
    parser.add_argument("--dataset", choices=["adult", "compas"], default="adult")
    parser.add_argument("--config", type=int, default=0)
    parser.add_argument("--model", choices=["lr", "svm-linear"], default="lr")
    parser.add_argument("--encoding", default="best")
    parser.add_argument(
        "--fraction",
        type=float,
        default=0.5,
        help="Fraction of non-sensitive features to include (1.0 keeps all).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit output JSON filename.",
    )
    args = parser.parse_args()

    dataset = Adult(verbose=False, config=args.config) if args.dataset == "adult" else Compas(
        verbose=False, config=args.config
    )

    models, _, X_tests, sensitive_attrs, _, y_tests = linear_classifier_wrap.init(
        dataset,
        classifier=args.model,
        verbose=False,
        compute_equalized_odds=True,
        fraction=args.fraction,
    )

    rows = []
    for fold, (model, X_test, y_test) in enumerate(zip(models, X_tests, y_tests)):
        metric = Metric(
            model=model,
            data=X_test,
            sensitive_attributes=sensitive_attrs,
            encoding=args.encoding,
            verbose=False,
        ).compute()
        metric_eqo = Metric(
            model=model,
            data=X_test,
            sensitive_attributes=sensitive_attrs,
            encoding=args.encoding,
            verbose=False,
        ).compute_eqo(y_test)
        p_max, p_min = extract_probability_bounds(metric)

        row = {
            "fold": fold,
            "di": metric.disparate_impact_ratio,
            "spd": metric.statistical_parity_difference,
            "p_max": p_max,
            "p_min": p_min,
            "time_sec": metric.time_taken,
            "most_favored_group": metric.most_favored_group,
            "least_favored_group": metric.least_favored_group,
            "eo_di_y1_y0": metric_eqo.disparate_impact_ratio,
            "eo_spd_y1_y0": metric_eqo.statistical_parity_difference,
            "eo_time_sec": metric_eqo.time_taken,
        }
        rows.append(row)
        print(row, flush=True)

    aggregate = {
        "dataset": args.dataset,
        "config": args.config,
        "model": args.model,
        "encoding": args.encoding,
        "fraction": args.fraction,
        "sensitive_attributes": sensitive_attrs,
        "mean_di": stats.mean(r["di"] for r in rows),
        "mean_spd": stats.mean(r["spd"] for r in rows),
        "mean_p_max": stats.mean(r["p_max"] for r in rows if r["p_max"] is not None),
        "mean_p_min": stats.mean(r["p_min"] for r in rows if r["p_min"] is not None),
        "mean_time_sec": stats.mean(r["time_sec"] for r in rows),
    }
    print("\nAggregate:", flush=True)
    print(aggregate, flush=True)

    if args.output is not None:
        output_file = args.output
    else:
        frac_tag = str(args.fraction).replace(".", "p")
        output_file = (
            f"results_{args.dataset}_cfg{args.config}_{args.model}_"
            f"{args.encoding}_frac{frac_tag}.json"
        )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"\nSaved per-fold results to {output_file}", flush=True)


if __name__ == "__main__":
    main()
