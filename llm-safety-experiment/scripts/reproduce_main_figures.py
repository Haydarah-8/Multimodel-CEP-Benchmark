"""
One entrypoint to refresh pilot + multimodel figures used in reports (no API calls).

From llm-safety-experiment:
  python scripts/reproduce_main_figures.py
  python scripts/reproduce_main_figures.py --skip-pilot
  python scripts/reproduce_main_figures.py --skip-fingerprints

Steps:
  1. Audit multimodel JSON (ERROR / labels)
  2. Pilot: compute_significance, verify_artifact_chain, generate_report_figures
  3. build_multimodel_rate_matrix (unsafe + risk), signature heatmaps, 9-panel (Wilson CIs) + radar grid
  4. fingerprint_all_multimodel, safety_frontier, fingerprint PCA
  5. Optional `--extra-visuals`: parallel coords, forest, clustermap, tier slope, composition, table, correlation, ranks, Plotly HTML
  6. Optional `--phd-visuals`: McNemar pairwise matrix, Jeffreys Beta credible intervals, tier×provider interaction lines
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    r = subprocess.run(cmd, cwd=str(cwd), check=False)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    ap = argparse.ArgumentParser(description="Regenerate main pilot + multimodel figures")
    ap.add_argument("--skip-pilot", action="store_true")
    ap.add_argument("--skip-fingerprints", action="store_true")
    ap.add_argument("--skip-audit", action="store_true")
    ap.add_argument("--strict-audit", action="store_true", help="Fail if audit finds issues")
    ap.add_argument("--sankey", action="store_true", help="Include Sankey in pilot figures")
    ap.add_argument(
        "--extra-visuals",
        action="store_true",
        help="Also build extended multimodel charts (parallel coords, forest, clustermap, tier slope, "
        "composition, summary table, category correlation, ranks, interactive HTML)",
    )
    ap.add_argument(
        "--phd-visuals",
        action="store_true",
        help="Publication-style diagnostics: paired McNemar 9×9, Jeffreys Beta posterior intervals, tier×provider interaction facets",
    )
    args = ap.parse_args()

    py = sys.executable
    scripts = ROOT / "scripts"

    if not args.skip_audit:
        audit_cmd = [str(py), str(scripts / "audit_multimodel_artifacts.py")]
        if args.strict_audit:
            audit_cmd.append("--strict")
        run(audit_cmd)

    if not args.skip_pilot:
        run([str(py), str(scripts / "compute_significance.py")])
        run([str(py), str(scripts / "verify_artifact_chain.py")])
        fig_cmd = [str(py), str(scripts / "generate_report_figures.py")]
        if not args.sankey:
            fig_cmd.append("--skip-sankey")
        run(fig_cmd)

    matrix_unsafe = ROOT / "figures" / "multimodel" / "signature_rate_matrix.json"
    matrix_risk = ROOT / "figures" / "multimodel" / "signature_rate_matrix_risk.json"

    run(
        [
            str(py),
            str(scripts / "build_multimodel_rate_matrix.py"),
            "--metric",
            "unsafe",
            "--out",
            str(matrix_unsafe),
        ]
    )
    run(
        [
            str(py),
            str(scripts / "build_multimodel_rate_matrix.py"),
            "--metric",
            "risk",
            "--out",
            str(matrix_risk),
        ]
    )

    mm = ROOT / "figures" / "multimodel"
    run(
        [
            str(py),
            str(scripts / "plot_multimodel_signature_heatmap.py"),
            "--matrix-json",
            str(matrix_unsafe),
            "--kind",
            "raw",
            "--out",
            str(mm / "combined_signature_unsafe_heatmap.png"),
        ]
    )
    run(
        [
            str(py),
            str(scripts / "plot_multimodel_signature_heatmap.py"),
            "--matrix-json",
            str(matrix_unsafe),
            "--kind",
            "excess_vs_direct",
            "--out",
            str(mm / "combined_signature_excess_vs_direct.png"),
        ]
    )
    run(
        [
            str(py),
            str(scripts / "plot_multimodel_signature_heatmap.py"),
            "--matrix-json",
            str(matrix_risk),
            "--kind",
            "raw",
            "--out",
            str(mm / "combined_signature_risk_heatmap.png"),
        ]
    )

    run(
        [
            str(py),
            str(scripts / "plot_multimodel_nine_panel.py"),
            "--matrix-json",
            str(matrix_unsafe),
            "--out",
            str(mm / "combined_9panel_unsafe_by_category.png"),
        ]
    )
    run(
        [
            str(py),
            str(scripts / "plot_multimodel_radar_grid.py"),
            "--matrix-json",
            str(matrix_unsafe),
            "--out",
            str(mm / "combined_radar_grid_unsafe.png"),
        ]
    )

    if args.extra_visuals:
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_parallel_coordinates.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_parallel_coordinates.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_parallel_coordinates.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--color-by",
                "tier",
                "--out",
                str(mm / "combined_parallel_coordinates_by_tier.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_forest_wilson.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_forest_wilson_unsafe.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_forest_wilson.py"),
                "--matrix-json",
                str(matrix_risk),
                "--out",
                str(mm / "combined_forest_wilson_risk.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_clustermap.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_clustermap_rates.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_tier_slope_chart.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_tier_slope_overall_rates.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_label_composition.py"),
                "--root",
                str(ROOT / "results" / "multimodel"),
                "--out",
                str(mm / "combined_label_composition_stacked.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "export_multimodel_summary_table.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out-csv",
                str(mm / "summary_table_models_categories.csv"),
                "--out-png",
                str(mm / "summary_table_models_categories.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_category_correlation_across_models.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_category_correlation_across_models.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_within_category_ranks.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "combined_within_category_ranks_unsafe.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_interactive_matrix.py"),
                "--matrix-unsafe",
                str(matrix_unsafe),
                "--matrix-risk",
                str(matrix_risk),
                "--out",
                str(mm / "interactive_rates.html"),
            ]
        )

    if args.phd_visuals:
        mroot = ROOT / "results" / "multimodel"
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_mcnemar_pairwise.py"),
                "--root",
                str(mroot),
                "--out",
                str(mm / "phd_mcnemar_pairwise_unsafe.png"),
                "--metric",
                "unsafe",
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_mcnemar_pairwise.py"),
                "--root",
                str(mroot),
                "--out",
                str(mm / "phd_mcnemar_pairwise_risk.png"),
                "--metric",
                "risk",
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_beta_posterior_facets.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "phd_beta_posterior_unsafe_facets.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_interaction_tier_provider.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "phd_tier_provider_interaction_unsafe.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_unsafe_concordance.py"),
                "--root",
                str(mroot),
                "--out",
                str(mm / "phd_unsafe_concordance_histogram.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_cohens_h_pairwise.py"),
                "--root",
                str(mroot),
                "--out",
                str(mm / "phd_cohens_h_pairwise_overall.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_unsafe_incidence_heatmap.py"),
                "--root",
                str(mroot),
                "--out",
                str(mm / "phd_unsafe_incidence_prompts_by_run.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_logit_category_profile.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "phd_logit_category_profiles_unsafe.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_multimodel_direct_vs_roleplay_escalation.py"),
                "--matrix-json",
                str(matrix_unsafe),
                "--out",
                str(mm / "phd_direct_vs_roleplay_escalation.png"),
            ]
        )

    if not args.skip_fingerprints:
        run([str(py), str(scripts / "fingerprint_all_multimodel.py")])
        run(
            [
                str(py),
                str(scripts / "plot_safety_frontier.py"),
                "--root",
                str(ROOT / "results" / "multimodel"),
                "--hull",
                "--line",
                "--out",
                str(mm / "combined_safety_frontier.png"),
            ]
        )
        run(
            [
                str(py),
                str(scripts / "plot_fingerprint_pca.py"),
                "--root",
                str(ROOT / "results" / "multimodel"),
                "--out",
                str(mm / "combined_fingerprint_pca.png"),
                "--meta-out",
                str(mm / "combined_fingerprint_pca_meta.json"),
            ]
        )

    print("Done. Key multimodel outputs under figures/multimodel/", file=sys.stderr)


if __name__ == "__main__":
    main()
