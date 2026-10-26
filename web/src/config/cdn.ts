// Asset locations for precomputed data and plots.
//
// This project used to serve plots and precomputed output from a paid CDN. That
// deployment has been retired; figures and data files are now published for free as
// GitHub Release assets, and the UI runs locally against locally generated output.
//
// Set VITE_CDN_URL to a base URL if you host the assets somewhere yourself.
// With it unset, every asset is read from local paths served by the Flask backend.
export const CDN_BASE_URL = import.meta.env.VITE_CDN_URL || '';

// Where readers download the published figures and data bundles.
export const ARCHIVE_URL = 'https://github.com/RifatAraProma/Feature-Taxonomy/releases/latest';

export const CDN_URLS = {
  precomputed: CDN_BASE_URL ? `${CDN_BASE_URL}/precomputed` : '/precomputed',
  plots: CDN_BASE_URL ? `${CDN_BASE_URL}/plots` : '/plots',
};

// Helper to construct precomputed data URLs
export function getPrecomputedUrl(dataset: string, algorithm: string) {
  return `${CDN_URLS.precomputed}/${dataset}/${algorithm}.json`;
}

export function getPlotUrl(path: string) {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/plots/') ? path.substring(7) : path;

  return `${CDN_URLS.plots}/${cleanPath}`;
}
