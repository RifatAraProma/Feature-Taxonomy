export const algorithmColorMap: Record<string, string> = {
  // Transformers - Cool blues and teals (full length output)
  'gaussian_filter': '#1E88E5',        // Vivid Blue
  'median_filter': '#039BE5',          // Light Blue
  'mean_filter': '#00ACC1',            // Cyan
  'min_filter': '#0097A7',             // Dark Cyan
  'max_filter': '#00897B',             // Teal
  'moving_average': '#00897B',         // Teal
  'savitzky_golay_filter': '#43A047',  // Green
  'butterworth_filter': '#7CB342',     // Light Green
  'fft_cutoff_filter': '#a3a80bff',    // Lime
  'chebyshev_filter': '#d8bc07ff',     // Yellow
  'elliptical_filter': '#e5a207ff',    // Amber

  // Reducers - Warm oranges and reds (reduced output)
  'lttb_downsample': '#FB8C00',        // Orange
  'm4_downsample': '#F4511E',          // Deep Orange
  'rdp_downsample': '#E53935',         // Red
  'minmaxlttb_downsample': '#D81B60',  // Pink
  'uniform_subsample': '#8E24AA',      // Purple
  'fpcs_downsample': '#5E35B1',        // Deep Purple
  'tda_downsample': '#3949AB',         // Indigo
  'median_filter_reducer': '#D32F2F',  // Medium Red
  'min_filter_reducer': '#C62828',     // Dark Red
  'max_filter_reducer': '#B71C1C',     // Darker Red
  
  // Aggregators - Browns and earth tones
  'asap_aggregator': '#6D4C41',        // Brown
  'bin_average_aggregator': '#8D6E63', // Light Brown
};

export const getAlgorithmColor = (method: string): string => {
  return algorithmColorMap[method] || '#9E9E9E'; // Default to Gray if not found
};
