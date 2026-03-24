"""
GSE208629 scRNA-seq Analysis: Actin Pathway in SMA Motor Neurons
================================================================
Dataset: Mouse SMA spinal cord scRNA-seq (Smn-/- model)
- GSM6355861: SMA (13,268 cells expected)
- GSM6355862: Control (8,887 cells expected)
- 10 major cell types including neurons
- Published: PLOS Genetics 2022

Goal: Check CORO1C/actin pathway genes in SMA motor neurons,
      cross-validate with GSE287257 (ALS human) findings:
      - CORO1C not MN-specific (highest in microglia/endothelial)
      - PFN2 (7.6x) and LIMK1 (2.3x) ARE MN-enriched
      - CFL2 DOWN in ALS motor neurons
"""

import os
import sys
import json
import warnings
import numpy as np
import pandas as pd
import scanpy as sc
from scipy import stats
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')
sc.settings.verbosity = 1

# Paths
BASE_DIR = Path("/mnt/c/Users/bryza/Dropbox/Christian fischer/SMA/sma-platform")
DATA_DIR = BASE_DIR / "data" / "geo" / "GSE208629"
RESULTS_DIR = DATA_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Mouse gene names (lowercase first letter)
ACTIN_PATHWAY = ['Coro1c', 'Cfl2', 'Pfn1', 'Pls3', 'Actg1', 'Actr2', 'Abi2',
                 'Pfn2', 'Limk1', 'Limk2', 'Rock1', 'Rock2', 'Rac1', 'Arpc3']

SMA_MN_MARKERS = ['Smn1', 'Stmn2', 'Ncald', 'Uba1']

MN_MARKERS = ['Chat', 'Isl1', 'Mnx1']

CELL_TYPE_MARKERS = {
    'Motor_Neuron': ['Chat', 'Isl1', 'Mnx1', 'Slc18a3'],
    'Excitatory_Neuron': ['Slc17a6', 'Slc17a7', 'Satb2'],
    'Inhibitory_Neuron': ['Gad1', 'Gad2', 'Slc32a1'],
    'Astrocyte': ['Aqp4', 'Gfap', 'Gja1', 'Slc1a2'],
    'Oligodendrocyte': ['Mbp', 'Mog', 'Plp1', 'Olig2'],
    'OPC': ['Pdgfra', 'Cspg4', 'Vcan'],
    'Microglia': ['Cx3cr1', 'P2ry12', 'Tmem119', 'Csf1r'],
    'Endothelial': ['Pecam1', 'Flt1', 'Cldn5'],
}

ALL_GENES = list(set(ACTIN_PATHWAY + SMA_MN_MARKERS + MN_MARKERS +
                     [g for gs in CELL_TYPE_MARKERS.values() for g in gs]))


def load_samples():
    """Load SMA and Control 10x MTX files."""
    print("=== Loading Samples ===")
    adatas = []

    for condition, dirname in [('SMA', 'SMA'), ('Control', 'Con')]:
        data_path = DATA_DIR / dirname
        print(f"  Loading {condition} from {data_path}...")
        try:
            adata = sc.read_10x_mtx(str(data_path), var_names='gene_symbols',
                                     cache=False)
            adata.var_names_make_unique()
            adata.obs['condition'] = condition
            adata.obs['sample'] = dirname
            print(f"    {adata.n_obs} cells, {adata.n_vars} genes")
            adatas.append(adata)
        except Exception as e:
            print(f"    FAILED: {e}")
            # Try gene_ids if gene_symbols fails
            try:
                adata = sc.read_10x_mtx(str(data_path), var_names='gene_ids',
                                         cache=False)
                adata.var_names_make_unique()
                adata.obs['condition'] = condition
                adata.obs['sample'] = dirname
                print(f"    Loaded with gene_ids: {adata.n_obs} cells, {adata.n_vars} genes")
                adatas.append(adata)
            except Exception as e2:
                print(f"    Also failed with gene_ids: {e2}")

    if not adatas:
        print("ERROR: No samples loaded!")
        sys.exit(1)

    adata = sc.concat(adatas, join='outer', label='batch',
                      keys=[a.obs['sample'].iloc[0] for a in adatas])
    print(f"\nCombined: {adata.n_obs} cells x {adata.n_vars} genes")
    print(f"  SMA cells: {(adata.obs['condition'] == 'SMA').sum()}")
    print(f"  Control cells: {(adata.obs['condition'] == 'Control').sum()}")
    return adata


def qc_filter(adata):
    """Run QC and filter cells/genes."""
    print("\n=== Quality Control ===")

    # Mouse mitochondrial genes start with 'mt-'
    adata.var['mt'] = adata.var_names.str.startswith('mt-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None,
                               log1p=False, inplace=True)

    n_before = adata.n_obs
    sc.pp.filter_cells(adata, min_genes=200)
    sc.pp.filter_genes(adata, min_cells=3)
    adata = adata[adata.obs.pct_counts_mt < 20, :].copy()
    n_after = adata.n_obs

    print(f"  Before QC: {n_before} cells")
    print(f"  After QC:  {n_after} cells (removed {n_before - n_after})")
    print(f"  Genes: {adata.n_vars}")
    print(f"  Median genes/cell: {adata.obs.n_genes_by_counts.median():.0f}")
    print(f"  Median counts/cell: {adata.obs.total_counts.median():.0f}")
    print(f"  Median MT%: {adata.obs.pct_counts_mt.median():.1f}%")

    return adata


def preprocess(adata):
    """Normalize, HVGs, PCA, UMAP, leiden."""
    print("\n=== Preprocessing ===")

    adata.raw = adata

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    sc.pp.highly_variable_genes(adata, n_top_genes=3000)
    print(f"  HVGs: {adata.var.highly_variable.sum()}")

    found_genes = [g for g in ALL_GENES if g in adata.var_names]
    missing_genes = [g for g in ALL_GENES if g not in adata.var_names]
    print(f"  Target genes found: {len(found_genes)}/{len(ALL_GENES)}")
    if missing_genes:
        print(f"  Missing: {missing_genes}")

    adata_hvg = adata[:, adata.var.highly_variable].copy()
    sc.pp.scale(adata_hvg, max_value=10)
    sc.tl.pca(adata_hvg, n_comps=50)
    adata.obsm['X_pca'] = adata_hvg.obsm['X_pca']

    sc.pp.neighbors(adata, n_neighbors=15, n_pcs=30)
    sc.tl.umap(adata)

    sc.tl.leiden(adata, resolution=0.8)
    n_clusters = adata.obs['leiden'].nunique()
    print(f"  Leiden clusters: {n_clusters}")

    return adata


def identify_cell_types(adata):
    """Score and annotate cell types based on marker genes."""
    print("\n=== Cell Type Identification ===")

    for ct, markers in CELL_TYPE_MARKERS.items():
        available = [g for g in markers if g in adata.var_names]
        if available:
            sc.tl.score_genes(adata, gene_list=available, score_name=f'{ct}_score')
            print(f"  {ct}: scored with {len(available)}/{len(markers)} markers ({available})")
        else:
            adata.obs[f'{ct}_score'] = 0
            print(f"  {ct}: NO markers found in data")

    score_cols = [f'{ct}_score' for ct in CELL_TYPE_MARKERS.keys()]
    score_df = adata.obs[score_cols]
    adata.obs['cell_type'] = score_df.idxmax(axis=1).str.replace('_score', '')

    mn_score = adata.obs['Motor_Neuron_score']
    mn_threshold = mn_score.quantile(0.95)
    adata.obs['is_motor_neuron'] = mn_score > mn_threshold

    print(f"\n  Cell type distribution:")
    for ct in CELL_TYPE_MARKERS.keys():
        n = (adata.obs['cell_type'] == ct).sum()
        print(f"    {ct}: {n} cells ({100*n/adata.n_obs:.1f}%)")

    n_mn = adata.obs['is_motor_neuron'].sum()
    print(f"\n  Motor neurons (top 5% MN score): {n_mn} cells ({100*n_mn/adata.n_obs:.1f}%)")

    return adata


def get_gene_expr(adata, gene):
    """Get expression vector for a gene, trying both raw and normalized."""
    use_raw = adata.raw is not None

    if use_raw and gene in adata.raw.var_names:
        x = adata.raw[:, gene].X
        if hasattr(x, 'todense'):
            return np.array(x.todense()).flatten()
        return np.array(x).flatten()
    elif gene in adata.var_names:
        x = adata[:, gene].X
        if hasattr(x, 'todense'):
            return np.array(x.todense()).flatten()
        return np.array(x).flatten()
    else:
        return None


def compare_groups(expr, mask_a, mask_b):
    """Compare expression between two groups. Returns mean_a, mean_b, pct_a, pct_b, log2fc, pval."""
    a = expr[mask_a]
    b = expr[mask_b]
    mean_a = float(np.mean(a))
    mean_b = float(np.mean(b))
    pct_a = float(np.mean(a > 0) * 100)
    pct_b = float(np.mean(b > 0) * 100)

    if pct_a > 0 and pct_b > 0 and len(a) > 2 and len(b) > 2:
        stat, pval = stats.mannwhitneyu(a, b, alternative='two-sided')
    else:
        stat, pval = 0, 1.0

    log2fc = np.log2((mean_a + 0.01) / (mean_b + 0.01))
    return mean_a, mean_b, pct_a, pct_b, log2fc, float(pval)


def sig_label(pval):
    if pval < 0.001:
        return "***"
    elif pval < 0.01:
        return "**"
    elif pval < 0.05:
        return "*"
    return ""


def analyze_expression(adata):
    """Full expression analysis."""
    print("\n=== Expression Analysis ===")

    is_mn = adata.obs['is_motor_neuron'].values
    is_sma = adata.obs['condition'].values == 'SMA'
    is_ctrl = adata.obs['condition'].values == 'Control'
    sma_mn = is_sma & is_mn
    ctrl_mn = is_ctrl & is_mn

    results = {
        'metadata': {
            'dataset': 'GSE208629',
            'description': 'Mouse SMA spinal cord scRNA-seq (Smn-/- model)',
            'species': 'Mus musculus',
            'n_cells_total': int(adata.n_obs),
            'n_cells_sma': int(is_sma.sum()),
            'n_cells_control': int(is_ctrl.sum()),
            'n_genes': int(adata.n_vars),
            'n_motor_neurons': int(is_mn.sum()),
            'n_sma_motor_neurons': int(sma_mn.sum()),
            'n_ctrl_motor_neurons': int(ctrl_mn.sum()),
            'n_clusters': int(adata.obs['leiden'].nunique()),
            'analysis_date': datetime.now().isoformat(),
        },
        'cell_type_distribution': {},
        'actin_pathway_mn_vs_other': {},
        'actin_pathway_sma_vs_control_all': {},
        'actin_pathway_sma_mn_vs_ctrl_mn': {},
        'sma_markers': {},
        'coro1c_by_cell_type': {},
        'coro1c_by_cluster': {},
        'cross_species_comparison': {},
    }

    # Cell type distribution
    for ct in CELL_TYPE_MARKERS.keys():
        n = int((adata.obs['cell_type'] == ct).sum())
        results['cell_type_distribution'][ct] = {
            'n_cells': n,
            'pct': round(100 * n / adata.n_obs, 2)
        }

    # ============================================================
    # 1) Motor Neurons vs Others — key question: is Coro1c MN-enriched?
    # ============================================================
    print("\n--- Actin pathway: Motor Neurons vs Other Cells ---")
    print(f"{'Gene':<10} {'MN_mean':>10} {'Other_mean':>10} {'MN_pct':>8} {'Other_pct':>8} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
    print("-" * 80)

    for gene in ACTIN_PATHWAY:
        expr = get_gene_expr(adata, gene)
        if expr is None:
            print(f"{gene:<10} NOT FOUND IN DATA")
            results['actin_pathway_mn_vs_other'][gene] = {'status': 'not_found'}
            continue

        mn_mean, other_mean, mn_pct, other_pct, log2fc, pval = compare_groups(expr, is_mn, ~is_mn)
        sig = sig_label(pval)
        print(f"{gene:<10} {mn_mean:>10.4f} {other_mean:>10.4f} {mn_pct:>7.1f}% {other_pct:>7.1f}% {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

        results['actin_pathway_mn_vs_other'][gene] = {
            'mn_mean': round(mn_mean, 6),
            'other_mean': round(other_mean, 6),
            'mn_pct_expressing': round(mn_pct, 2),
            'other_pct_expressing': round(other_pct, 2),
            'log2fc_mn_vs_other': round(log2fc, 4),
            'pvalue': float(pval),
            'significant': pval < 0.05,
        }

    # ============================================================
    # 2) SMA vs Control (ALL cells)
    # ============================================================
    print("\n--- Actin pathway: SMA vs Control (all cells) ---")
    print(f"{'Gene':<10} {'SMA_mean':>10} {'Ctrl_mean':>10} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
    print("-" * 65)

    for gene in ACTIN_PATHWAY:
        expr = get_gene_expr(adata, gene)
        if expr is None:
            results['actin_pathway_sma_vs_control_all'][gene] = {'status': 'not_found'}
            continue

        sma_mean, ctrl_mean, sma_pct, ctrl_pct, log2fc, pval = compare_groups(expr, is_sma, is_ctrl)
        sig = sig_label(pval)
        print(f"{gene:<10} {sma_mean:>10.4f} {ctrl_mean:>10.4f} {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

        results['actin_pathway_sma_vs_control_all'][gene] = {
            'sma_mean': round(sma_mean, 6),
            'ctrl_mean': round(ctrl_mean, 6),
            'sma_pct': round(sma_pct, 2),
            'ctrl_pct': round(ctrl_pct, 2),
            'log2fc_sma_vs_ctrl': round(log2fc, 4),
            'pvalue': float(pval),
            'significant': pval < 0.05,
        }

    # ============================================================
    # 3) SMA Motor Neurons vs Control Motor Neurons — THE KEY COMPARISON
    # ============================================================
    print(f"\n--- Actin pathway: SMA Motor Neurons vs Control Motor Neurons ---")
    n_sma_mn = int(sma_mn.sum())
    n_ctrl_mn = int(ctrl_mn.sum())
    print(f"SMA motor neurons: {n_sma_mn}, Control motor neurons: {n_ctrl_mn}")

    if n_sma_mn >= 5 and n_ctrl_mn >= 5:
        print(f"{'Gene':<10} {'SMA_MN':>10} {'Ctrl_MN':>10} {'SMA_pct':>8} {'Ctrl_pct':>8} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
        print("-" * 80)

        for gene in ACTIN_PATHWAY:
            expr = get_gene_expr(adata, gene)
            if expr is None:
                results['actin_pathway_sma_mn_vs_ctrl_mn'][gene] = {'status': 'not_found'}
                continue

            sma_mn_mean, ctrl_mn_mean, sma_pct, ctrl_pct, log2fc, pval = compare_groups(expr, sma_mn, ctrl_mn)
            sig = sig_label(pval)
            print(f"{gene:<10} {sma_mn_mean:>10.4f} {ctrl_mn_mean:>10.4f} {sma_pct:>7.1f}% {ctrl_pct:>7.1f}% {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

            results['actin_pathway_sma_mn_vs_ctrl_mn'][gene] = {
                'sma_mn_mean': round(sma_mn_mean, 6),
                'ctrl_mn_mean': round(ctrl_mn_mean, 6),
                'sma_mn_pct': round(sma_pct, 2),
                'ctrl_mn_pct': round(ctrl_pct, 2),
                'log2fc': round(log2fc, 4),
                'pvalue': float(pval),
                'significant': pval < 0.05,
            }
    else:
        print("  WARNING: Too few motor neurons for SMA vs Control MN comparison")
        print("  Trying relaxed threshold (top 10% MN score)...")

        mn_score = adata.obs['Motor_Neuron_score']
        mn_threshold_relaxed = mn_score.quantile(0.90)
        is_mn_relaxed = mn_score > mn_threshold_relaxed
        sma_mn_r = is_sma & is_mn_relaxed.values
        ctrl_mn_r = is_ctrl & is_mn_relaxed.values
        n_sma_mn_r = int(sma_mn_r.sum())
        n_ctrl_mn_r = int(ctrl_mn_r.sum())
        print(f"  Relaxed: SMA MNs={n_sma_mn_r}, Control MNs={n_ctrl_mn_r}")

        if n_sma_mn_r >= 5 and n_ctrl_mn_r >= 5:
            results['metadata']['mn_threshold'] = 'top_10pct'
            results['metadata']['n_sma_motor_neurons_relaxed'] = n_sma_mn_r
            results['metadata']['n_ctrl_motor_neurons_relaxed'] = n_ctrl_mn_r

            print(f"{'Gene':<10} {'SMA_MN':>10} {'Ctrl_MN':>10} {'SMA_pct':>8} {'Ctrl_pct':>8} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
            print("-" * 80)

            for gene in ACTIN_PATHWAY:
                expr = get_gene_expr(adata, gene)
                if expr is None:
                    results['actin_pathway_sma_mn_vs_ctrl_mn'][gene] = {'status': 'not_found'}
                    continue

                sma_mn_mean, ctrl_mn_mean, sma_pct, ctrl_pct, log2fc, pval = compare_groups(expr, sma_mn_r, ctrl_mn_r)
                sig = sig_label(pval)
                print(f"{gene:<10} {sma_mn_mean:>10.4f} {ctrl_mn_mean:>10.4f} {sma_pct:>7.1f}% {ctrl_pct:>7.1f}% {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

                results['actin_pathway_sma_mn_vs_ctrl_mn'][gene] = {
                    'sma_mn_mean': round(sma_mn_mean, 6),
                    'ctrl_mn_mean': round(ctrl_mn_mean, 6),
                    'sma_mn_pct': round(sma_pct, 2),
                    'ctrl_mn_pct': round(ctrl_pct, 2),
                    'log2fc': round(log2fc, 4),
                    'pvalue': float(pval),
                    'significant': pval < 0.05,
                    'note': 'relaxed_threshold_top10pct',
                }

    # ============================================================
    # 4) SMA/MN Markers
    # ============================================================
    print("\n--- SMA/MN Marker Expression ---")
    all_markers = SMA_MN_MARKERS + MN_MARKERS
    for gene in all_markers:
        expr = get_gene_expr(adata, gene)
        if expr is None:
            print(f"  {gene}: NOT FOUND")
            results['sma_markers'][gene] = {'status': 'not_found'}
            continue

        overall_mean = float(np.mean(expr))
        overall_pct = float(np.mean(expr > 0) * 100)
        mn_expr_vals = expr[is_mn]
        mn_mean = float(np.mean(mn_expr_vals))
        mn_pct = float(np.mean(mn_expr_vals > 0) * 100)

        # SMA vs Control for this marker
        sma_expr = expr[is_sma]
        ctrl_expr = expr[is_ctrl]
        sma_mean_v = float(np.mean(sma_expr))
        ctrl_mean_v = float(np.mean(ctrl_expr))

        print(f"  {gene}: overall={overall_mean:.4f} ({overall_pct:.1f}%), "
              f"MN={mn_mean:.4f} ({mn_pct:.1f}%), "
              f"SMA={sma_mean_v:.4f}, Ctrl={ctrl_mean_v:.4f}")

        results['sma_markers'][gene] = {
            'overall_mean': round(overall_mean, 6),
            'overall_pct': round(overall_pct, 2),
            'mn_mean': round(mn_mean, 6),
            'mn_pct': round(mn_pct, 2),
            'sma_mean': round(sma_mean_v, 6),
            'ctrl_mean': round(ctrl_mean_v, 6),
        }

    # ============================================================
    # 5) Coro1c expression by cell type
    # ============================================================
    print("\n--- Coro1c Expression by Cell Type ---")
    coro1c_expr = get_gene_expr(adata, 'Coro1c')
    if coro1c_expr is not None:
        for ct in sorted(adata.obs['cell_type'].unique()):
            mask = adata.obs['cell_type'].values == ct
            ct_expr = coro1c_expr[mask]
            ct_mean = float(np.mean(ct_expr))
            ct_pct = float(np.mean(ct_expr > 0) * 100)
            n_cells = int(mask.sum())
            print(f"  {ct}: mean={ct_mean:.4f}, {ct_pct:.1f}% expressing, n={n_cells}")
            results['coro1c_by_cell_type'][ct] = {
                'mean': round(ct_mean, 6),
                'pct_expressing': round(ct_pct, 2),
                'n_cells': n_cells,
            }
    else:
        print("  Coro1c NOT FOUND in data")

    # ============================================================
    # 6) Coro1c expression by cluster
    # ============================================================
    print("\n--- Coro1c Expression by Cluster ---")
    if coro1c_expr is not None:
        for cl in sorted(adata.obs['leiden'].unique(), key=lambda x: int(x)):
            mask = adata.obs['leiden'].values == cl
            cl_expr = coro1c_expr[mask]
            cl_mean = float(np.mean(cl_expr))
            cl_pct = float(np.mean(cl_expr > 0) * 100)
            n_cells = int(mask.sum())
            mn_frac = float(is_mn[mask].mean() * 100)
            print(f"  Cluster {cl}: mean={cl_mean:.4f}, {cl_pct:.1f}% expressing, n={n_cells}, MN%={mn_frac:.1f}%")
            results['coro1c_by_cluster'][f'cluster_{cl}'] = {
                'mean': round(cl_mean, 6),
                'pct_expressing': round(cl_pct, 2),
                'n_cells': n_cells,
                'mn_fraction_pct': round(mn_frac, 2),
            }

    # ============================================================
    # 7) Cross-species comparison summary
    # ============================================================
    print("\n--- Cross-Species Comparison (Mouse SMA vs Human ALS) ---")
    key_genes = ['Coro1c', 'Pfn2', 'Limk1', 'Cfl2', 'Pls3', 'Rock1', 'Rock2']
    for gene in key_genes:
        data = results['actin_pathway_mn_vs_other'].get(gene, {})
        if data and data.get('status') != 'not_found':
            enriched = "MN-enriched" if data['log2fc_mn_vs_other'] > 0.5 else \
                       "MN-depleted" if data['log2fc_mn_vs_other'] < -0.5 else "similar"
            print(f"  {gene}: log2FC(MN/other)={data['log2fc_mn_vs_other']:.3f} ({enriched}), p={data['pvalue']:.2e}")

            sma_data = results['actin_pathway_sma_mn_vs_ctrl_mn'].get(gene, {})
            if sma_data and sma_data.get('status') != 'not_found':
                direction = "UP in SMA" if sma_data['log2fc'] > 0.2 else \
                            "DOWN in SMA" if sma_data['log2fc'] < -0.2 else "unchanged"
                print(f"    SMA MN vs Ctrl MN: log2FC={sma_data['log2fc']:.3f} ({direction}), p={sma_data['pvalue']:.2e}")

            results['cross_species_comparison'][gene] = {
                'mn_enrichment_log2fc': data['log2fc_mn_vs_other'],
                'mn_enrichment_pval': data['pvalue'],
                'mn_enrichment_label': enriched,
            }
            if sma_data and sma_data.get('status') != 'not_found':
                results['cross_species_comparison'][gene].update({
                    'sma_vs_ctrl_mn_log2fc': sma_data['log2fc'],
                    'sma_vs_ctrl_mn_pval': sma_data['pvalue'],
                })

    return results


def main():
    print("=" * 70)
    print("GSE208629 scRNA-seq Analysis: Actin Pathway in SMA Motor Neurons")
    print("=" * 70)

    adata = load_samples()
    adata = qc_filter(adata)
    adata = preprocess(adata)
    adata = identify_cell_types(adata)
    results = analyze_expression(adata)

    # Save results JSON
    results_file = RESULTS_DIR / "gse208629_analysis_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 70)
    print("SUMMARY — Key Findings")
    print("=" * 70)

    m = results['metadata']
    print(f"\nDataset: {m['dataset']} ({m['description']})")
    print(f"Total cells: {m['n_cells_total']} (SMA: {m['n_cells_sma']}, Control: {m['n_cells_control']})")
    print(f"Motor neurons: {m['n_motor_neurons']} (SMA: {m['n_sma_motor_neurons']}, Control: {m['n_ctrl_motor_neurons']})")

    print("\n--- Question 1: Is Coro1c MN-enriched in mouse? ---")
    coro1c = results['actin_pathway_mn_vs_other'].get('Coro1c', {})
    if coro1c and coro1c.get('status') != 'not_found':
        print(f"  MN mean: {coro1c['mn_mean']:.4f} ({coro1c['mn_pct_expressing']:.1f}% expressing)")
        print(f"  Other mean: {coro1c['other_mean']:.4f} ({coro1c['other_pct_expressing']:.1f}% expressing)")
        print(f"  log2FC(MN/other): {coro1c['log2fc_mn_vs_other']:.3f}")
        print(f"  p-value: {coro1c['pvalue']:.2e}")
        if coro1c['log2fc_mn_vs_other'] < 0:
            print("  => CONFIRMS: Coro1c is NOT motor neuron-specific in mouse (consistent with human ALS)")
        else:
            print("  => DIFFERENT: Coro1c IS MN-enriched in mouse (different from human ALS)")
    else:
        print("  Coro1c not found in data")

    print("\n--- Question 2: Is Pfn2 MN-enriched in mouse? ---")
    pfn2 = results['actin_pathway_mn_vs_other'].get('Pfn2', {})
    if pfn2 and pfn2.get('status') != 'not_found':
        print(f"  log2FC(MN/other): {pfn2['log2fc_mn_vs_other']:.3f}, p={pfn2['pvalue']:.2e}")
        if pfn2['log2fc_mn_vs_other'] > 0.5:
            print("  => CROSS-SPECIES VALIDATED: Pfn2 is MN-enriched in both mouse and human")

    print("\n--- Question 3: Is Limk1 MN-enriched in mouse? ---")
    limk1 = results['actin_pathway_mn_vs_other'].get('Limk1', {})
    if limk1 and limk1.get('status') != 'not_found':
        print(f"  log2FC(MN/other): {limk1['log2fc_mn_vs_other']:.3f}, p={limk1['pvalue']:.2e}")

    print("\n--- Question 4: Actin genes in SMA MNs vs Control MNs ---")
    for gene in ACTIN_PATHWAY:
        data = results['actin_pathway_sma_mn_vs_ctrl_mn'].get(gene, {})
        if data and data.get('status') != 'not_found':
            sig = sig_label(data['pvalue'])
            direction = "UP" if data['log2fc'] > 0 else "DOWN"
            print(f"  {gene}: log2FC={data['log2fc']:.3f} ({direction} in SMA), p={data['pvalue']:.2e} {sig}")

    print("\n--- Question 5: Cfl2 in SMA MNs (opposite from ALS?) ---")
    cfl2 = results['actin_pathway_sma_mn_vs_ctrl_mn'].get('Cfl2', {})
    if cfl2 and cfl2.get('status') != 'not_found':
        print(f"  log2FC(SMA_MN/Ctrl_MN): {cfl2['log2fc']:.3f}, p={cfl2['pvalue']:.2e}")
        if cfl2['log2fc'] > 0:
            print("  => CFL2 UP in SMA motor neurons (OPPOSITE from ALS where CFL2 is DOWN)")
            print("  => This confirms DISEASE-SPECIFIC actin pathway dysregulation!")
        else:
            print("  => CFL2 DOWN in SMA motor neurons (SAME direction as ALS)")

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
