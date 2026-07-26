"""
Create per-metric heatmaps from fc_score_datapoint_category_count.csv files
Uses the grades already calculated in those files
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from util import list_datasets
from algorithm_names import get_algorithm_name


def load_all_grades():
    """Load grades from all dataset count files"""
    datasets = list_datasets()
    all_data = []
    
    for dataset_info in datasets:
        dataset_id = dataset_info['id'] if isinstance(dataset_info, dict) else dataset_info
        count_file = Path('plots') / dataset_id / 'fc_score_datapoint_category_count.csv'
        
        if not count_file.exists():
            continue
        
        df = pd.read_csv(count_file)
        df['dataset'] = dataset_id
        all_data.append(df)
    
    return pd.concat(all_data, ignore_index=True)


def create_metric_heatmaps(grades_df, output_dir='plots/fc_visualizations/by_metric'):
    """Create heatmaps for each metric"""
    print(f"\n📊 Creating per-metric heatmaps...")
    
    # Apply display names
    grades_df = grades_df.copy()
    grades_df['algorithm'] = grades_df['algorithm'].apply(get_algorithm_name)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    metrics = sorted(grades_df['metric'].unique())
    print(f"   Found {len(metrics)} metrics")
    
    grade_map = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'F': 1}
    
    for i, metric in enumerate(metrics, 1):
        metric_df = grades_df[grades_df['metric'] == metric]
        
        # Pivot: algorithms on rows, datasets on columns
        pivot = metric_df.pivot(index='algorithm', columns='dataset', values='grade')
        pivot_numeric = pivot.applymap(lambda x: grade_map.get(x, 0))
        
        # Create both greyscale and colored versions
        for version in ['greyscale', 'colored']:
            fig, ax = plt.subplots(figsize=(40, 10))
            
            if version == 'greyscale':
                cmap = sns.color_palette(['#2d2d2d', '#525252', '#7a7a7a', '#a8a8a8', '#d6d6d6'], as_cmap=True)
            else:
                from matplotlib.colors import ListedColormap
                colors = ["#e6d5f5", '#c9a8e8','#9b6fd9', '#7340b8', '#4a1a7a']  # F, D, C, B, A (purple)
                cmap = ListedColormap(colors)
            
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
                annot_kws={'fontsize': 16, 'fontweight': 'bold'}
            )
            
            if version == 'colored':
                for text in ax.texts:
                    grade = text.get_text()
                    if grade in ['A', 'B', 'C']:
                        text.set_color('white')
                    else:
                        text.set_color('black')
            
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_title('')
            ax.tick_params(labelsize=16)
            ax.xaxis.tick_top()
            ax.set_xticklabels(ax.get_xticklabels(), rotation=90, ha='center')
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            
            plt.tight_layout()
            
            safe_metric_name = metric.replace('/', '_').replace(' ', '_')
            svg_path = output_path / f'{safe_metric_name}_{version}.svg'
            png_path = output_path / f'{safe_metric_name}_{version}.pdf'
            
            plt.savefig(svg_path, dpi=300, bbox_inches='tight')
            plt.savefig(png_path, dpi=300, bbox_inches='tight')
            plt.close()
        
        if i % 5 == 0 or i == len(metrics):
            print(f"   Processed {i}/{len(metrics)} metrics...")
    
    print(f"   ✅ Created {len(metrics) * 2} heatmaps ({len(metrics)} greyscale + {len(metrics)} colored)")


def main():
    print("=" * 80)
    print("CREATE PER-METRIC HEATMAPS FROM COUNT FILES")
    print("=" * 80)
    
    # Load all grades
    print("\nLoading grades from fc_score_datapoint_category_count.csv files...")
    grades_df = load_all_grades()
    print(f"   ✅ Loaded {len(grades_df)} grade records")
    
    # Create heatmaps
    create_metric_heatmaps(grades_df)
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)
    print(f"\nFiles saved in: plots/fc_visualizations/by_metric/")
    print("=" * 80)


if __name__ == '__main__':
    main()
