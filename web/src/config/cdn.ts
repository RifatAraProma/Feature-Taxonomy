// CDN configuration for accessing precomputed data and plots
export const CDN_BASE_URL = import.meta.env.VITE_CDN_URL || 'https://feature-taxonomy-precomputed.sfo3.cdn.digitaloceanspaces.com';

// Detect if running locally
// Allow forcing CDN mode locally via ?forceCDN=true URL parameter for testing
const urlParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
const forceCDN = urlParams?.get('forceCDN') === 'true';
const isLocal = !forceCDN && typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

export const CDN_URLS = {
  precomputed: `${CDN_BASE_URL}/precomputed`,
  plots: isLocal ? '/plots' : `${CDN_BASE_URL}/plots`,  // Use local plots in dev, CDN in production
};

// Helper to construct CDN URLs
export function getPrecomputedUrl(dataset: string, algorithm: string) {
  return `${CDN_URLS.precomputed}/${dataset}/${algorithm}.json`;
}

export function getPlotUrl(path: string) {
  // Remove leading slash if present
  const cleanPath = path.startsWith('/plots/') ? path.substring(7) : path;
  
  // Local development: use Vite proxy to Flask backend
  if (isLocal) {
    return `/plots/${cleanPath}`;
  }
  
  // Production: use CDN
  return `${CDN_URLS.plots}/${cleanPath}`;
}
