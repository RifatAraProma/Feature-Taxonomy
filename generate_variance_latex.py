"""
Generate LaTeX table for algorithm-metric variance analysis
Each cell is colored with steelblue opacity based on variance level
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name

def variance_to_color(variance):
    """
    Convert variance to color category based on documented thresholds.
    - Low (<0.5): No color (consistent performance)
    - Moderate (0.5-1.5): Light steelblue 30% (some data-dependency)
    - High (>1.5): Dark steelblue 70% (highly data-dependent)
    """
    if variance < 0.5:
        return None  # No color
    elif variance < 1.5:
        return 30  # Light steelblue
    else:
        return 70  # Dark steelblue

def generate_latex_table():
    """Generate LaTeX table with colored cells based on variance"""
    
    # Load variance data
    df = pd.read_csv('plots/fc_visualizations/algorithm_metric_variance_table.csv', index_col=0)
    
    print(f"Loaded variance table: {df.shape[0]} algorithms × {df.shape[1]} metrics")
    
    # Get min/max variance for color scaling
    min_var = df.min().min()
    max_var = df.max().max()
    
    print(f"Variance range: {min_var:.3f} to {max_var:.3f}")
    
    # Metric display names (full names) with proper notation
    metric_names = {
        'level_l1': r'Level $\ell_1$',
        'level_linf': r'Level $\ell_\infty$',
        'mean_delta': r'Mean $\Delta$',
        'regimes_delta': r'Regimes $\Delta$',
        'extrema_wasserstein': r'Extrema $W_1$',
        'extrema_bottleneck': r'Extrema $W_\infty$',
        'spikes_dips_wasserstein': r'Spikes/Dips $W_1$',
        'spikes_dips_bottleneck': r'Spikes/Dips $W_\infty$',
        'slope_l1': r'Slope $\ell_1$',
        'slope_linf': r'Slope $\ell_\infty$',
        'curvature_l1': r'Curvature $\ell_1$',
        'curvature_linf': r'Curvature $\ell_\infty$',
        'trend_l1': r'Trend $\ell_1$',
        'trend_linf': r'Trend $\ell_\infty$',
        'regression_l1': r'Regression $\ell_1$',
        'regression_linf': r'Regression $\ell_\infty$',
        'periodicity_amplitude_delta': r'Periodicity Amplitude $\Delta$',
        'periodicity_num_periods_delta': r'Periodicity Periods $\Delta$',
        'roughness_delta': r'Roughness $\Delta$',
        'noise_l1': r'Noise $\ell_1$',
        'noise_linf': r'Noise $\ell_\infty$'
    }
    
    # Define column order: level, mean, regimes, extrema, spikes/dips, slope, curvature, trend, regression, periodicity, roughness, noise
    # Within each feature group: L1 before L_inf, Wasserstein before Bottleneck
    column_order = [
        'level_l1', 'level_linf',
        'mean_delta',
        'regimes_delta',
        'extrema_wasserstein', 'extrema_bottleneck',
        'spikes_dips_wasserstein', 'spikes_dips_bottleneck',
        'slope_l1', 'slope_linf',
        'curvature_l1', 'curvature_linf',
        'trend_l1', 'trend_linf',
        'regression_l1', 'regression_linf',
        'periodicity_amplitude_delta', 'periodicity_num_periods_delta',
        'roughness_delta',
        'noise_l1', 'noise_linf'
    ]
    
    # Reorder dataframe columns
    df = df[column_order]
    
    # Start LaTeX document
    latex = []
    latex.append("\\documentclass[landscape]{article}")
    latex.append("\\usepackage[margin=0.5in]{geometry}")
    latex.append("\\usepackage{xcolor}")
    latex.append("\\usepackage{colortbl}")
    latex.append("\\usepackage{booktabs}")
    latex.append("\\usepackage{rotating}")
    latex.append("\\usepackage{graphicx}")  # For resizebox
    latex.append("\\begin{document}")
    latex.append("\\pagestyle{empty}")
    latex.append("")
    latex.append("\\definecolor{steelblue}{RGB}{70,130,180}")
    latex.append("")
    latex.append("\\begin{table}[ht]")
    latex.append("\\centering")
    latex.append("\\caption{Algorithm Variance Across Metrics (Darker = Higher Variance)}")
    latex.append("\\label{tab:variance}")
    latex.append("\\resizebox{\\textwidth}{!}{%")
    
    # Table header
    num_cols = len(df.columns)
    latex.append(f"\\begin{{tabular}}{{l{'c' * num_cols}}}")
    latex.append("\\toprule")
    
    # Column headers (rotated for space)
    header_row = "\\textbf{Algorithm}"
    for col in df.columns:
        short_name = metric_names.get(col, col)
        header_row += f" & \\rotatebox{{90}}{{{short_name}}}"
    header_row += " \\\\"
    latex.append(header_row)
    latex.append("\\midrule")
    
    # Data rows
    for algo in df.index:
        # Get polished algorithm name
        algo_display = get_algorithm_name(algo)
        row_parts = [f"\\textbf{{{algo_display}}}"]
        
        for metric in df.columns:
            variance = df.loc[algo, metric]
            
            # Skip NaN values
            if pd.isna(variance):
                row_parts.append("--")
                continue
            
            # Get color category
            color_pct = variance_to_color(variance)
            
            # Create colored cell (or plain if no color)
            if color_pct is None:
                cell = f"{variance:.2f}"  # No color for low variance
            else:
                cell = f"\\cellcolor{{steelblue!{color_pct}}}{variance:.2f}"
            row_parts.append(cell)
        
        latex.append(" & ".join(row_parts) + " \\\\")
    
    latex.append("\\bottomrule")
    latex.append("\\end{tabular}%")
    latex.append("}%")  # End resizebox
    latex.append("\\end{table}")
    latex.append("")
    latex.append("\\vspace{1em}")
    latex.append("\\noindent\\textbf{Legend:}")
    latex.append("\\begin{itemize}")
    latex.append("\\item Variance range: [%.3f, %.3f]" % (min_var, max_var))
    latex.append("\\item \\textbf{No color}: Low variance ($<0.5$) -- consistent performance")
    latex.append("\\item \\cellcolor{steelblue!30}Light steelblue: Moderate variance ($0.5-1.5$) -- some data-dependency")
    latex.append("\\item \\cellcolor{steelblue!70}Dark steelblue: High variance ($>1.5$) -- highly data-dependent")
    latex.append("\\end{itemize}")
    latex.append("")
    latex.append("\\end{document}")
    
    # Write to file
    output_file = 'plots/fc_visualizations/variance_table.tex'
    with open(output_file, 'w') as f:
        f.write('\n'.join(latex))
    
    print(f"\n✅ Generated LaTeX table: {output_file}")
    print(f"   Compile with: pdflatex variance_table.tex")
    
    # Also create a standalone version (no document wrapper)
    latex_standalone = []
    latex_standalone.append("% Paste this into your LaTeX document")
    latex_standalone.append("% Requires: \\usepackage{xcolor,colortbl,booktabs,rotating}")
    latex_standalone.append("")
    latex_standalone.append("\\definecolor{steelblue}{RGB}{70,130,180}")
    latex_standalone.append("")
    
    # Find the table part
    table_start = latex.index("\\begin{table}[ht]")
    table_end = latex.index("\\end{table}") + 1
    latex_standalone.extend(latex[table_start:table_end])
    
    output_file_standalone = 'plots/fc_visualizations/variance_table_standalone.tex'
    with open(output_file_standalone, 'w') as f:
        f.write('\n'.join(latex_standalone))
    
    print(f"✅ Generated standalone LaTeX: {output_file_standalone}")
    print(f"   (For pasting into existing documents)")

if __name__ == '__main__':
    print("=" * 80)
    print("VARIANCE TABLE LATEX GENERATOR")
    print("=" * 80)
    generate_latex_table()
    print("=" * 80)
