import argparse
import importlib
import importlib.util
import json
import random
import statistics as stats
import sys
from pathlib import Path

import numpy as np
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


def _op_binned_frame(x_train, x_test):
    train = x_train.copy()
    test = x_test.copy()

    for col in train.columns:
        nunique = train[col].nunique()
        if nunique > 8:
            edges = np.unique(np.quantile(train[col], [0, 0.25, 0.5, 0.75, 1.0]))
            if len(edges) < 2:
                train[col] = 0.0
                test[col] = 0.0
            else:
                train[col] = pd.cut(
                    train[col],
                    bins=edges,
                    include_lowest=True,
                    labels=False,
                    duplicates="drop",
                ).astype(float)
                test[col] = pd.cut(
                    test[col],
                    bins=edges,
                    include_lowest=True,
                    labels=False,
                    duplicates="drop",
                ).fillna(-1).astype(float)
        else:
            train[col] = train[col].astype(float)
            test[col] = test[col].astype(float)

    return train, test


def _op_distortion(sens_cols):
    def distortion(vold, vnew):
        bad = 10.0
        total = 0.0
        for key, old in vold.items():
            new = vnew.get(key, old)
            if key in sens_cols and new != old:
                return bad
            if key == "target":
                if new != old:
                    total += 1.0
            elif new != old:
                total += 0.5
        return total

    return distortion


def apply_optimized_preprocessing(x_train, y_train, x_test, sens_cols):
    from aif360.algorithms.preprocessing.optim_preproc import OptimPreproc
    from aif360.algorithms.preprocessing.optim_preproc_helpers.opt_tools import OptTools
    from aif360.datasets import BinaryLabelDataset

    x_train_binned, x_test_binned = _op_binned_frame(x_train, x_test)
    train_df = x_train_binned.copy()
    train_df["target"] = y_train.astype(float)
    test_df = x_test_binned.copy()
    test_df["target"] = 0.0

    train_bld = BinaryLabelDataset(
        df=train_df,
        label_names=["target"],
        protected_attribute_names=sens_cols,
        favorable_label=1.0,
        unfavorable_label=0.0,
    )
    test_bld = BinaryLabelDataset(
        df=test_df,
        label_names=["target"],
        protected_attribute_names=sens_cols,
        favorable_label=1.0,
        unfavorable_label=0.0,
    )
    meta = {
        "label_maps": [{1.0: "1", 0.0: "0"}],
        "protected_attribute_maps": [{1.0: "1", 0.0: "0"} for _ in sens_cols],
    }
    train_bld.metadata.update(meta)
    test_bld.metadata.update(meta)

    optim_options = {
        "distortion_fun": _op_distortion(sens_cols),
        "epsilon": 0.05,
        "clist": [0.99, 1.99, 2.99],
        "dlist": [0.1, 0.05, 0.0],
    }
    op = OptimPreproc(OptTools, optim_options, verbose=False)
    op = op.fit(train_bld)
    train_transformed = op.transform(train_bld, transform_Y=True)
    test_transformed = op.transform(test_bld, transform_Y=True)

    transformed_train_df = train_transformed.convert_to_dataframe()[0]
    transformed_test_df = test_transformed.convert_to_dataframe()[0]
    x_train_out = transformed_train_df.drop(columns=["target"]).astype(float)
    y_train_out = transformed_train_df["target"].round().astype(int)
    x_test_out = transformed_test_df.drop(columns=["target"]).astype(float)

    return x_train_out, y_train_out, x_test_out


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

        if method == "op":
            x_train, y_train, x_test = apply_optimized_preprocessing(
                x_train=x_train,
                y_train=y_train,
                x_test=x_test,
                sens_cols=sens_cols,
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
            "Supported methods: orig, rw, op (OP requires aif360 and cvxpy)."
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
