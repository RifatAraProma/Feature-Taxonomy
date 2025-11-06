export async function getDatasets() {
  const r = await fetch('/datasets'); return r.json();
}
export async function getSeries(id: string) {
  const r = await fetch(`/series/${id}`); return r.json();
}
export async function getPrecomputedInfo(seriesId: string, algorithm: string) {
  const r = await fetch(`/precomputed/${seriesId}/${algorithm}`);
  return r.json();
}
export async function postSmooth(body: any) {
  const r = await fetch('/smooth', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)});
  return r.json();
}
