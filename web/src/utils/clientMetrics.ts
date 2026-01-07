/**
 * Client-side metric computation for CDN mode
 * Computes basic preservation metrics when backend computation isn't available
 */

export interface BasicMetrics {
  mae: number;
  rmse: number;
  correlation: number;
  lengthRatio: number;
}

/**
 * Compute Mean Absolute Error between original and simplified series
 */
function computeMAE(orig: number[], simp: number[]): number {
  if (orig.length !== simp.length) {
    return NaN;
  }
  const sum = orig.reduce((acc, val, idx) => acc + Math.abs(val - simp[idx]), 0);
  return sum / orig.length;
}

/**
 * Compute Root Mean Squared Error between original and simplified series
 */
function computeRMSE(orig: number[], simp: number[]): number {
  if (orig.length !== simp.length) {
    return NaN;
  }
  const sumSq = orig.reduce((acc, val, idx) => acc + Math.pow(val - simp[idx], 2), 0);
  return Math.sqrt(sumSq / orig.length);
}

/**
 * Compute Pearson correlation between original and simplified series
 */
function computeCorrelation(orig: number[], simp: number[]): number {
  if (orig.length !== simp.length || orig.length === 0) {
    return NaN;
  }
  
  const n = orig.length;
  const meanOrig = orig.reduce((a, b) => a + b, 0) / n;
  const meanSimp = simp.reduce((a, b) => a + b, 0) / n;
  
  let num = 0;
  let denOrig = 0;
  let denSimp = 0;
  
  for (let i = 0; i < n; i++) {
    const diffOrig = orig[i] - meanOrig;
    const diffSimp = simp[i] - meanSimp;
    num += diffOrig * diffSimp;
    denOrig += diffOrig * diffOrig;
    denSimp += diffSimp * diffSimp;
  }
  
  if (denOrig === 0 || denSimp === 0) {
    return NaN;
  }
  
  return num / Math.sqrt(denOrig * denSimp);
}

/**
 * Interpolate reduced data back to original length for metric computation
 */
function interpolateToOriginalLength(
  origData: {t: number, y: number}[], 
  simpData: {t: number, y: number}[]
): number[] {
  if (simpData.length === origData.length) {
    return simpData.map(d => d.y);
  }
  
  // Simple linear interpolation
  const interpolated: number[] = [];
  
  for (let i = 0; i < origData.length; i++) {
    const targetT = origData[i].t;
    
    // Find surrounding points in simplified data
    let leftIdx = 0;
    let rightIdx = simpData.length - 1;
    
    for (let j = 0; j < simpData.length - 1; j++) {
      if (simpData[j].t <= targetT && simpData[j + 1].t >= targetT) {
        leftIdx = j;
        rightIdx = j + 1;
        break;
      }
    }
    
    const left = simpData[leftIdx];
    const right = simpData[rightIdx];
    
    if (left.t === right.t) {
      interpolated.push(left.y);
    } else {
      const ratio = (targetT - left.t) / (right.t - left.t);
      const interpY = left.y + ratio * (right.y - left.y);
      interpolated.push(interpY);
    }
  }
  
  return interpolated;
}

/**
 * Compute basic metrics between original and simplified data
 * Handles both same-length (transformers) and reduced-length (reducers) data
 */
export function computeBasicMetrics(
  origData: {t: number, y: number}[],
  simpData: {t: number, y: number}[]
): BasicMetrics {
  const origY = origData.map(d => d.y);
  
  let simpY: number[];
  if (simpData.length === origData.length) {
    // Same length - direct comparison
    simpY = simpData.map(d => d.y);
  } else {
    // Different length - interpolate to original length
    simpY = interpolateToOriginalLength(origData, simpData);
  }
  
  return {
    mae: computeMAE(origY, simpY),
    rmse: computeRMSE(origY, simpY),
    correlation: computeCorrelation(origY, simpY),
    lengthRatio: simpData.length / origData.length
  };
}
