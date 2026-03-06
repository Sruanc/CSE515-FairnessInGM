import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_runtime_by_fold(path):
    rows = json.loads(Path(path).read_text())
    runtime = {int(r["fold"]): float(r["time_sec"]) for r in rows}
    return runtime


def main():
    parser = argparse.ArgumentParser(
        description="Plot fold-wise runtime comparison between two Justicia runs."
    )
    parser.add_argument("--baseline", required=True, help="Path to baseline results_*.json")
    parser.add_argument("--candidate", required=True, help="Path to candidate results_*.json")
    parser.add_argument("--baseline-label", default="best", help="Legend label for baseline")
    parser.add_argument(
        "--candidate-label", default="best-correlated", help="Legend label for candidate"
    )
    parser.add_argument("--outdir", default="plots_runtime_compare", help="Output directory")
    args = parser.parse_args()

    baseline = load_runtime_by_fold(args.baseline)
    candidate = load_runtime_by_fold(args.candidate)

    folds = sorted(set(baseline.keys()) & set(candidate.keys()))
    if not folds:
        raise ValueError("No overlapping folds between baseline and candidate files.")

    b_vals = [baseline[f] for f in folds]
    c_vals = [candidate[f] for f in folds]

    x = list(range(len(folds)))
    w = 0.38

    plt.figure(figsize=(8, 4))
    plt.bar([i - w / 2 for i in x], b_vals, width=w, label=args.baseline_label)
    plt.bar([i + w / 2 for i in x], c_vals, width=w, label=args.candidate_label)
    plt.xticks(x, folds)
    plt.xlabel("Fold")
    plt.ylabel("Seconds")
    plt.title("Verification Runtime by Fold (Assumption Comparison)")
    plt.legend()
    plt.tight_layout()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "runtime_comparison_by_fold.png"
    plt.savefig(out, dpi=150)
    plt.close()

    mean_b = sum(b_vals) / len(b_vals)
    mean_c = sum(c_vals) / len(c_vals)
    print(f"Mean runtime ({args.baseline_label}): {mean_b:.6f}s")
    print(f"Mean runtime ({args.candidate_label}): {mean_c:.6f}s")
    print(f"Saved plot: {out}")


if __name__ == "__main__":
    main()
