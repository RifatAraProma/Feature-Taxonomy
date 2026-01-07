"""
Visualize FC Score Distribution Summaries using Altair
Creates interactive visualizations from the FC score summary CSVs
"""

import pandas as pd
import altair as alt
from pathlib import Path

# Enable data transformer for large datasets
alt.data_transformers.disable_max_rows()

def load_summaries(plots_dir='plots'):
    """Load the three summary CSV files"""
    dataset_summary = pd.read_csv(Path(plots_dir) / 'dataset_fc_summary.csv')
    algorithm_summary = pd.read_csv(Path(plots_dir) / 'dataset_algorithm_fc_summary.csv')
    feature_summary = pd.read_csv(Path(plots_dir) / 'dataset_feature_fc_summary.csv')
    
    return dataset_summary, algorithm_summary, feature_summary


def create_dataset_heatmap(dataset_summary):
    """
    Heatmap showing rating distribution across datasets
    Rows: Datasets, Columns: Rating categories
    """
    # Reshape data for heatmap
    df = dataset_summary[['dataset', 'excellent_pct', 'good_pct', 'fair_pct', 'poor_pct']].copy()
    df_long = df.melt(id_vars='dataset', 
                      var_name='rating', 
                      value_name='percentage')
    
    # Clean rating names
    df_long['rating'] = df_long['rating'].str.replace('_pct', '').str.title()
    
    # Sort datasets by excellent percentage
    dataset_order = dataset_summary.sort_values('excellent_pct', ascending=False)['dataset'].tolist()
    
    chart = alt.Chart(df_long).mark_rect().encode(
        x=alt.X('rating:N', 
                title='Rating Category',
                sort=['Excellent', 'Good', 'Fair', 'Poor']),
        y=alt.Y('dataset:N', 
                title='Dataset',
                sort=dataset_order),
        color=alt.Color('percentage:Q',
                       scale=alt.Scale(scheme='viridis'),
                       title='Percentage (%)'),
        tooltip=[
            alt.Tooltip('dataset:N', title='Dataset'),
            alt.Tooltip('rating:N', title='Rating'),
            alt.Tooltip('percentage:Q', title='Percentage', format='.1f')
        ]
    ).properties(
        width=400,
        height=1200,
        title='FC Score Rating Distribution by Dataset'
    )
    
    return chart


def create_algorithm_performance_heatmap(algorithm_summary):
    """
    Heatmap showing algorithm performance across rating categories
    Average percentages across all datasets
    """
    # Compute average percentages per algorithm
    algo_avg = algorithm_summary.groupby('algorithm')[['excellent', 'good', 'fair', 'poor']].mean().reset_index()
    
    # Reshape for heatmap
    df_long = algo_avg.melt(id_vars='algorithm',
                            var_name='rating',
                            value_name='percentage')
    
    df_long['rating'] = df_long['rating'].str.title()
    
    # Sort algorithms by excellent percentage
    algo_order = algo_avg.sort_values('excellent', ascending=False)['algorithm'].tolist()
    
    chart = alt.Chart(df_long).mark_rect().encode(
        x=alt.X('rating:N',
                title='Rating Category',
                sort=['Excellent', 'Good', 'Fair', 'Poor']),
        y=alt.Y('algorithm:N',
                title='Algorithm',
                sort=algo_order),
        color=alt.Color('percentage:Q',
                       scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100]),
                       title='Avg % Across Datasets'),
        tooltip=[
            alt.Tooltip('algorithm:N', title='Algorithm'),
            alt.Tooltip('rating:N', title='Rating'),
            alt.Tooltip('percentage:Q', title='Avg %', format='.1f')
        ]
    ).properties(
        width=400,
        height=400,
        title='Average Algorithm Performance Across All Datasets'
    )
    
    return chart


def create_feature_preservation_heatmap(feature_summary):
    """
    Heatmap showing feature preservation quality across rating categories
    Average percentages across all datasets
    """
    # Compute average percentages per feature
    feat_avg = feature_summary.groupby('feature')[['excellent', 'good', 'fair', 'poor']].mean().reset_index()
    
    # Reshape for heatmap
    df_long = feat_avg.melt(id_vars='feature',
                            var_name='rating',
                            value_name='percentage')
    
    df_long['rating'] = df_long['rating'].str.title()
    
    # Sort features by excellent percentage
    feat_order = feat_avg.sort_values('excellent', ascending=False)['feature'].tolist()
    
    chart = alt.Chart(df_long).mark_rect().encode(
        x=alt.X('rating:N',
                title='Rating Category',
                sort=['Excellent', 'Good', 'Fair', 'Poor']),
        y=alt.Y('feature:N',
                title='Feature',
                sort=feat_order),
        color=alt.Color('percentage:Q',
                       scale=alt.Scale(scheme='redyellowgreen', domain=[0, 100]),
                       title='Avg % Across Datasets'),
        tooltip=[
            alt.Tooltip('feature:N', title='Feature'),
            alt.Tooltip('rating:N', title='Rating'),
            alt.Tooltip('percentage:Q', title='Avg %', format='.1f')
        ]
    ).properties(
        width=400,
        height=500,
        title='Feature Preservation Quality Across All Datasets'
    )
    
    return chart


def create_stacked_bar_top_bottom(dataset_summary, n=10):
    """
    Stacked bar chart comparing top vs bottom datasets
    """
    # Get top and bottom n datasets by excellent %
    top_n = dataset_summary.nlargest(n, 'excellent_pct')
    bottom_n = dataset_summary.nsmallest(n, 'excellent_pct')
    
    # Combine and add category
    top_n['category'] = 'Top ' + str(n)
    bottom_n['category'] = 'Bottom ' + str(n)
    
    df = pd.concat([top_n, bottom_n])
    
    # Reshape for stacked bar
    df_long = df.melt(id_vars=['dataset', 'category'],
                      value_vars=['excellent_pct', 'good_pct', 'fair_pct', 'poor_pct'],
                      var_name='rating',
                      value_name='percentage')
    
    df_long['rating'] = df_long['rating'].str.replace('_pct', '').str.title()
    
    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X('percentage:Q',
                title='Percentage (%)',
                stack='normalize'),
        y=alt.Y('dataset:N',
                title='Dataset',
                sort=alt.EncodingSortField('percentage', op='sum', order='descending')),
        color=alt.Color('rating:N',
                       scale=alt.Scale(
                           domain=['Excellent', 'Good', 'Fair', 'Poor'],
                           range=['#2ca02c', '#98df8a', '#ffbb78', '#d62728']
                       ),
                       title='Rating'),
        tooltip=[
            alt.Tooltip('dataset:N', title='Dataset'),
            alt.Tooltip('rating:N', title='Rating'),
            alt.Tooltip('percentage:Q', title='Percentage', format='.1f')
        ]
    ).properties(
        width=600,
        height=400,
        title=f'FC Score Distribution: Top {n} vs Bottom {n} Datasets'
    ).facet(
        row=alt.Row('category:N', title=None)
    )
    
    return chart


def create_dataset_type_comparison(dataset_summary):
    """
    Compare rating distributions across dataset types (astro, climate, EEG, stock, unemployment)
    """
    # Extract dataset type from name
    def get_dataset_type(name):
        if name.startswith('astro_'):
            return 'Astronomy'
        elif name.startswith('climate_'):
            return 'Climate'
        elif name.startswith('eeg_'):
            return 'EEG'
        elif name.startswith('stock_'):
            return 'Stock Market'
        elif name.startswith('unemployment_'):
            return 'Unemployment'
        elif name.startswith('chi_'):
            return 'Crime'
        elif name.startswith('flights_'):
            return 'Flights'
        elif name.startswith('nz_'):
            return 'Tourism'
        else:
            return 'Other'
    
    df = dataset_summary.copy()
    df['type'] = df['dataset'].apply(get_dataset_type)
    
    # Average by type
    type_avg = df.groupby('type')[['excellent_pct', 'good_pct', 'fair_pct', 'poor_pct']].mean().reset_index()
    
    # Reshape
    df_long = type_avg.melt(id_vars='type',
                            var_name='rating',
                            value_name='percentage')
    
    df_long['rating'] = df_long['rating'].str.replace('_pct', '').str.title()
    
    chart = alt.Chart(df_long).mark_bar().encode(
        x=alt.X('type:N', title='Dataset Type'),
        y=alt.Y('percentage:Q', title='Average Percentage (%)'),
        color=alt.Color('rating:N',
                       scale=alt.Scale(
                           domain=['Excellent', 'Good', 'Fair', 'Poor'],
                           range=['#2ca02c', '#98df8a', '#ffbb78', '#d62728']
                       ),
                       title='Rating'),
        tooltip=[
            alt.Tooltip('type:N', title='Dataset Type'),
            alt.Tooltip('rating:N', title='Rating'),
            alt.Tooltip('percentage:Q', title='Avg %', format='.1f')
        ]
    ).properties(
        width=500,
        height=400,
        title='FC Score Distribution by Dataset Type'
    )
    
    return chart


def create_algorithm_feature_grid(algorithm_summary, feature_summary):
    """
    Grid showing algorithm × feature performance
    Color-coded by excellent percentage
    """
    # Compute average excellent % per algorithm
    algo_perf = algorithm_summary.groupby('algorithm')['excellent'].mean().reset_index()
    algo_perf.columns = ['algorithm', 'avg_excellent']
    
    # Compute average excellent % per feature
    feat_perf = feature_summary.groupby('feature')['excellent'].mean().reset_index()
    feat_perf.columns = ['feature', 'avg_excellent']
    
    # Create cross-join for all combinations
    algo_perf['key'] = 1
    feat_perf['key'] = 1
    
    grid = algo_perf.merge(feat_perf, on='key', suffixes=('_algo', '_feat')).drop('key', axis=1)
    
    # Average the two metrics
    grid['performance'] = (grid['avg_excellent_algo'] + grid['avg_excellent_feat']) / 2
    
    chart = alt.Chart(grid).mark_rect().encode(
        x=alt.X('algorithm:N', title='Algorithm'),
        y=alt.Y('feature:N', title='Feature'),
        color=alt.Color('performance:Q',
                       scale=alt.Scale(scheme='viridis'),
                       title='Avg Excellent %'),
        tooltip=[
            alt.Tooltip('algorithm:N', title='Algorithm'),
            alt.Tooltip('feature:N', title='Feature'),
            alt.Tooltip('performance:Q', title='Performance', format='.1f')
        ]
    ).properties(
        width=800,
        height=600,
        title='Algorithm × Feature Performance Grid'
    )
    
    return chart


def create_quartile_distribution(dataset_summary):
    """
    Distribution of quartile values across datasets
    """
    df = dataset_summary[['dataset', 'q25', 'q50', 'q75']].copy()
    df_long = df.melt(id_vars='dataset',
                      var_name='quartile',
                      value_name='value')
    
    chart = alt.Chart(df_long).mark_boxplot(extent='min-max').encode(
        x=alt.X('quartile:N', 
                title='Quartile',
                sort=['q25', 'q50', 'q75']),
        y=alt.Y('value:Q', title='FC Score Value'),
        color=alt.Color('quartile:N',
                       scale=alt.Scale(
                           domain=['q25', 'q50', 'q75'],
                           range=['#d62728', '#ff7f0e', '#2ca02c']
                       ),
                       title='Quartile')
    ).properties(
        width=400,
        height=300,
        title='Distribution of Quartile Values Across All Datasets'
    )
    
    return chart


def save_visualizations(plots_dir='plots'):
    """Generate and save all visualizations"""
    print("=" * 80)
    print("FC SCORE VISUALIZATION GENERATION")
    print("=" * 80)
    
    # Load data
    print("\n📊 Loading summary CSV files...")
    dataset_summary, algorithm_summary, feature_summary = load_summaries(plots_dir)
    print(f"   ✅ Dataset summary: {len(dataset_summary)} rows")
    print(f"   ✅ Algorithm summary: {len(algorithm_summary)} rows")
    print(f"   ✅ Feature summary: {len(feature_summary)} rows")
    
    output_dir = Path(plots_dir) / 'fc_visualizations'
    output_dir.mkdir(exist_ok=True)
    
    # Generate visualizations
    print(f"\n📊 Generating visualizations...")
    
    # 1. Dataset heatmap
    print("   1/8 Creating dataset rating heatmap...")
    chart1 = create_dataset_heatmap(dataset_summary)
    chart1.save(str(output_dir / 'dataset_rating_heatmap.html'))
    
    # 2. Algorithm performance heatmap
    print("   2/8 Creating algorithm performance heatmap...")
    chart2 = create_algorithm_performance_heatmap(algorithm_summary)
    chart2.save(str(output_dir / 'algorithm_performance_heatmap.html'))
    
    # 3. Feature preservation heatmap
    print("   3/8 Creating feature preservation heatmap...")
    chart3 = create_feature_preservation_heatmap(feature_summary)
    chart3.save(str(output_dir / 'feature_preservation_heatmap.html'))
    
    # 4. Stacked bar: top vs bottom
    print("   4/8 Creating top vs bottom datasets stacked bar...")
    chart4 = create_stacked_bar_top_bottom(dataset_summary, n=10)
    chart4.save(str(output_dir / 'top_bottom_datasets_stacked.html'))
    
    # 5. Dataset type comparison
    print("   5/8 Creating dataset type comparison...")
    chart5 = create_dataset_type_comparison(dataset_summary)
    chart5.save(str(output_dir / 'dataset_type_comparison.html'))
    
    # 6. Algorithm × Feature grid
    print("   6/8 Creating algorithm × feature performance grid...")
    chart6 = create_algorithm_feature_grid(algorithm_summary, feature_summary)
    chart6.save(str(output_dir / 'algorithm_feature_grid.html'))
    
    # 7. Quartile distribution
    print("   7/8 Creating quartile distribution boxplot...")
    chart7 = create_quartile_distribution(dataset_summary)
    chart7.save(str(output_dir / 'quartile_distribution.html'))
    
    # 8. Combined dashboard
    print("   8/8 Creating combined dashboard...")
    dashboard = alt.vconcat(
        alt.hconcat(chart2, chart3),
        alt.hconcat(chart5, chart7)
    ).properties(
        title='FC Score Summary Dashboard'
    ).configure_title(
        fontSize=20,
        anchor='middle'
    )
    dashboard.save(str(output_dir / 'dashboard.html'))
    
    print(f"\n✅ All visualizations saved to: {output_dir.absolute()}")
    print("\n📄 Generated files:")
    print("   1. dataset_rating_heatmap.html - Heatmap of rating distribution by dataset")
    print("   2. algorithm_performance_heatmap.html - Algorithm performance across ratings")
    print("   3. feature_preservation_heatmap.html - Feature preservation quality")
    print("   4. top_bottom_datasets_stacked.html - Top 10 vs Bottom 10 datasets")
    print("   5. dataset_type_comparison.html - Performance by dataset type")
    print("   6. algorithm_feature_grid.html - Algorithm × Feature performance grid")
    print("   7. quartile_distribution.html - Quartile value distributions")
    print("   8. dashboard.html - Combined overview dashboard")
    print("\n💡 Open any HTML file in your browser for interactive exploration!")
    print("=" * 80)


if __name__ == '__main__':
    save_visualizations()
