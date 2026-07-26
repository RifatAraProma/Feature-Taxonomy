"""
Display mode grades per metric for each algorithm
Reads from algorithm_metric_mode_grades.csv and formats output
"""

import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, 'server')
from algorithm_names import get_algorithm_name


def main():
    print("="*80)
    print("MODE GRADES BY ALGORITHM AND METRIC")
    print("="*80)
    
    # Load data
    csv_path = Path('plots/fc_visualizations/algorithm_metric_mode_grades.csv')
    df = pd.read_csv(csv_path)
    
    print(f"\nLoaded {len(df)} algorithm-metric combinations")
    
    # Apply display names
    df['algorithm_display'] = df['algorithm'].apply(get_algorithm_name)
    
    # Sort alphabetically by display name
    df = df.sort_values('algorithm_display')
    
    # Group by algorithm
    for algo_display, algo_df in df.groupby('algorithm_display', sort=False):
        print("\n" + "="*80)
        print(f"{algo_display}")
        print("="*80)
        
        # Sort metrics alphabetically
        algo_df = algo_df.sort_values('metric')
        
        # Display in a table format
        print(f"{'Metric':<35} {'Mode Grade':<12} A    B    C    D    F")
        print("-"*80)
        
        for _, row in algo_df.iterrows():
            metric = row['metric']
            mode = row['mode']
            a_count = row['A']
            b_count = row['B']
            c_count = row['C']
            d_count = row['D']
            f_count = row['F']
            
            print(f"{metric:<35} {mode:<12} {a_count:<4} {b_count:<4} {c_count:<4} {d_count:<4} {f_count:<4}")
    
    print("\n" + "="*80)
    print("SUMMARY BY ALGORITHM")
    print("="*80)
    
    # Count mode grades per algorithm
    summary_data = []
    for algo_display, algo_df in df.groupby('algorithm_display', sort=False):
        mode_counts = algo_df['mode'].str.split(', ').explode().value_counts()
        
        summary_data.append({
            'Algorithm': algo_display,
            'A modes': mode_counts.get('A', 0),
            'B modes': mode_counts.get('B', 0),
            'C modes': mode_counts.get('C', 0),
            'D modes': mode_counts.get('D', 0),
            'F modes': mode_counts.get('F', 0),
            'Total metrics': len(algo_df)
        })
    
    summary_df = pd.DataFrame(summary_data)
    print("\n" + summary_df.to_string(index=False))
    
    print("\n" + "="*80)
    print("OUTPUT")
    print("="*80)
    
    # Save a detailed report
    output_file = Path('plots/fc_visualizations/algorithm_metric_mode_report.txt')
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("MODE GRADES BY ALGORITHM AND METRIC\n")
        f.write("="*80 + "\n\n")
        
        for algo_display, algo_df in df.groupby('algorithm_display', sort=False):
            f.write("\n" + "="*80 + "\n")
            f.write(f"{algo_display}\n")
            f.write("="*80 + "\n")
            
            algo_df = algo_df.sort_values('metric')
            f.write(f"{'Metric':<35} {'Mode Grade':<12} A    B    C    D    F\n")
            f.write("-"*80 + "\n")
            
            for _, row in algo_df.iterrows():
                metric = row['metric']
                mode = row['mode']
                a_count = row['A']
                b_count = row['B']
                c_count = row['C']
                d_count = row['D']
                f_count = row['F']
                
                f.write(f"{metric:<35} {mode:<12} {a_count:<4} {b_count:<4} {c_count:<4} {d_count:<4} {f_count:<4}\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("SUMMARY BY ALGORITHM\n")
        f.write("="*80 + "\n\n")
        f.write(summary_df.to_string(index=False) + "\n")
    
    print(f"\n✅ Saved detailed report to: {output_file}")
    print("="*80)


if __name__ == '__main__':
    main()
