import pandas as pd

df = pd.read_csv('plots/fc_visualizations/algorithm_metric_variance_table.csv')

algos = {
    'rdp_downsample': 'Douglas-Peucker',
    'min_filter': 'Min Filter',
    'max_filter': 'Max Filter',
    'fpcs_downsample': 'FPCS',
    'asap_aggregator': 'ASAP',
    'chebyshev_filter': 'Chebyshev',
    'elliptical_filter': 'Elliptical',
    'lttb_downsample': 'LTTB',
    'minmaxlttb_downsample': 'MinMaxLTTB'
}

for algo_code, algo_name in algos.items():
    avg = df[df['algorithm']==algo_code].iloc[:, 1:].mean(axis=1).values[0]
    print(f'{algo_name}: {avg:.2f}')
