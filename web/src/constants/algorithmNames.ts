/**
 * Centralized algorithm display names configuration.
 * Maps internal algorithm identifiers to polished, human-readable names
 * for use in visualizations, UI labels, and reports.
 * 
 * This mirrors the Python configuration in server/algorithm_names.py
 */

export const ALGORITHM_NAMES: Record<string, string> = {
  // Transformers (Filters)
  'gaussian_filter': 'Gaussian Filter',
  'median_filter': 'Median Filter',
  'mean_filter': 'Mean Filter',
  'min_filter': 'Min Filter',
  'max_filter': 'Max Filter',
  'moving_average': 'Moving Average',
  'savitzky_golay_filter': 'Savitzky-Golay',
  'butterworth_filter': 'Butterworth',
  'fft_cutoff_filter': 'FFT Cutoff',
  'chebyshev_filter': 'Chebyshev',
  'elliptical_filter': 'Elliptical',
  
  // Reducers (Downsamplers)
  'lttb_downsample': 'LTTB',
  'm4_downsample': 'M4',
  'rdp_downsample': 'Douglas-Peucker',
  'minmaxlttb_downsample': 'MinMaxLTTB',
  'uniform_subsample': 'Uniform Subsample',
  'fpcs_downsample': 'FPCS',
  'tda_downsample': 'TopoLines',
  
  // Aggregators
  'asap_aggregator': 'ASAP',
  'bin_average_aggregator': 'PAA',
};

/**
 * Get the polished display name for an algorithm.
 * Falls back to title-cased version if not found.
 */
export function getAlgorithmName(algorithmId: string): string {
  return ALGORITHM_NAMES[algorithmId] || algorithmId.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Get all algorithm name mappings.
 */
export function getAllAlgorithmNames(): Record<string, string> {
  return { ...ALGORITHM_NAMES };
}

// Reverse mapping: display name -> algorithm ID
const NAME_TO_ID: Record<string, string> = Object.fromEntries(
  Object.entries(ALGORITHM_NAMES).map(([id, name]) => [name, id])
);

/**
 * Get the internal algorithm ID from a display name.
 */
export function getAlgorithmId(displayName: string): string {
  return NAME_TO_ID[displayName] || displayName.toLowerCase().replace(/ /g, '_');
}
