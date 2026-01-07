// CDN configuration for accessing precomputed data and plots
export const CDN_BASE_URL = import.meta.env.VITE_CDN_URL || 'https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com';

export const CDN_URLS = {
  precomputed: `${CDN_BASE_URL}/precomputed`,
  plots: `${CDN_BASE_URL}/plots`,
};

// Helper to construct CDN URLs
export function getPrecomputedUrl(dataset: string, algorithm: string) {
  return `${CDN_URLS.precomputed}/${dataset}/${algorithm}.json`;
}

export function getPlotUrl(path: string) {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/plots/') ? path.substring(7) : path;
  return `${CDN_URLS.plots}/${cleanPath}`;
}
