import { getPrecomputedUrl, CDN_BASE_URL } from './config/cdn';

// Detect if running locally (development) or in production
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

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
  
  // Production: fetch from CDN
  try {
    const cdnUrl = `${CDN_BASE_URL}/data/${id}.json`;
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
    console.warn(`[API] CDN fetch failed`);
  }
  
  // Fallback: Try to infer category and fetch from CDN with category path
  const categories = ['astro', 'chi_homicide', 'climate_awnd', 'climate_prcp', 'climate_tmax', 
                      'eeg_10000', 'eeg_2500', 'eeg_500', 'flights', 'nz_tourist', 
                      'stock_price', 'stock_volume', 'unemployment'];
  
  for (const cat of categories) {
    if (id.startsWith(cat) || id.includes(cat)) {
      try {
        const cdnUrl = `${CDN_BASE_URL}/data/${cat}/${id}.json`;
        console.log(`[API] Trying CDN with category: ${cdnUrl}`);
        const r = await fetch(cdnUrl);
        if (r.ok) {
          const data = await r.json();
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
  // Production: fetch from CDN
  if (isLocal) {
    const r = await fetch(`/precomputed/${seriesId}/${algorithm}`);
    if (!r.ok) {
      return { available: false };
    }
    return r.json();
  }
  
  // Production: fetch from CDN
  const cdnUrl = getPrecomputedUrl(seriesId, algorithm);
  const r = await fetch(cdnUrl);
  if (!r.ok) {
    return { available: false };
  }
  return r.json();
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
  return r.json();
}
