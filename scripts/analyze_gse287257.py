"""
GSE287257 snRNA-seq Analysis: CORO1C in ALS Motor Neurons
=========================================================
Dataset: 8 ALS + 4 control, human postmortem cervical spinal cord
Format: 10x Genomics filtered_feature_bc_matrix.h5
Goal: Validate CORO1C upregulation in ALS at single-cell resolution,
      specifically in motor neurons vs other cell types.
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
DATA_DIR = BASE_DIR / "data" / "geo" / "GSE287257"
RESULTS_DIR = DATA_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Gene lists
ACTIN_PATHWAY = ['CORO1C', 'CFL2', 'PFN1', 'PLS3', 'ACTG1', 'ACTR2', 'ABI2',
                 'PFN2', 'LIMK1', 'LIMK2', 'ROCK1', 'ROCK2', 'RAC1', 'ARPC3']

SMA_MN_MARKERS = ['SMN1', 'SMN2', 'STMN2', 'NCALD', 'UBA1',
                  'CHAT', 'ISL1', 'MNX1']

MN_MARKERS = ['CHAT', 'ISL1', 'MNX1']
CELL_TYPE_MARKERS = {
    'Motor_Neuron': ['CHAT', 'ISL1', 'MNX1', 'SLC18A3'],
    'Excitatory_Neuron': ['SLC17A6', 'SLC17A7', 'SATB2'],
    'Inhibitory_Neuron': ['GAD1', 'GAD2', 'SLC32A1'],
    'Astrocyte': ['AQP4', 'GFAP', 'GJA1', 'SLC1A2'],
    'Oligodendrocyte': ['MBP', 'MOG', 'PLP1', 'OLIG2'],
    'OPC': ['PDGFRA', 'CSPG4', 'VCAN'],
    'Microglia': ['CX3CR1', 'P2RY12', 'TMEM119', 'CSF1R'],
    'Endothelial': ['PECAM1', 'FLT1', 'CLDN5'],
}

ALL_GENES = list(set(ACTIN_PATHWAY + SMA_MN_MARKERS +
                     [g for gs in CELL_TYPE_MARKERS.values() for g in gs]))


def load_samples():
    """Load all .h5 files and concatenate into single AnnData."""
    h5_files = sorted(DATA_DIR.glob("*.h5"))
    print(f"Found {len(h5_files)} .h5 files")

    adatas = []
    for f in h5_files:
        name = f.stem
        parts = name.split('_')
        gsm = parts[0]
        sample_id = parts[1]
        condition = 'ALS' if 'ALS' in name else 'Control'

        print(f"  Loading {gsm} ({sample_id}, {condition})...", end=" ")
        try:
            adata = sc.read_10x_h5(str(f))
            adata.var_names_make_unique()
            adata.obs['sample'] = f"{gsm}_{sample_id}"
            adata.obs['condition'] = condition
            adata.obs['gsm'] = gsm
            print(f"{adata.n_obs} cells, {adata.n_vars} genes")
            adatas.append(adata)
        except Exception as e:
            print(f"FAILED: {e}")
            continue

    if not adatas:
        print("ERROR: No samples loaded!")
        sys.exit(1)

    adata = sc.concat(adatas, join='outer', label='batch',
                      keys=[a.obs['sample'].iloc[0] for a in adatas])
    print(f"\nCombined: {adata.n_obs} cells x {adata.n_vars} genes")
    return adata


def qc_filter(adata):
    """Run QC and filter cells/genes."""
    print("\n=== Quality Control ===")

    adata.var['mt'] = adata.var_names.str.startswith('MT-')
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
    """Normalize, find HVGs, PCA, neighbors, UMAP, leiden."""
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
        ct_clean = ct
        n = (adata.obs['cell_type'] == ct_clean).sum()
        print(f"    {ct_clean}: {n} cells ({100*n/adata.n_obs:.1f}%)")

    n_mn = adata.obs['is_motor_neuron'].sum()
    print(f"\n  Motor neurons (top 5% MN score): {n_mn} cells ({100*n_mn/adata.n_obs:.1f}%)")

    return adata


def analyze_expression(adata):
    """Compare gene expression between motor neurons and other cells, ALS vs Control."""
    print("\n=== Expression Analysis ===")
    results = {
        'metadata': {
            'dataset': 'GSE287257',
            'description': 'ALS snRNA-seq, human cervical spinal cord',
            'n_samples_als': int((adata.obs.groupby('sample')['condition'].first() == 'ALS').sum()),
            'n_samples_control': int((adata.obs.groupby('sample')['condition'].first() == 'Control').sum()),
            'n_cells_total': int(adata.n_obs),
            'n_genes': int(adata.n_vars),
            'n_motor_neurons': int(adata.obs['is_motor_neuron'].sum()),
            'n_clusters': int(adata.obs['leiden'].nunique()),
            'analysis_date': datetime.now().isoformat(),
        },
        'cell_type_distribution': {},
        'actin_pathway_mn_vs_other': {},
        'actin_pathway_als_vs_control': {},
        'actin_pathway_als_mn_specific': {},
        'sma_mn_markers': {},
    }

    for ct in CELL_TYPE_MARKERS.keys():
        n = int((adata.obs['cell_type'] == ct).sum())
        results['cell_type_distribution'][ct] = {
            'n_cells': n,
            'pct': round(100 * n / adata.n_obs, 2)
        }

    use_raw = adata.raw is not None

    def get_gene_expr(gene, subset=None):
        if gene not in adata.var_names:
            if use_raw and gene in adata.raw.var_names:
                pass
            else:
                return None
        if use_raw and gene in adata.raw.var_names:
            if subset is not None:
                return np.array(adata.raw[subset, gene].X.todense()).flatten()
            return np.array(adata.raw[:, gene].X.todense()).flatten()
        else:
            if subset is not None:
                x = adata[subset, gene].X
            else:
                x = adata[:, gene].X
            if hasattr(x, 'todense'):
                return np.array(x.todense()).flatten()
            return np.array(x).flatten()

    is_mn = adata.obs['is_motor_neuron'].values
    is_als = adata.obs['condition'].values == 'ALS'
    is_ctrl = adata.obs['condition'].values == 'Control'

    # 1) Motor neurons vs others
    print("\n--- Actin pathway: Motor Neurons vs Other Cells ---")
    print(f"{'Gene':<10} {'MN_mean':>10} {'Other_mean':>10} {'MN_pct':>8} {'Other_pct':>8} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
    print("-" * 80)

    for gene in ACTIN_PATHWAY:
        expr = get_gene_expr(gene)
        if expr is None:
            print(f"{gene:<10} NOT FOUND IN DATA")
            results['actin_pathway_mn_vs_other'][gene] = {'status': 'not_found'}
            continue

        mn_expr = expr[is_mn]
        other_expr = expr[~is_mn]
        mn_mean = float(np.mean(mn_expr))
        other_mean = float(np.mean(other_expr))
        mn_pct = float(np.mean(mn_expr > 0) * 100)
        other_pct = float(np.mean(other_expr > 0) * 100)

        if mn_pct > 0 and other_pct > 0:
            stat, pval = stats.mannwhitneyu(mn_expr, other_expr, alternative='two-sided')
        else:
            stat, pval = 0, 1.0

        log2fc = np.log2((mn_mean + 0.01) / (other_mean + 0.01))
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

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

    # 2) ALS vs Control (all cells)
    print("\n--- Actin pathway: ALS vs Control (all cells) ---")
    print(f"{'Gene':<10} {'ALS_mean':>10} {'Ctrl_mean':>10} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
    print("-" * 65)

    for gene in ACTIN_PATHWAY:
        expr = get_gene_expr(gene)
        if expr is None:
            results['actin_pathway_als_vs_control'][gene] = {'status': 'not_found'}
            continue

        als_expr = expr[is_als]
        ctrl_expr = expr[is_ctrl]
        als_mean = float(np.mean(als_expr))
        ctrl_mean = float(np.mean(ctrl_expr))

        if np.mean(als_expr > 0) > 0 and np.mean(ctrl_expr > 0) > 0:
            stat, pval = stats.mannwhitneyu(als_expr, ctrl_expr, alternative='two-sided')
        else:
            stat, pval = 0, 1.0

        log2fc = np.log2((als_mean + 0.01) / (ctrl_mean + 0.01))
        sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

        print(f"{gene:<10} {als_mean:>10.4f} {ctrl_mean:>10.4f} {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

        results['actin_pathway_als_vs_control'][gene] = {
            'als_mean': round(als_mean, 6),
            'ctrl_mean': round(ctrl_mean, 6),
            'log2fc_als_vs_ctrl': round(log2fc, 4),
            'pvalue': float(pval),
            'significant': pval < 0.05,
        }

    # 3) ALS MN vs Control MN
    print("\n--- Actin pathway: ALS Motor Neurons vs Control Motor Neurons ---")
    als_mn = is_als & is_mn
    ctrl_mn = is_ctrl & is_mn
    n_als_mn = int(als_mn.sum())
    n_ctrl_mn = int(ctrl_mn.sum())
    print(f"ALS motor neurons: {n_als_mn}, Control motor neurons: {n_ctrl_mn}")
    results['metadata']['n_als_motor_neurons'] = n_als_mn
    results['metadata']['n_ctrl_motor_neurons'] = n_ctrl_mn

    if n_als_mn > 5 and n_ctrl_mn > 5:
        print(f"{'Gene':<10} {'ALS_MN':>10} {'Ctrl_MN':>10} {'log2FC':>8} {'p-value':>12} {'Sig':>4}")
        print("-" * 65)

        for gene in ACTIN_PATHWAY:
            expr = get_gene_expr(gene)
            if expr is None:
                results['actin_pathway_als_mn_specific'][gene] = {'status': 'not_found'}
                continue

            als_mn_expr = expr[als_mn]
            ctrl_mn_expr = expr[ctrl_mn]
            als_mn_mean = float(np.mean(als_mn_expr))
            ctrl_mn_mean = float(np.mean(ctrl_mn_expr))

            if np.mean(als_mn_expr > 0) > 0 and np.mean(ctrl_mn_expr > 0) > 0:
                stat, pval = stats.mannwhitneyu(als_mn_expr, ctrl_mn_expr, alternative='two-sided')
            else:
                stat, pval = 0, 1.0

            log2fc = np.log2((als_mn_mean + 0.01) / (ctrl_mn_mean + 0.01))
            sig = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else ""

            print(f"{gene:<10} {als_mn_mean:>10.4f} {ctrl_mn_mean:>10.4f} {log2fc:>8.3f} {pval:>12.2e} {sig:>4}")

            results['actin_pathway_als_mn_specific'][gene] = {
                'als_mn_mean': round(als_mn_mean, 6),
                'ctrl_mn_mean': round(ctrl_mn_mean, 6),
                'log2fc': round(log2fc, 4),
                'pvalue': float(pval),
                'significant': pval < 0.05,
            }
    else:
        print("  WARNING: Too few motor neurons for ALS vs Control comparison")

    # 4) SMA/MN markers
    print("\n--- SMA/MN Marker Expression ---")
    for gene in SMA_MN_MARKERS:
        expr = get_gene_expr(gene)
        if expr is None:
            print(f"  {gene}: NOT FOUND")
            results['sma_mn_markers'][gene] = {'status': 'not_found'}
            continue

        overall_mean = float(np.mean(expr))
        overall_pct = float(np.mean(expr > 0) * 100)
        mn_expr_vals = expr[is_mn]
        mn_mean = float(np.mean(mn_expr_vals))
        mn_pct = float(np.mean(mn_expr_vals > 0) * 100)

        print(f"  {gene}: overall={overall_mean:.4f} ({overall_pct:.1f}%), MN={mn_mean:.4f} ({mn_pct:.1f}%)")

        results['sma_mn_markers'][gene] = {
            'overall_mean': round(overall_mean, 6),
            'overall_pct': round(overall_pct, 2),
            'mn_mean': round(mn_mean, 6),
            'mn_pct': round(mn_pct, 2),
        }

    # 5) CORO1C per cluster
    print("\n--- CORO1C Expression by Cluster ---")
    coro1c_expr = get_gene_expr('CORO1C')
    if coro1c_expr is not None:
        cluster_data = {}
        for cl in sorted(adata.obs['leiden'].unique(), key=int):
            mask = adata.obs['leiden'].values == cl
            cl_expr = coro1c_expr[mask]
            cl_mean = float(np.mean(cl_expr))
            cl_pct = float(np.mean(cl_expr > 0) * 100)
            n_cells = int(mask.sum())
            mn_frac = float(is_mn[mask].mean() * 100)
            print(f"  Cluster {cl}: mean={cl_mean:.4f}, {cl_pct:.1f}% expressing, n={n_cells}, MN%={mn_frac:.1f}%")
            cluster_data[f'cluster_{cl}'] = {
                'mean': round(cl_mean, 6),
                'pct_expressing': round(cl_pct, 2),
                'n_cells': n_cells,
                'mn_fraction_pct': round(mn_frac, 2),
            }
        results['coro1c_by_cluster'] = cluster_data

    # 6) CORO1C per cell type
    print("\n--- CORO1C Expression by Cell Type ---")
    if coro1c_expr is not None:
        ct_data = {}
        for ct in sorted(adata.obs['cell_type'].unique()):
            mask = adata.obs['cell_type'].values == ct
            ct_expr = coro1c_expr[mask]
            ct_mean = float(np.mean(ct_expr))
            ct_pct = float(np.mean(ct_expr > 0) * 100)
            n_cells = int(mask.sum())
            print(f"  {ct}: mean={ct_mean:.4f}, {ct_pct:.1f}% expressing, n={n_cells}")
            ct_data[ct] = {
                'mean': round(ct_mean, 6),
                'pct_expressing': round(ct_pct, 2),
                'n_cells': n_cells,
            }
        results['coro1c_by_cell_type'] = ct_data

    return results


def main():
    print("=" * 70)
    print("GSE287257 snRNA-seq Analysis: CORO1C in ALS Motor Neurons")
    print("=" * 70)

    adata = load_samples()
    adata = qc_filter(adata)
    adata = preprocess(adata)
    adata = identify_cell_types(adata)
    results = analyze_expression(adata)

    # Save results
    results_file = RESULTS_DIR / "gse287257_analysis_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    coro1c = results['actin_pathway_mn_vs_other'].get('CORO1C', {})
    if coro1c and coro1c.get('status') != 'not_found':
        print(f"CORO1C in Motor Neurons vs Others:")
        print(f"  MN mean: {coro1c['mn_mean']:.4f} ({coro1c['mn_pct_expressing']:.1f}% expressing)")
        print(f"  Other mean: {coro1c['other_mean']:.4f} ({coro1c['other_pct_expressing']:.1f}% expressing)")
        print(f"  log2FC: {coro1c['log2fc_mn_vs_other']:.3f}")
        print(f"  p-value: {coro1c['pvalue']:.2e}")
        print(f"  Significant: {coro1c['significant']}")

    coro1c_als = results['actin_pathway_als_vs_control'].get('CORO1C', {})
    if coro1c_als and coro1c_als.get('status') != 'not_found':
        print(f"\nCORO1C ALS vs Control (all cells):")
        print(f"  ALS mean: {coro1c_als['als_mean']:.4f}")
        print(f"  Control mean: {coro1c_als['ctrl_mean']:.4f}")
        print(f"  log2FC: {coro1c_als['log2fc_als_vs_ctrl']:.3f}")
        print(f"  p-value: {coro1c_als['pvalue']:.2e}")

    coro1c_mn = results['actin_pathway_als_mn_specific'].get('CORO1C', {})
    if coro1c_mn and coro1c_mn.get('status') != 'not_found':
        print(f"\nCORO1C ALS-MN vs Control-MN:")
        print(f"  ALS-MN mean: {coro1c_mn['als_mn_mean']:.4f}")
        print(f"  Control-MN mean: {coro1c_mn['ctrl_mn_mean']:.4f}")
        print(f"  log2FC: {coro1c_mn['log2fc']:.3f}")
        print(f"  p-value: {coro1c_mn['pvalue']:.2e}")

    print(f"\nTotal cells: {results['metadata']['n_cells_total']}")
    print(f"Motor neurons: {results['metadata']['n_motor_neurons']}")
    print(f"ALS MNs: {results['metadata'].get('n_als_motor_neurons', 'N/A')}")
    print(f"Control MNs: {results['metadata'].get('n_ctrl_motor_neurons', 'N/A')}")


if __name__ == '__main__':
    main()
