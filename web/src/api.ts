import { getPrecomputedUrl } from './config/cdn';

export async function getDatasets() {
  const r = await fetch('/datasets'); return r.json();
}
export async function getSeries(id: string) {
  const r = await fetch(`/series/${id}`); return r.json();
}
export async function getPrecomputedInfo(seriesId: string, algorithm: string) {
  // Fetch directly from CDN instead of backend
  const cdnUrl = getPrecomputedUrl(seriesId, algorithm);
  const r = await fetch(cdnUrl);
  if (!r.ok) {
    return { available: false };
  }
  return r.json();
}
export async function postSmooth(body: any) {
  const r = await fetch('/smooth', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  return r.json();
}
