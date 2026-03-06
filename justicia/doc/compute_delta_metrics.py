import argparse
import json
import statistics as stats
from pathlib import Path


def load_rows(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a JSON list of per-fold rows.")
    return data


def by_fold(rows):
    out = {}
    for row in rows:
        if "fold" not in row:
            raise ValueError("Each row must include a 'fold' key.")
        out[int(row["fold"])] = row
    return out


def toward_fairness_improvement(di_base, di_new, spd_base, spd_new):
    # DI target is 1, SPD target is 0.
    # Positive value means the new system moved closer to the fairness target.
    di_improve = abs(1.0 - di_base) - abs(1.0 - di_new)
    spd_improve = abs(spd_base) - abs(spd_new)
    return di_improve, spd_improve


def mean_or_none(values):
    return stats.mean(values) if values else None


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compute paper-style delta metrics between a baseline and a candidate "
            "fairness verification result JSON."
        )
    )
    parser.add_argument("--baseline", required=True, help="Baseline per-fold JSON file.")
    parser.add_argument("--candidate", required=True, help="Candidate per-fold JSON file.")
    parser.add_argument("--baseline-label", default="baseline")
    parser.add_argument("--candidate-label", default="candidate")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    baseline_rows = load_rows(args.baseline)
    candidate_rows = load_rows(args.candidate)

    base_map = by_fold(baseline_rows)
    cand_map = by_fold(candidate_rows)

    common_folds = sorted(set(base_map).intersection(cand_map))
    if not common_folds:
        raise ValueError("No overlapping folds between baseline and candidate files.")

    rows = []
    for fold in common_folds:
        b = base_map[fold]
        c = cand_map[fold]
        di_base = float(b["di"])
        di_new = float(c["di"])
        spd_base = float(b["spd"])
        spd_new = float(c["spd"])
        delta_di = di_new - di_base
        delta_spd = spd_new - spd_base
        improve_di, improve_spd = toward_fairness_improvement(
            di_base, di_new, spd_base, spd_new
        )
        rows.append(
            {
                "fold": fold,
                "baseline_di": di_base,
                "candidate_di": di_new,
                "delta_di": delta_di,
                "baseline_spd": spd_base,
                "candidate_spd": spd_new,
                "delta_spd": delta_spd,
                "improve_toward_fair_di": improve_di,
                "improve_toward_fair_spd": improve_spd,
            }
        )

    summary = {
        "baseline": str(Path(args.baseline)),
        "candidate": str(Path(args.candidate)),
        "baseline_label": args.baseline_label,
        "candidate_label": args.candidate_label,
        "num_common_folds": len(common_folds),
        "mean_delta_di": mean_or_none([r["delta_di"] for r in rows]),
        "mean_delta_spd": mean_or_none([r["delta_spd"] for r in rows]),
        "mean_improve_toward_fair_di": mean_or_none(
            [r["improve_toward_fair_di"] for r in rows]
        ),
        "mean_improve_toward_fair_spd": mean_or_none(
            [r["improve_toward_fair_spd"] for r in rows]
        ),
    }

    result = {"summary": summary, "rows": rows}

    if args.output is not None:
        output = args.output
    else:
        bname = Path(args.baseline).stem
        cname = Path(args.candidate).stem
        output = f"delta_{cname}_vs_{bname}.json"

    with open(output, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("Delta summary:")
    print(json.dumps(summary, indent=2))
    print(f"\nSaved delta results to {output}")


if __name__ == "__main__":
    main()
