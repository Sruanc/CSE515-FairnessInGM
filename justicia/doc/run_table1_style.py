import argparse
import importlib
import importlib.util
import json
import random
import statistics as stats
import sys
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

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
from justicia import utils
from justicia.metrics import Metric


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


def get_dataset(name, config):
    if name == "adult":
        return Adult(verbose=False, config=config)
    if name == "compas":
        return Compas(verbose=False, config=config)
    raise ValueError(name)


def one_hot_and_split(dataset, fraction):
    df = dataset.get_df(repaired=False)
    x = df.drop(["target"], axis=1)
    y = df["target"]

    random.seed(10)
    if fraction != 1:
        non_sensitive = [
            col for col in x.columns if col not in dataset.known_sensitive_attributes
        ]
        sub_columns = random.sample(non_sensitive, int(fraction * len(non_sensitive)))
        x = x[sub_columns + dataset.known_sensitive_attributes]

    x = utils.get_one_hot_encoded_df(x, dataset.categorical_attributes)
    return x, y


def sensitive_columns(encoded_df, known_sensitive_attributes):
    sens_cols = []
    for col in encoded_df.columns:
        prefix = col.split("_")[0]
        if prefix in known_sensitive_attributes or col in known_sensitive_attributes:
            sens_cols.append(col)
    return sens_cols


def compound_group_key(df, sens_cols):
    # Build a deterministic compound group identifier from sensitive columns.
    if not sens_cols:
        return pd.Series(["ALL"] * len(df), index=df.index)
    return df[sens_cols].astype(str).agg("|".join, axis=1)


def reweighing_weights(x_train, y_train, sens_cols):
    # Kamiran-Calders style weights: w(a,y)=P(a)P(y)/P(a,y)
    a_key = compound_group_key(x_train, sens_cols)
    n = len(x_train)
    if n == 0:
        return pd.Series(dtype=float)

    p_y = y_train.value_counts(normalize=True)
    p_a = a_key.value_counts(normalize=True)
    joint_counts = pd.crosstab(a_key, y_train)
    p_ay = joint_counts / n

    weights = []
    for idx in x_train.index:
        a = a_key.loc[idx]
        y = y_train.loc[idx]
        p_joint = float(p_ay.loc[a, y]) if (a in p_ay.index and y in p_ay.columns) else 0.0
        if p_joint <= 0:
            w = 1.0
        else:
            w = float(p_a.loc[a]) * float(p_y.loc[y]) / p_joint
        weights.append(w)

    out = pd.Series(weights, index=x_train.index, dtype=float)
    # Stabilize to mean 1 to keep optimization scale comparable.
    mean_w = out.mean()
    if mean_w > 0:
        out = out / mean_w
    return out


def run_method(
    method,
    x,
    y,
    known_sensitive_attributes,
    encoding,
    class_weight,
):
    if method == "op" and not importlib.util.find_spec("aif360"):
        raise RuntimeError(
            "Method 'op' requested but aif360 is not installed. "
            "Install aif360 to reproduce OP exactly."
        )

    kf = KFold(n_splits=5, shuffle=True, random_state=10)
    rows = []

    sens_cols = sensitive_columns(x, known_sensitive_attributes)
    for fold, (train_idx, test_idx) in enumerate(kf.split(x, y)):
        x_train = x.iloc[train_idx].copy()
        y_train = y.iloc[train_idx].copy()
        x_test = x.iloc[test_idx].copy()
        y_test = y.iloc[test_idx].copy()

        sample_weight = None
        if method == "rw":
            sample_weight = reweighing_weights(x_train, y_train, sens_cols)

        # NOTE: OP needs aif360's OptimPreproc implementation.
        if method == "op":
            raise RuntimeError(
                "Method 'op' is reserved for aif360 Optimized Preprocessing and "
                "is not enabled in this script without aif360."
            )

        clf = LogisticRegression(
            class_weight=class_weight if class_weight != "none" else None,
            solver="liblinear",
            random_state=0,
        )
        fit_kwargs = {}
        if sample_weight is not None:
            fit_kwargs["sample_weight"] = sample_weight.to_numpy()
        clf.fit(x_train, y_train, **fit_kwargs)

        metric = Metric(
            model=clf,
            data=x_test,
            sensitive_attributes=known_sensitive_attributes,
            encoding=encoding,
            verbose=False,
        ).compute()
        metric_eqo = Metric(
            model=clf,
            data=x_test,
            sensitive_attributes=known_sensitive_attributes,
            encoding=encoding,
            verbose=False,
        ).compute_eqo(y_test)
        p_max, p_min = extract_probability_bounds(metric)

        row = {
            "fold": fold,
            "method": method,
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

    return rows


def aggregate(rows):
    return {
        "mean_di": stats.mean(r["di"] for r in rows),
        "mean_spd": stats.mean(r["spd"] for r in rows),
        "mean_p_max": stats.mean(r["p_max"] for r in rows if r["p_max"] is not None),
        "mean_p_min": stats.mean(r["p_min"] for r in rows if r["p_min"] is not None),
        "mean_time_sec": stats.mean(r["time_sec"] for r in rows),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run paper-style mitigation comparison for Justicia verification. "
            "Supported methods: orig, rw (op requires aif360)."
        )
    )
    parser.add_argument("--dataset", choices=["adult", "compas"], default="adult")
    parser.add_argument("--config", type=int, default=0)
    parser.add_argument("--encoding", default="best-correlated")
    parser.add_argument("--fraction", type=float, default=0.5)
    parser.add_argument(
        "--methods",
        default="orig,rw",
        help="Comma-separated list from {orig,rw,op}. Default: orig,rw",
    )
    parser.add_argument(
        "--class-weight",
        choices=["balanced", "none"],
        default="balanced",
        help="Class-weight mode for LogisticRegression. Default: balanced",
    )
    parser.add_argument(
        "--out-prefix",
        default=None,
        help="Optional output prefix. Defaults to dataset/config/encoding/fraction",
    )
    args = parser.parse_args()

    methods = [m.strip().lower() for m in args.methods.split(",") if m.strip()]
    valid = {"orig", "rw", "op"}
    bad = [m for m in methods if m not in valid]
    if bad:
        raise ValueError(f"Unsupported method(s): {bad}")

    dataset = get_dataset(args.dataset, args.config)
    x, y = one_hot_and_split(dataset, args.fraction)

    frac_tag = str(args.fraction).replace(".", "p")
    base_prefix = (
        args.out_prefix
        if args.out_prefix
        else f"{args.dataset}_cfg{args.config}_lr_{args.encoding}_frac{frac_tag}"
    )

    manifest = {
        "dataset": args.dataset,
        "config": args.config,
        "encoding": args.encoding,
        "fraction": args.fraction,
        "class_weight": args.class_weight,
        "methods": {},
    }

    for method in methods:
        print(f"\n=== Running method: {method} ===", flush=True)
        rows = run_method(
            method=method,
            x=x,
            y=y,
            known_sensitive_attributes=dataset.known_sensitive_attributes,
            encoding=args.encoding,
            class_weight=args.class_weight,
        )
        out = f"results_{base_prefix}_{method}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2)
        agg = aggregate(rows)
        print(f"Saved {out}", flush=True)
        print(f"Aggregate {method}: {agg}", flush=True)
        manifest["methods"][method] = {"file": out, "aggregate": agg}

    manifest_file = f"manifest_{base_prefix}.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nSaved manifest to {manifest_file}", flush=True)


if __name__ == "__main__":
    main()
