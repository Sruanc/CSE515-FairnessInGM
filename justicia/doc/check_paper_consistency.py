import argparse
import json
import statistics as stats
import sys
from pathlib import Path
import importlib
import logging
import math

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
from justicia import utils

logging.getLogger("pgmpy").setLevel(logging.ERROR)


def extract_probability_bounds(metric):
    probs = []
    for item in metric.sensitive_group_statistics:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            probs.append(float(item[1]))

    if probs:
        return max(probs), min(probs)

    di = float(metric.disparate_impact_ratio)
    spd = float(metric.statistical_parity_difference)
    if abs(1.0 - di) < 1e-12:
        return None, None
    p_max = spd / (1.0 - di)
    p_min = di * p_max
    return p_max, p_min


def run_config(dataset_name, config, model, encoding, fraction):
    dataset = (
        Adult(verbose=False, config=config)
        if dataset_name == "adult"
        else Compas(verbose=False, config=config)
    )

    models, _, X_tests, sensitive_attrs = linear_classifier_wrap.init(
        dataset,
        classifier=model,
        verbose=False,
        compute_equalized_odds=False,
        fraction=fraction,
    )

    # Estimate theoretical number of compound sensitive groups from encoded columns.
    # For single binary columns, Justicia internally considers both literal and negation.
    encoded_sensitive_groups = utils.get_sensitive_attibutes(
        dataset.known_sensitive_attributes, X_tests[0].columns.to_list()
    )
    sensitive_attribute_cardinalities = [
        2 if len(group) == 1 else len(group) for group in encoded_sensitive_groups
    ]
    compound_group_count_estimate = math.prod(sensitive_attribute_cardinalities)

    rows = []
    for fold, (clf, X_test) in enumerate(zip(models, X_tests)):
        metric = Metric(
            model=clf,
            data=X_test,
            sensitive_attributes=sensitive_attrs,
            encoding=encoding,
            verbose=False,
        ).compute()
        p_max, p_min = extract_probability_bounds(metric)
        rows.append(
            {
                "fold": fold,
                "di": float(metric.disparate_impact_ratio),
                "spd": float(metric.statistical_parity_difference),
                "p_max": p_max,
                "p_min": p_min,
                "time_sec": float(metric.time_taken),
                "num_compound_groups": len(metric.sensitive_group_statistics),
            }
        )

    summary = {
        "config": config,
        "sensitive_attributes": sensitive_attrs,
        "sensitive_attribute_cardinalities": sensitive_attribute_cardinalities,
        "num_compound_groups_estimate": compound_group_count_estimate,
        "mean_di": stats.mean(r["di"] for r in rows),
        "mean_spd": stats.mean(r["spd"] for r in rows),
        "mean_p_max": stats.mean(r["p_max"] for r in rows if r["p_max"] is not None),
        "mean_p_min": stats.mean(r["p_min"] for r in rows if r["p_min"] is not None),
        "mean_time_sec": stats.mean(r["time_sec"] for r in rows),
        "mean_num_compound_groups": stats.mean(r["num_compound_groups"] for r in rows),
        "rows": rows,
    }
    return summary


def trend_checks(summaries):
    ordered = sorted(summaries, key=lambda s: s["num_compound_groups_estimate"])
    di_non_increasing = all(
        ordered[i]["mean_di"] >= ordered[i + 1]["mean_di"]
        for i in range(len(ordered) - 1)
    )
    spd_non_decreasing = all(
        ordered[i]["mean_spd"] <= ordered[i + 1]["mean_spd"]
        for i in range(len(ordered) - 1)
    )
    return {
        "ordered_by_compound_groups": [
            {
                "config": s["config"],
                "groups": s["num_compound_groups_estimate"],
                "mean_di": s["mean_di"],
                "mean_spd": s["mean_spd"],
            }
            for s in ordered
        ],
        "di_non_increasing_with_more_groups": di_non_increasing,
        "spd_non_decreasing_with_more_groups": spd_non_decreasing,
    }


def parse_configs(config_str):
    return [int(x.strip()) for x in config_str.split(",") if x.strip()]


def main():
    parser = argparse.ArgumentParser(
        description="Check consistency of reproduced fairness trends with the AAAI paper."
    )
    parser.add_argument("--dataset", choices=["adult", "compas"], default="adult")
    parser.add_argument("--model", choices=["lr", "svm-linear"], default="lr")
    parser.add_argument("--encoding", default="best-correlated")
    parser.add_argument(
        "--fraction",
        type=float,
        default=1.0,
        help="Fraction of non-sensitive features to include (1.0 keeps all).",
    )
    parser.add_argument(
        "--configs",
        default="2,6,0,4",
        help="Comma-separated dataset sensitive-group configs to evaluate.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional explicit output JSON filename.",
    )
    args = parser.parse_args()

    configs = parse_configs(args.configs)
    summaries = []

    for config in configs:
        summary = run_config(
            dataset_name=args.dataset,
            config=config,
            model=args.model,
            encoding=args.encoding,
            fraction=args.fraction,
        )
        summaries.append(summary)
        print(
            (
                f"config={config} sensitive={summary['sensitive_attributes']} "
                f"groups={summary['num_compound_groups_estimate']} "
                f"DI={summary['mean_di']:.4f} SPD={summary['mean_spd']:.4f} "
                f"p_max={summary['mean_p_max']:.4f} p_min={summary['mean_p_min']:.4f} "
                f"time={summary['mean_time_sec']:.3f}s"
            ),
            flush=True,
        )

    trends = trend_checks(summaries)
    print("\nTrend checks:", flush=True)
    print(json.dumps(trends, indent=2), flush=True)

    result = {
        "dataset": args.dataset,
        "model": args.model,
        "encoding": args.encoding,
        "fraction": args.fraction,
        "configs": configs,
        "summaries": summaries,
        "trend_checks": trends,
    }

    if args.output is not None:
        output_file = args.output
    else:
        frac_tag = str(args.fraction).replace(".", "p")
        output_file = (
            f"paper_consistency_{args.dataset}_{args.model}_"
            f"{args.encoding}_frac{frac_tag}.json"
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved consistency results to {output_file}", flush=True)


if __name__ == "__main__":
    main()
