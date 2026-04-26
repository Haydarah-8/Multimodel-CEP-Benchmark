"""
Interactive Plotly heatmap: unsafe and risk rates with metric toggle (offline HTML).

Usage:
  python scripts/plot_multimodel_interactive_matrix.py \\
    --matrix-unsafe figures/multimodel/signature_rate_matrix.json \\
    --matrix-risk figures/multimodel/signature_rate_matrix_risk.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_matrix(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix-unsafe", type=Path, required=True)
    ap.add_argument("--matrix-risk", type=Path, required=True)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "figures" / "multimodel" / "interactive_rates.html",
    )
    args = ap.parse_args()

    try:
        import plotly.graph_objects as go
    except ImportError:
        print("plotly required", file=sys.stderr)
        sys.exit(1)

    for p in (args.matrix_unsafe, args.matrix_risk):
        if not p.is_file():
            print(f"Missing {p}", file=sys.stderr)
            sys.exit(1)

    du = load_matrix(args.matrix_unsafe)
    dr = load_matrix(args.matrix_risk)

    def build_fig(data: dict, title: str) -> go.Figure:
        cats = data.get("categories") or []
        models = data.get("models") or []
        p_hat = data.get("p_hat") or []
        nmat = data.get("n") or []
        y_labels = [f"[{m.get('tier')}] {m.get('provider')}/{m.get('model')}" for m in models]
        z = [[(None if v is None else round(100.0 * float(v), 1)) for v in row] for row in p_hat]
        text = []
        for i, row in enumerate(p_hat):
            tr = []
            for j, v in enumerate(row):
                nn = nmat[i][j] if i < len(nmat) and j < len(nmat[i]) else ""
                pct = f"{100.0 * float(v):.1f}%" if v is not None else "—"
                tr.append(f"n={nn}<br>{pct}")
            text.append(tr)
        fig = go.Figure(
            data=go.Heatmap(
                z=z,
                x=cats,
                y=y_labels,
                text=text,
                texttemplate="%{z}%",
                textfont={"size": 10},
                colorscale=[
                    [0, "rgb(18,22,28)"],
                    [0.5, "rgb(60,40,36)"],
                    [1, "rgb(154,82,48)"],
                ],
                zmin=0,
                zmax=100,
                hovertemplate="%{y}<br>%{x}<br>%{text}<extra></extra>",
                colorbar=dict(title="%"),
            )
        )
        fig.update_layout(
            title=title,
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font=dict(color="#e6edf3", size=12),
            xaxis=dict(side="bottom", gridcolor="#30363d"),
            yaxis=dict(gridcolor="#30363d", autorange="reversed"),
            margin=dict(l=220, r=40, t=60, b=80),
            height=max(420, 44 * len(y_labels)),
        )
        return fig

    fig_u = build_fig(du, "Multimodel rates: % UNSAFE (hover for n)")
    fig_r = build_fig(dr, "Multimodel rates: % risk (P ∪ U)")

    combined = go.Figure()
    for trace in fig_u.data:
        combined.add_trace(trace)
    combined.data[0].visible = True
    trace_r = fig_r.data[0]
    trace_r.visible = False
    combined.add_trace(trace_r)

    combined.update_layout(
        title="Multimodel category rates (toggle metric)",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#e6edf3", size=12),
        xaxis=dict(side="bottom", gridcolor="#30363d"),
        yaxis=dict(gridcolor="#30363d", autorange="reversed"),
        margin=dict(l=220, r=40, t=80, b=80),
        height=max(420, 44 * len(du.get("models") or [])),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                x=0.0,
                y=1.12,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label=" % UNSAFE ",
                        method="update",
                        args=[
                            {"visible": [True, False]},
                            {"title": "Multimodel rates: % UNSAFE"},
                        ],
                    ),
                    dict(
                        label=" % risk ",
                        method="update",
                        args=[
                            {"visible": [False, True]},
                            {"title": "Multimodel rates: % risk (P ∪ U)"},
                        ],
                    ),
                ],
            )
        ],
    )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    combined.write_html(
        args.out,
        include_plotlyjs="cdn",
        config={"displayModeBar": True},
    )
    print(f"Wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
