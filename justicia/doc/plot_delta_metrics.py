import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description="Plot fold-wise delta fairness metrics.")
    parser.add_argument("--input", required=True, help="Path to delta_*.json")
    parser.add_argument(
        "--baseline-label",
        default="baseline",
        help="Human-readable baseline label for plot titles",
    )
    parser.add_argument(
        "--candidate-label",
        default="candidate",
        help="Human-readable candidate label for plot titles",
    )
    parser.add_argument("--outdir", default="plots_delta", help="Output directory")
    args = parser.parse_args()

    in_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    payload = json.loads(in_path.read_text())
    rows = payload["rows"]
    summary = payload["summary"]

    folds = [int(r["fold"]) for r in rows]
    delta_di = [float(r["delta_di"]) for r in rows]
    delta_spd = [float(r["delta_spd"]) for r in rows]
    improve_di = [float(r["improve_toward_fair_di"]) for r in rows]
    improve_spd = [float(r["improve_toward_fair_spd"]) for r in rows]

    # Plot 1: raw deltas
    plt.figure(figsize=(8, 4))
    plt.plot(folds, delta_di, marker="o", label=r"$\Delta$DI")
    plt.plot(folds, delta_spd, marker="o", label=r"$\Delta$SPD")
    plt.axhline(0.0, color="black", linestyle=":", linewidth=1)
    plt.title(
        f"Fold-wise Delta Fairness Metrics ({args.candidate_label} - {args.baseline_label})"
    )
    plt.xlabel("Fold")
    plt.ylabel("Delta Value")
    plt.legend()
    plt.tight_layout()
    p1 = outdir / "delta_metrics_by_fold.png"
    plt.savefig(p1, dpi=150)
    plt.close()

    # Plot 2: toward-fairness improvement
    plt.figure(figsize=(8, 4))
    plt.plot(folds, improve_di, marker="o", label="Improve toward DI target")
    plt.plot(folds, improve_spd, marker="o", label="Improve toward SPD target")
    plt.axhline(0.0, color="black", linestyle=":", linewidth=1)
    plt.title(
        f"Toward-Fairness Improvement ({args.candidate_label} - {args.baseline_label})"
    )
    plt.xlabel("Fold")
    plt.ylabel("Improvement (positive is better)")
    plt.legend()
    plt.tight_layout()
    p2 = outdir / "delta_improvement_by_fold.png"
    plt.savefig(p2, dpi=150)
    plt.close()

    print("Delta summary:")
    print(json.dumps(summary, indent=2))
    print("\nSaved plots:")
    print(p1)
    print(p2)


if __name__ == "__main__":
    main()
