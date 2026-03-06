import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def fmt_group(group):
    return ", ".join([f"{k} {v[0]} {v[1]}" for k, v in group.items()])


def main():
    parser = argparse.ArgumentParser(description="Summarize and plot Justicia results JSON.")
    parser.add_argument("--input", required=True, help="Path to results_*.json")
    parser.add_argument("--outdir", default="plots", help="Output directory for plots")
    args = parser.parse_args()

    input_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows = json.loads(input_path.read_text())
    folds = [r["fold"] for r in rows]
    di = [float(r["di"]) for r in rows]
    spd = [float(r["spd"]) for r in rows]
    time_sec = [float(r["time_sec"]) for r in rows]
    eo_di_y1 = [float(r["eo_di_y1_y0"][0]) for r in rows]
    eo_di_y0 = [float(r["eo_di_y1_y0"][1]) for r in rows]
    eo_spd_y1 = [float(r["eo_spd_y1_y0"][0]) for r in rows]
    eo_spd_y0 = [float(r["eo_spd_y1_y0"][1]) for r in rows]

    favored = Counter(fmt_group(r["most_favored_group"]) for r in rows)
    least = Counter(fmt_group(r["least_favored_group"]) for r in rows)

    print("Per-fold summary")
    for r in rows:
        print(
            f"fold={r['fold']} DI={r['di']:.3f} SPD={r['spd']:.3f} "
            f"EO_DI(y=1,y=0)=({r['eo_di_y1_y0'][0]:.3f},{r['eo_di_y1_y0'][1]:.3f}) "
            f"EO_SPD(y=1,y=0)=({r['eo_spd_y1_y0'][0]:.3f},{r['eo_spd_y1_y0'][1]:.3f}) "
            f"time={r['time_sec']:.3f}s"
        )

    mean_di = sum(di) / len(di)
    mean_spd = sum(spd) / len(spd)
    mean_time = sum(time_sec) / len(time_sec)
    print("\nAggregate")
    print(f"mean DI = {mean_di:.3f} (closer to 1.0 is better)")
    print(f"mean SPD = {mean_spd:.3f} (closer to 0.0 is better)")
    print(f"mean time = {mean_time:.3f}s")

    print("\nMost favored groups (count)")
    for k, v in favored.most_common():
        print(f"{v}x: {k}")
    print("\nLeast favored groups (count)")
    for k, v in least.most_common():
        print(f"{v}x: {k}")

    # Plot 1: DI and SPD per fold
    plt.figure(figsize=(8, 4))
    plt.plot(folds, di, marker="o", label="DI")
    plt.plot(folds, spd, marker="o", label="SPD")
    plt.axhline(1.0, color="gray", linestyle="--", linewidth=1, label="DI target=1")
    plt.axhline(0.0, color="black", linestyle=":", linewidth=1, label="SPD target=0")
    plt.title("Group Fairness by Fold")
    plt.xlabel("Fold")
    plt.ylabel("Metric Value")
    plt.legend()
    plt.tight_layout()
    p1 = outdir / "fairness_by_fold.png"
    plt.savefig(p1, dpi=150)
    plt.close()

    # Plot 2: EO metrics by fold
    plt.figure(figsize=(8, 4))
    plt.plot(folds, eo_di_y1, marker="o", label="EO DI (y=1)")
    plt.plot(folds, eo_di_y0, marker="o", label="EO DI (y=0)")
    plt.plot(folds, eo_spd_y1, marker="o", label="EO SPD (y=1)")
    plt.plot(folds, eo_spd_y0, marker="o", label="EO SPD (y=0)")
    plt.axhline(1.0, color="gray", linestyle="--", linewidth=1)
    plt.axhline(0.0, color="black", linestyle=":", linewidth=1)
    plt.title("Equalized-Odds-style Metrics by Fold")
    plt.xlabel("Fold")
    plt.ylabel("Metric Value")
    plt.legend(ncol=2, fontsize=8)
    plt.tight_layout()
    p2 = outdir / "eo_metrics_by_fold.png"
    plt.savefig(p2, dpi=150)
    plt.close()

    # Plot 3: runtime
    plt.figure(figsize=(8, 3.5))
    plt.bar(folds, time_sec)
    plt.title("Verification Runtime by Fold")
    plt.xlabel("Fold")
    plt.ylabel("Seconds")
    plt.tight_layout()
    p3 = outdir / "runtime_by_fold.png"
    plt.savefig(p3, dpi=150)
    plt.close()

    print("\nSaved plots:")
    print(p1)
    print(p2)
    print(p3)


if __name__ == "__main__":
    main()
