"""
Visualize L1 vs PAE with quality regions based on regression-adjusted boundaries.

Instead of horizontal regions, this uses curved/slanted boundaries that account
for the expected relationship: lower PAE should correspond to lower L1 (better preservation).

Uses polynomial regression to model the PAE-L1 relationship and defines quality
regions based on residual distances from the fitted curve.
"""

import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures

def load_precomputed_data(dataset_name="stock_aapl_price"):
    """Load all precomputed level files for a dataset."""
    data_points = []
    
    # Get all JSON files in the precomputed directory
    pattern = f"precomputed/{dataset_name}/*_level_*.json"
    files = glob.glob(pattern)
    
    print(f"Found {len(files)} precomputed files")
    
    for filepath in files:
        try:
            with open(filepath, 'r') as f:
                level_data = json.load(f)
            
            # Extract algorithm name and level from filename
            filename = Path(filepath).stem  # e.g., "gaussian_filter_level_50"
            parts = filename.rsplit('_level_', 1)
            algorithm = parts[0]
            level = int(parts[1])
            
            # Extract metrics
            pae = level_data.get('pae')
            feature_preservation = level_data.get('feature_preservation', {})
            l1 = feature_preservation.get('level', {}).get('l1')
            
            if pae is not None and l1 is not None:
                data_points.append({
                    'algorithm': algorithm,
                    'level': level,
                    'pae': pae,
                    'l1': l1
                })
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return data_points


def fit_pae_l1_relationship(pae_values, l1_values, degree=2):
    """
    Fit polynomial regression to model PAE-L1 relationship.
    
    Args:
        pae_values: Array of PAE values
        l1_values: Array of L1 values
        degree: Polynomial degree (1=linear, 2=quadratic, 3=cubic)
    
    Returns:
        Fitted model and polynomial features transformer
    """
    # Reshape for sklearn
    X = pae_values.reshape(-1, 1)
    y = l1_values
    
    # Create polynomial features
    poly_features = PolynomialFeatures(degree=degree, include_bias=False)
    X_poly = poly_features.fit_transform(X)
    
    # Fit model
    model = LinearRegression()
    model.fit(X_poly, y)
    
    # Calculate R² score
    r2_score = model.score(X_poly, y)
    
    print(f"\nPolynomial Regression (degree={degree}):")
    print(f"  R² score: {r2_score:.4f}")
    
    # Print equation
    if degree == 1:
        print(f"  Equation: L1 = {model.intercept_:.4f} + {model.coef_[0]:.4f} * PAE")
    elif degree == 2:
        print(f"  Equation: L1 = {model.intercept_:.4f} + {model.coef_[0]:.4f} * PAE + {model.coef_[1]:.4f} * PAE²")
    elif degree == 3:
        print(f"  Equation: L1 = {model.intercept_:.4f} + {model.coef_[0]:.4f} * PAE + {model.coef_[1]:.4f} * PAE² + {model.coef_[2]:.4f} * PAE³")
    
    return model, poly_features, r2_score


def calculate_residuals(pae_values, l1_values, model, poly_features):
    """
    Calculate residuals (distance from regression line).
    
    Positive residual = above the line (worse than expected)
    Negative residual = below the line (better than expected)
    """
    X = pae_values.reshape(-1, 1)
    X_poly = poly_features.transform(X)
    
    predicted_l1 = model.predict(X_poly)
    residuals = l1_values - predicted_l1
    
    return residuals, predicted_l1


def plot_l1_vs_pae_curved_regions(data_points, degree=2):
    """
    Create scatter plot with curved quality regions based on regression residuals.
    
    Args:
        data_points: List of dicts with 'algorithm', 'pae', 'l1'
        degree: Polynomial degree for regression (1=linear, 2=quadratic, 3=cubic)
    """
    
    if not data_points:
        print("No data points to plot!")
        return
    
    # Extract data
    algorithms = [d['algorithm'] for d in data_points]
    pae_values = np.array([d['pae'] for d in data_points])
    l1_values = np.array([d['l1'] for d in data_points])
    
    print(f"\nData summary:")
    print(f"  Total points: {len(data_points)}")
    print(f"  Unique algorithms: {len(set(algorithms))}")
    print(f"  PAE range: [{pae_values.min():.4f}, {pae_values.max():.4f}]")
    print(f"  L1 range: [{l1_values.min():.2f}, {l1_values.max():.2f}]")
    
    # Fit regression model
    model, poly_features, r2_score = fit_pae_l1_relationship(pae_values, l1_values, degree=degree)
    
    # Calculate residuals
    residuals, predicted_l1 = calculate_residuals(pae_values, l1_values, model, poly_features)
    
    # Calculate residual percentiles for quality regions
    percentiles = [0, 25, 50, 75, 100]
    residual_percentiles = np.percentile(residuals, percentiles)
    
    print(f"\nResidual Percentiles (from regression line):")
    for p, v in zip(percentiles, residual_percentiles):
        print(f"  {p}th: {v:+.2f}")
    
    # Create smooth curve for plotting boundaries
    pae_smooth = np.linspace(pae_values.min(), pae_values.max(), 500)
    X_smooth = pae_smooth.reshape(-1, 1)
    X_smooth_poly = poly_features.transform(X_smooth)
    l1_smooth = model.predict(X_smooth_poly)
    
    # Calculate boundary curves (regression line ± residual percentiles)
    boundaries = {
        'excellent': l1_smooth + residual_percentiles[1],  # 25th percentile
        'good': l1_smooth + residual_percentiles[2],       # 50th percentile (median)
        'fair': l1_smooth + residual_percentiles[3],       # 75th percentile
    }
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Define quality regions with colors
    region_colors = {
        'excellent': 'green',
        'good': 'yellow',
        'fair': 'orange',
        'poor': 'red'
    }
    
    # Fill regions between curves
    # Region 1: Below 25th percentile (Excellent) - below the curve
    ax.fill_between(pae_smooth, 
                    l1_values.min() - 10,  # Bottom of plot
                    boundaries['excellent'],
                    alpha=0.15, color=region_colors['excellent'], zorder=0,
                    label='Excellent (< 25th %ile)')
    
    # Region 2: Between 25th and 50th percentile (Good)
    ax.fill_between(pae_smooth,
                    boundaries['excellent'],
                    boundaries['good'],
                    alpha=0.15, color=region_colors['good'], zorder=0,
                    label='Good (25th-50th %ile)')
    
    # Region 3: Between 50th and 75th percentile (Fair)
    ax.fill_between(pae_smooth,
                    boundaries['good'],
                    boundaries['fair'],
                    alpha=0.15, color=region_colors['fair'], zorder=0,
                    label='Fair (50th-75th %ile)')
    
    # Region 4: Above 75th percentile (Poor)
    ax.fill_between(pae_smooth,
                    boundaries['fair'],
                    l1_values.max() + 10,  # Top of plot
                    alpha=0.15, color=region_colors['poor'], zorder=0,
                    label='Poor (> 75th %ile)')
    
    # Draw regression line
    ax.plot(pae_smooth, l1_smooth, 
            'k--', linewidth=2, alpha=0.7, zorder=5,
            label=f'Regression line (R²={r2_score:.3f})')
    
    # Draw boundary curves
    ax.plot(pae_smooth, boundaries['excellent'], 'g-', linewidth=1.5, alpha=0.5, zorder=4)
    ax.plot(pae_smooth, boundaries['good'], 'y-', linewidth=1.5, alpha=0.5, zorder=4)
    ax.plot(pae_smooth, boundaries['fair'], 'orange', linewidth=1.5, alpha=0.5, zorder=4)
    
    # Algorithm colors from frontend
    algorithm_color_map = {
        'gaussian_filter': '#1E88E5',
        'median_filter': '#039BE5',
        'mean_filter': '#00ACC1',
        'min_filter': '#0097A7',
        'max_filter': '#00897B',
        'savitzky_golay_filter': '#43A047',
        'butterworth_filter': '#7CB342',
        'fft_cutoff_filter': '#a3a80bff',
        'chebyshev_filter': '#d8bc07ff',
        'elliptical_filter': '#e5a207ff',
        'lttb_downsample': '#FB8C00',
        'm4_downsample': '#F4511E',
        'rdp_downsample': '#E53935',
        'minmaxlttb_downsample': '#D81B60',
        'uniform_subsample': '#8E24AA',
        'fpcs_downsample': '#5E35B1',
        'tda_downsample': '#3949AB',
        'asap_aggregator': '#6D4C41',
        'bin_average_aggregator': '#8D6E63',
    }
    
    unique_algorithms = sorted(set(algorithms))
    
    # Plot points for each algorithm
    for algo in unique_algorithms:
        # Filter points for this algorithm
        mask = np.array([a == algo for a in algorithms])
        algo_pae = pae_values[mask]
        algo_l1 = l1_values[mask]
        
        # Get color from map or use gray as default
        algo_color = algorithm_color_map.get(algo, '#9E9E9E')
        
        ax.scatter(algo_pae, algo_l1, 
                  label=algo, 
                  color=algo_color,
                  alpha=0.7, 
                  s=50,
                  edgecolors='black',
                  linewidth=0.5,
                  zorder=6)
    
    # Labels and title
    degree_name = {1: 'Linear', 2: 'Quadratic', 3: 'Cubic'}.get(degree, f'Degree-{degree}')
    ax.set_xlabel('PAE (Perceptual Approximation Error)\nLower is Better', fontsize=13, fontweight='bold')
    ax.set_ylabel('L1 (Average Point-wise Error)\nLower is Better', fontsize=13, fontweight='bold')
    ax.set_title(f'L1 vs PAE with {degree_name} Regression-Based Quality Regions\n' +
                 'Regions account for expected PAE-L1 relationship', 
                 fontsize=14, fontweight='bold', pad=20)
    
    # Add annotation explaining the approach
    textstr = (f'{degree_name} Regression: R² = {r2_score:.3f}\n'
               f'Regions based on residual percentiles:\n'
               f'• Excellent: Below expected (< 25th %ile)\n'
               f'• Good: Near expected (25th-50th %ile)\n'
               f'• Fair: Above expected (50th-75th %ile)\n'
               f'• Poor: Well above expected (> 75th %ile)')
    
    ax.text(0.02, 0.98, textstr,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Legend - split into two: regions and algorithms
    # Get handles and labels
    handles, labels = ax.get_legend_handles_labels()
    
    # First 5 are regions + regression line
    region_handles = handles[:5]
    region_labels = labels[:5]
    
    # Rest are algorithms
    algo_handles = handles[5:]
    algo_labels = labels[5:]
    
    # Create two legends
    legend1 = ax.legend(region_handles, region_labels, 
                       loc='upper right', fontsize=9,
                       framealpha=0.95, edgecolor='black',
                       title='Quality Regions')
    ax.add_artist(legend1)  # Add first legend back
    
    legend2 = ax.legend(algo_handles, algo_labels,
                       loc='lower left', ncol=2, fontsize=7,
                       framealpha=0.95, edgecolor='black',
                       title='Algorithms')
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', zorder=1)
    
    # Set y-axis limits to avoid excessive whitespace
    y_margin = (l1_values.max() - l1_values.min()) * 0.1
    ax.set_ylim([l1_values.min() - y_margin, l1_values.max() + y_margin])
    
    plt.tight_layout()
    
    # Save plot
    output_path = f'plots/l1_vs_pae_curved_regions_deg{degree}.png'
    Path('plots').mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")
    
    plt.show()


def compare_regression_degrees(data_points):
    """
    Create a comparison plot showing linear, quadratic, and cubic regression fits.
    """
    if not data_points:
        print("No data points to plot!")
        return
    
    # Extract data
    pae_values = np.array([d['pae'] for d in data_points])
    l1_values = np.array([d['l1'] for d in data_points])
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    
    for idx, degree in enumerate([1, 2, 3]):
        ax = axes[idx]
        
        # Fit model
        model, poly_features, r2_score = fit_pae_l1_relationship(pae_values, l1_values, degree=degree)
        
        # Create smooth curve
        pae_smooth = np.linspace(pae_values.min(), pae_values.max(), 500)
        X_smooth = pae_smooth.reshape(-1, 1)
        X_smooth_poly = poly_features.transform(X_smooth)
        l1_smooth = model.predict(X_smooth_poly)
        
        # Plot data points
        ax.scatter(pae_values, l1_values, alpha=0.3, s=20, c='steelblue', edgecolors='none')
        
        # Plot regression line
        ax.plot(pae_smooth, l1_smooth, 'r-', linewidth=2, label=f'R² = {r2_score:.4f}')
        
        degree_name = {1: 'Linear', 2: 'Quadratic', 3: 'Cubic'}[degree]
        ax.set_xlabel('PAE', fontsize=11, fontweight='bold')
        ax.set_ylabel('L1', fontsize=11, fontweight='bold')
        ax.set_title(f'{degree_name} Regression', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=10)
    
    fig.suptitle('Comparison of Regression Models for PAE-L1 Relationship', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_path = 'plots/l1_vs_pae_regression_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nComparison plot saved to: {output_path}")
    
    plt.show()


def main():
    print("=" * 80)
    print("L1 vs PAE Visualization with Curved Regression-Based Quality Regions")
    print("=" * 80)
    
    # Load data
    data_points = load_precomputed_data("stock_aapl_price")
    
    if not data_points:
        print("No data found to plot!")
        return
    
    # First, compare different regression degrees
    print("\n" + "=" * 80)
    print("Step 1: Comparing regression models...")
    print("=" * 80)
    compare_regression_degrees(data_points)
    
    # Create plots with different polynomial degrees
    for degree in [1, 2, 3]:
        print("\n" + "=" * 80)
        print(f"Step 2.{degree}: Creating plot with degree {degree} regression...")
        print("=" * 80)
        plot_l1_vs_pae_curved_regions(data_points, degree=degree)

if __name__ == "__main__":
    main()
