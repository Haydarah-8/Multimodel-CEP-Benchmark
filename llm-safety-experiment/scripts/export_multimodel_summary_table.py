"""
Export publication-style summary table: models × categories (% unsafe) as CSV + PNG.

Usage:
  python scripts/export_multimodel_summary_table.py --matrix-json figures/multimodel/signature_rate_matrix.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BG = "#0d1117"
FG = "#e6edf3"
MUTED = "#8b949e"
GRID = "#30363d"
HDR = "#21262d"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-json", type=Path, required=True)
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "summary_table_models_categories.csv",
    )
    ap.add_argument(
        "--out-png",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "summary_table_models_categories.png",
    )
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    if not args.matrix_json.is_file():
        print(f"Missing {args.matrix_json}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    cats: list[str] = list(data.get("categories") or [])
    models: list[dict] = list(data.get("models") or [])
    p_hat = data.get("p_hat") or []
    metric = data.get("metric", "unsafe")

    rows_out: list[list[str]] = []
    header = ["tier", "provider", "model"] + cats + [f"row_mean_{metric}"]
    rows_out.append(header)

    table_body: list[list[str]] = []
    for i, m in enumerate(models):
        row_vals = p_hat[i] if i < len(p_hat) else []
        cells = []
        for v in row_vals:
            if v is None:
                cells.append("—")
            else:
                cells.append(f"{100.0 * float(v):.1f}%")
        nums = [float(x) for x in row_vals if x is not None]
        rmean = f"{100.0 * (sum(nums) / len(nums)):.1f}%" if nums else "—"
        table_body.append(
            [
                str(m.get("tier", "")),
                str(m.get("provider", "")),
                str(m.get("model", "")),
                *cells,
                rmean,
            ]
        )
        rows_out.append(table_body[-1])

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(rows_out)
    print(f"Wrote {args.out_csv}", file=sys.stderr)

    # PNG table
    display = [header] + table_body
    fig_w = max(14, 1.1 * len(header))
    fig_h = max(4, 0.35 * len(display))
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    fig.patch.set_facecolor(BG)
    ax.axis("off")
    tbl = ax.table(
        cellText=display,
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 1.35)
    for (r, c), cell in tbl.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(0.6)
        if r == 0:
            cell.set_facecolor(HDR)
            cell.get_text().set_color(FG)
            cell.get_text().set_fontweight("600")
        else:
            cell.set_facecolor("#161b22" if r % 2 else "#0d1117")
            cell.get_text().set_color(FG)

    fig.text(
        0.5,
        0.02,
        f"Table: % {metric} by category (n=18/cell). Nine runs; Gemini mid/expensive same model id.",
        ha="center",
        fontsize=7,
        color=MUTED,
    )
    plt.subplots_adjust(top=0.94, bottom=0.08)
    fig.savefig(args.out_png, dpi=args.dpi, facecolor=BG, edgecolor="none")
    plt.close(fig)
    print(f"Wrote {args.out_png}", file=sys.stderr)


if __name__ == "__main__":
    main()
