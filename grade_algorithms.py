"""
Create Graded Performance Visualization
Assign letter grades (A/B/C/D/F) based on rating percentages
Simplifies Dataset × Algorithm × Feature complexity into readable heatmaps
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

def load_detailed_fc_scores():
    """Load FC scores from all datasets"""
    from server.util import list_datasets
    
    datasets = list_datasets()
    all_data = []
    
    print(f"\n📊 Loading detailed FC scores from {len(datasets)} datasets...")
    
    for i, dataset_info in enumerate(datasets, 1):
        # list_datasets returns dicts, extract the 'id' field
        dataset = dataset_info['id'] if isinstance(dataset_info, dict) else dataset_info
        fc_file = Path('plots') / dataset / 'ranking' / 'fc_scores_all.csv'
        if not fc_file.exists():
            continue
            
        df = pd.read_csv(fc_file)
        df['dataset'] = dataset
        all_data.append(df)
        
        if i % 10 == 0:
            print(f"   Loaded {i}/{len(datasets)} datasets...")
    
    print(f"   ✅ Loaded {len(all_data)} datasets successfully")
    
    return pd.concat(all_data, ignore_index=True)


def categorize_fc_scores(combined_df):
    """Add rating categories based on dataset-specific quartiles"""
    quartiles_file = 'plots/dataset_fc_summary.csv'
    quartiles = pd.read_csv(quartiles_file)
    quartiles_dict = quartiles.set_index('dataset')[['q25', 'q50', 'q75']].to_dict('index')
    
    print("\n📊 Categorizing FC scores into ratings...")
    
    def get_rating(row):
        dataset = row['dataset']
        fc_score = row['fc_score']
        
        if dataset not in quartiles_dict:
            return 'unknown'
        
        q = quartiles_dict[dataset]
        if fc_score > q['q75']:
            return 'excellent'
        elif fc_score > q['q50']:
            return 'good'
        elif fc_score > q['q25']:
            return 'fair'
        else:
            return 'poor'
    
    combined_df['rating'] = combined_df.apply(get_rating, axis=1)
    
    return combined_df


def compute_grade_per_dataset_algorithm_metric(df):
    """
    Compute letter grade for each Dataset × Algorithm × Metric combination
    Based on performance for that specific metric only
    
    Grading scale:
    - A: Excellent% > 40% OR (Excellent% + Good%) > 70%
    - B: (Excellent% + Good%) > 50%
    - C: (Excellent% + Good%) > 30%
    - D: (Excellent% + Good%) > 15%
    - F: Otherwise
    """
    print("\n📊 Computing grades for Dataset × Algorithm × Metric combinations...")
    
    # Group by dataset, algorithm, metric and count ratings
    grouped = df.groupby(['dataset', 'algorithm', 'metric', 'rating']).size().unstack(fill_value=0)
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in grouped.columns:
            grouped[rating] = 0
    
    # Calculate percentages
    total = grouped.sum(axis=1)
    pct = grouped.div(total, axis=0) * 100
    
    # Assign grades
    def assign_grade(row):
        excellent = row.get('excellent', 0)
        good = row.get('good', 0)
        combined = excellent + good
        
        if excellent > 40 or combined > 70:
            return 'A'
        elif combined > 50:
            return 'B'
        elif combined > 30:
            return 'C'
        elif combined > 15:
            return 'D'
        else:
            return 'F'
    
    pct['grade'] = pct.apply(assign_grade, axis=1)
    pct = pct.reset_index()
    
    print(f"   ✅ Computed {len(pct)} grades")
    
    return pct


def compute_grade_per_dataset_algorithm(df):
    """
    Compute letter grade for each Dataset × Algorithm combination
    Based on average performance across all metrics
    
    Grading scale:
    - A: Excellent% > 40% OR (Excellent% + Good%) > 70%
    - B: (Excellent% + Good%) > 50%
    - C: (Excellent% + Good%) > 30%
    - D: (Excellent% + Good%) > 15%
    - F: Otherwise
    """
    print("\n📊 Computing grades for Dataset × Algorithm combinations...")
    
    # Group by dataset, algorithm and count ratings across ALL metrics
    grouped = df.groupby(['dataset', 'algorithm', 'rating']).size().unstack(fill_value=0)
    
    # Ensure all rating columns exist
    for rating in ['excellent', 'good', 'fair', 'poor']:
        if rating not in grouped.columns:
            grouped[rating] = 0
    
    # Calculate percentages
    total = grouped.sum(axis=1)
    pct = grouped.div(total, axis=0) * 100
    
    # Assign grades
    def assign_grade(row):
        excellent = row.get('excellent', 0)
        good = row.get('good', 0)
        combined = excellent + good
        
        if excellent > 40 or combined > 70:
            return 'A'
        elif combined > 50:
            return 'B'
        elif combined > 30:
            return 'C'
        elif combined > 15:
            return 'D'
        else:
            return 'F'
    
    pct['grade'] = pct.apply(assign_grade, axis=1)
    pct = pct.reset_index()
    
    print(f"   ✅ Computed {len(pct)} grades")
    
    return pct


def create_grade_heatmap(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create a single heatmap: Algorithm × Dataset with letter grades
    """
    print("\n📊 Creating grade heatmap...")
    
    # Pivot for heatmap (swapped: algorithms on rows, datasets on columns)
    pivot = grades_df.pivot(index='algorithm', columns='dataset', values='grade')
    
    # Convert grades to numeric for color mapping
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot.map(lambda x: grade_map.get(x, 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(40, 10))
    
    # Create heatmap with grey colormap (matching FC score distributions)
    cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
    
    sns.heatmap(
        pivot_numeric,
        ax=ax,
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar=False,  # No legend
        linewidths=0.5,
        linecolor='white',
        annot=pivot,  # Show letter grades
        fmt='',
        annot_kws={'fontsize': 16, 'fontweight': 'bold'}
    )
    
    # No titles or axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    ax.tick_params(labelsize=16)
    
    # Dataset names at top
    ax.xaxis.tick_top()
    
    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='left')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    svg_path = output_path / 'algorithm_grades_by_dataset.svg'
    png_path = output_path / 'algorithm_grades_by_dataset.png'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_grade_heatmap_colored(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create colored version using frontend color scheme:
    Excellent: #2E7D32 (dark green)
    Good: #66BB6A (light green)
    Fair: #FFA726 (orange)
    Poor: #E53935 (red)
    F: #9E9E9E (grey)
    """
    print("\n📊 Creating colored grade heatmap...")
    
    # Pivot for heatmap (algorithms on rows, datasets on columns)
    pivot = grades_df.pivot(index='algorithm', columns='dataset', values='grade')
    
    # Convert grades to numeric for color mapping
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    pivot_numeric = pivot.map(lambda x: grade_map.get(x, 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(40, 10))
    
    # Use frontend color scheme
    # A (excellent) = dark green, B (good) = light green, C (fair) = orange, D = dark orange, F = red
    from matplotlib.colors import ListedColormap
    colors = ['#E53935', '#FF6F00', '#FFA726', '#66BB6A', '#2E7D32']  # F, D, C, B, A
    cmap = ListedColormap(colors)
    
    sns.heatmap(
        pivot_numeric,
        ax=ax,
        cmap=cmap,
        vmin=1,
        vmax=5,
        cbar=False,  # No legend
        linewidths=0.5,
        linecolor='white',
        annot=pivot,  # Show letter grades
        fmt='',
        annot_kws={'fontsize': 16, 'fontweight': 'bold', 'color': 'white'}
    )
    
    # No titles or axis labels
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_title('')
    ax.tick_params(labelsize=16)
    
    # Dataset names at top
    ax.xaxis.tick_top()
    
    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='left')
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    svg_path = output_path / 'algorithm_grades_by_dataset_colored.svg'
    png_path = output_path / 'algorithm_grades_by_dataset_colored.png'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_grade_distribution_bar(grades_df, output_dir='plots/fc_visualizations'):
    """
    Bar chart showing grade distribution for each algorithm
    """
    print("\n📊 Creating grade distribution bar chart...")
    
    # Count grades per algorithm
    grade_counts = grades_df.groupby(['algorithm', 'grade']).size().unstack(fill_value=0)
    
    # Ensure all grades exist
    for grade in ['A', 'B', 'C', 'D', 'F']:
        if grade not in grade_counts.columns:
            grade_counts[grade] = 0
    
    # Reorder columns
    grade_counts = grade_counts[['A', 'B', 'C', 'D', 'F']]
    
    # Sort algorithms by number of A's + B's
    grade_counts['total_good'] = grade_counts['A'] + grade_counts['B']
    grade_counts = grade_counts.sort_values('total_good', ascending=False)
    grade_counts = grade_counts.drop('total_good', axis=1)
    
    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(14, 8))
    
    grade_counts.plot(
        kind='bar',
        stacked=True,
        ax=ax,
        color=['#2ca02c', '#98df8a', '#ffdd57', '#ff7f0e', '#d62728'],
        width=0.8
    )
    
    ax.set_title('Algorithm Grade Distribution Across All Datasets', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Algorithm', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of Datasets', fontsize=11, fontweight='bold')
    ax.legend(title='Grade', loc='upper right', frameon=True)
    ax.tick_params(labelsize=9)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_dir)
    svg_path = output_path / 'algorithm_grade_distribution.svg'
    png_path = output_path / 'algorithm_grade_distribution.png'
    
    plt.savefig(svg_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    
    print(f"   ✅ Saved: {svg_path.name}")
    
    plt.close()


def create_summary_table(grades_df, output_dir='plots/fc_visualizations'):
    """
    Create summary CSV with grade statistics
    """
    print("\n📊 Creating summary statistics...")
    
    # Overall grade distribution
    overall = grades_df['grade'].value_counts().sort_index()
    
    # Grade distribution by algorithm
    by_algo = grades_df.groupby('algorithm')['grade'].value_counts().unstack(fill_value=0)
    for grade in ['A', 'B', 'C', 'D', 'F']:
        if grade not in by_algo.columns:
            by_algo[grade] = 0
    by_algo = by_algo[['A', 'B', 'C', 'D', 'F']]
    
    # Add GPA-style metric (A=4.0, B=3.0, C=2.0, D=1.0, F=0.0)
    grade_values = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    grades_df['grade_value'] = grades_df['grade'].map(grade_values)
    
    gpa = grades_df.groupby('algorithm')['grade_value'].mean().sort_values(ascending=False)
    by_algo['GPA'] = gpa
    
    # Sort by GPA
    by_algo = by_algo.sort_values('GPA', ascending=False)
    
    # Save
    output_path = Path(output_dir)
    csv_path = output_path / 'algorithm_grade_summary.csv'
    by_algo.to_csv(csv_path)
    
    print(f"   ✅ Saved: {csv_path.name}")
    
    # Print top performers
    print("\n📊 Top 5 Algorithms by GPA:")
    for i, (algo, row) in enumerate(by_algo.head(5).iterrows(), 1):
        print(f"   {i}. {algo}: GPA={row['GPA']:.2f} (A:{int(row['A'])}, B:{int(row['B'])}, C:{int(row['C'])}, D:{int(row['D'])}, F:{int(row['F'])})")
    
    return by_algo


def create_metric_heatmaps(grades_df, output_dir='plots/fc_visualizations/by_metric'):
    """
    Create separate heatmaps for each of the 23 metrics
    Both greyscale and colored versions
    """
    print("\n📊 Creating per-metric heatmaps...")
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Get list of all metrics
    metrics = sorted(grades_df['metric'].unique())
    print(f"   Found {len(metrics)} metrics")
    
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    
    for i, metric in enumerate(metrics, 1):
        # Filter data for this metric
        metric_df = grades_df[grades_df['metric'] == metric]
        
        # Pivot: algorithms on rows, datasets on columns
        pivot = metric_df.pivot(index='algorithm', columns='dataset', values='grade')
        pivot_numeric = pivot.map(lambda x: grade_map.get(x, 0))
        
        # Create both versions
        for version in ['greyscale', 'colored']:
            fig, ax = plt.subplots(figsize=(40, 10))
            
            if version == 'greyscale':
                cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
                text_color = 'black'
            else:  # colored
                from matplotlib.colors import ListedColormap
                colors = ['#E53935', '#FF6F00', '#FFA726', '#66BB6A', '#2E7D32']  # F, D, C, B, A
                cmap = ListedColormap(colors)
                text_color = 'white'
            
            sns.heatmap(
                pivot_numeric,
                ax=ax,
                cmap=cmap,
                vmin=1,
                vmax=5,
                cbar=False,
                linewidths=0.5,
                linecolor='white',
                annot=pivot,
                fmt='',
                annot_kws={'fontsize': 16, 'fontweight': 'bold', 'color': text_color}
            )
            
            # No titles or axis labels
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_title('')
            ax.tick_params(labelsize=16)
            
            # Dataset names at top
            ax.xaxis.tick_top()
            
            # Rotate labels
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='left')
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            
            plt.tight_layout()
            
            # Save with metric name
            safe_metric_name = metric.replace('/', '_').replace(' ', '_')
            svg_path = output_path / f'{safe_metric_name}_{version}.svg'
            png_path = output_path / f'{safe_metric_name}_{version}.png'
            
            plt.savefig(svg_path, dpi=300, bbox_inches='tight')
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            
            plt.close()
        
        if i % 5 == 0 or i == len(metrics):
            print(f"   Processed {i}/{len(metrics)} metrics...")
    
    print(f"   ✅ Created {len(metrics) * 2} heatmaps ({len(metrics)} greyscale + {len(metrics)} colored)")


def main():
    print("=" * 80)
    print("ALGORITHM GRADING SYSTEM")
    print("=" * 80)
    
    # Load data
    combined = load_detailed_fc_scores()
    
    # Categorize scores
    combined = categorize_fc_scores(combined)
    
    # Compute grades averaged across all metrics
    grades_df = compute_grade_per_dataset_algorithm(combined)
    
    # Save grades CSV
    output_path = Path('plots/fc_visualizations')
    output_path.mkdir(exist_ok=True, parents=True)
    grades_csv = output_path / 'dataset_algorithm_grades.csv'
    grades_df.to_csv(grades_csv, index=False)
    print(f"\n💾 Saved grades: {grades_csv}")
    
    # Create overall visualizations
    create_grade_heatmap(grades_df)
    create_grade_heatmap_colored(grades_df)
    create_grade_distribution_bar(grades_df)
    summary = create_summary_table(grades_df)
    
    # Compute grades per metric
    metric_grades_df = compute_grade_per_dataset_algorithm_metric(combined)
    
    # Save metric-specific grades CSV
    metric_grades_csv = output_path / 'dataset_algorithm_metric_grades.csv'
    metric_grades_df.to_csv(metric_grades_csv, index=False)
    print(f"\n💾 Saved metric-specific grades: {metric_grades_csv}")
    
    # Create per-metric heatmaps (23 metrics × 2 versions = 46 heatmaps)
    create_metric_heatmaps(metric_grades_df)
    
    print("\n" + "=" * 80)
    print("✅ GRADING COMPLETE!")
    print("=" * 80)
    print(f"\nFiles created in {output_path}:")
    print("  1. dataset_algorithm_grades.csv - Full grade table (averaged across metrics)")
    print("  2. algorithm_grades_by_dataset.svg/png - Heatmap with letter grades (greyscale)")
    print("  3. algorithm_grades_by_dataset_colored.svg/png - Heatmap with letter grades (colored)")
    print("  4. algorithm_grade_distribution.svg/png - Stacked bar chart")
    print("  5. algorithm_grade_summary.csv - Summary statistics with GPA")
    print("  6. dataset_algorithm_metric_grades.csv - Grades for each metric separately")
    print(f"  7. by_metric/ - 46 heatmaps (23 metrics × 2 versions each)")
    print("=" * 80)


if __name__ == '__main__':
    main()
