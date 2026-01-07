import { getPrecomputedUrl, CDN_BASE_URL } from './config/cdn';

// Detect if running locally (development) or in production
// Allow forcing CDN mode locally via ?forceCDN=true URL parameter for testing
const urlParams = new URLSearchParams(window.location.search);
const forceCDN = urlParams.get('forceCDN') === 'true';
const isLocal = !forceCDN && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

if (forceCDN) {
  console.log('🔧 [DEV] Forcing CDN mode for local testing');
}

export async function getDatasets() {
  // Local: use Flask backend via Vite proxy
  // Production: use CDN
  const url = isLocal ? '/datasets' : `${CDN_BASE_URL}/datasets.json`;
  const r = await fetch(url); 
  return r.json();
}
export async function getSeries(id: string) {
  // Local: use Flask backend via Vite proxy  
  // Production: use CDN
  if (isLocal) {
    const r = await fetch(`/series/${id}`);
    return r.json();
  }
  
  // Production: fetch from CDN with category path
  // All files are stored as data/{category}/{dataset}.json
  const categories = ['astro', 'chi_homicide', 'climate_awnd', 'climate_prcp', 'climate_tmax', 
                      'eeg_10000', 'eeg_2500', 'eeg_500', 'flights', 'nz_tourist', 
                      'stock_price', 'stock_volume', 'unemployment'];
  
  // Try to infer category from dataset name
  for (const cat of categories) {
    if (id.startsWith(cat) || id.includes(cat.replace(/_/g, '_'))) {
      try {
        const cdnUrl = `${CDN_BASE_URL}/data/${cat}/${id}.json`;
        console.log(`[API] Fetching series from CDN: ${cdnUrl}`);
        const r = await fetch(cdnUrl);
        if (r.ok) {
          const data = await r.json();
          // Handle both formats: {y: [...]} or just [...]
          if (Array.isArray(data)) {
            return { id, y: data };
          }
          return data;
        }
      } catch (e) {
        continue;
      }
    }
  }
  
  throw new Error(`Could not fetch series ${id} from CDN`);
}
export async function getPrecomputedInfo(seriesId: string, algorithm: string) {
  // Local: use Flask backend via Vite proxy
  // Production: return structure indicating CDN-based loading
  if (isLocal) {
    const r = await fetch(`/precomputed/${seriesId}/${algorithm}`);
    if (!r.ok) {
      return { available: false };
    }
    return r.json();
  }
  
  // Production: We don't have a metadata file in CDN, but we know the structure:
  // - 100 levels (0-99)
  // - Files are named: {algorithm}_level_{0-99}.json
  // Return a structure that tells the frontend to fetch levels on-demand
  try {
    // Try to fetch level 0 to verify the algorithm exists
    const testUrl = `${CDN_BASE_URL}/precomputed/${seriesId}/${algorithm}_level_0.json`;
    const testResponse = await fetch(testUrl, { method: 'HEAD' });
    
    if (testResponse.ok) {
      return {
        available: true,
        useCDN: true,  // Flag indicating CDN-based loading
        numLevels: 100,  // Standard structure: 100 levels
        paramName: 'level',  // Generic param name
        paramValues: Array.from({length: 100}, (_, i) => i),  // 0-99
        paeValues: []  // Not available in CDN without metadata
      };
    }
  } catch (e) {
    console.warn(`[API] Could not verify precomputed data for ${seriesId}/${algorithm}`);
  }
  
  return { available: false };
}
export async function postSmooth(body: any) {
  // Local: use Flask backend via Vite proxy
  // Production: fetch precomputed from CDN
  if (isLocal) {
    const r = await fetch('/smooth', {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'}, 
      body: JSON.stringify(body)
    });
    return r.json();
  }
  
  // Production: fetch precomputed data from CDN instead of computing at runtime
  const level = body.sliderLevel ?? 0;
  const url = `${CDN_BASE_URL}/precomputed/${body.seriesId}/${body.method}_level_${level}.json`;
  console.log(`[API] Fetching precomputed: ${url}`);
  const r = await fetch(url);
  if (!r.ok) {
    throw new Error(`Failed to fetch precomputed data: ${r.status} ${r.statusText}`);
  }
  
  const data = await r.json();
  
  // Transform CDN data format to match Flask backend response format
  // CDN format: {output: [...], pae: number, parameter_name: string, parameter_value: any}
  // Expected format: {yhat: [{t, y}], banking: {aspect}, metrics: {}, pae: number}
  
  let yhat;
  if (data.output && data.output.length > 0) {
    if (Array.isArray(data.output[0])) {
      // Reducer format: [[x, y], [x, y], ...]
      yhat = data.output.map((pair: [number, number]) => ({t: pair[0] + 1, y: pair[1]}));
    } else {
      // Transformer format: [y, y, y, ...]
      yhat = data.output.map((y: number, idx: number) => ({t: idx + 1, y}));
    }
  } else {
    yhat = [];
  }
  
  return {
    yhat,
    banking: { aspect: 1.0 },  // Default aspect ratio for CDN data
    metrics: {},  // No metrics in CDN files
    pae: data.pae || null,
    allFeaturesOrig: {},  // No features in CDN files
    allFeaturesSimp: {},  // No features in CDN files
    precomputedInfo: {
      paramName: data.parameter_name,
      paramValue: data.parameter_value
    }
  };
}
