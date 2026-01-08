/**
 * API Service Layer
 * Centralized module for all backend API calls
 */

import type { FeatureScales } from '../types/scales';
import { CDN_BASE_URL } from '../config/cdn';

// Deprecated: No longer using Railway backend - fetching everything from CDN
// const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Fetch global feature preservation scales for a dataset
 * @param datasetId - The dataset identifier (e.g., 'stock_aapl_price')
 * @returns Promise resolving to feature scales object
 */
export async function fetchFeatureScales(datasetId: string): Promise<FeatureScales | null> {
  try {
    console.log(`[API] Fetching feature scales for dataset: ${datasetId} from CDN`);
    
    // Fetch from CDN instead of Railway backend
    const response = await fetch(`${CDN_BASE_URL}/precomputed/${datasetId}/_feature_scales.json`);
    
    console.log(`[API] Feature scales response status: ${response.status}`);
    
    if (!response.ok) {
      console.warn(`[API] Failed to fetch feature scales (${response.status})`);
      return null;
    }
    
    const data = await response.json();
    console.log(`[API] Received feature scales data:`, data);
    
    if (data && data.scales) {
      console.log(`[API] ========================================`);
      console.log(`[API] ✅ Successfully loaded scales for ${datasetId}`);
      console.log(`[API] Available metrics:`, Object.keys(data.scales));
      console.log(`[API] level_l1:`, data.scales.level_l1);
      console.log(`[API] level_linf:`, data.scales.level_linf);
      console.log(`[API] mean_delta:`, data.scales.mean_delta);
      console.log(`[API] ========================================`);
      return data.scales;
    } else {
      console.warn(`[API] No scales found in response data`);
      return null;
    }
  } catch (error) {
    // Silently fail on CORS errors - CDN may not have CORS configured
    // Only log if it's not a fetch/network error
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.log(`[API] Feature scales not available (CORS/network issue) - using defaults`);
    } else {
      console.error(`[API] Error fetching feature scales:`, error);
    }
    return null;
  }
}

/**
 * Fetch precomputed algorithm metadata and outputs from CDN
 * @param datasetId - The dataset identifier
 * @param algorithm - The algorithm name
 * @returns Promise resolving to algorithm data
 */
export async function fetchPrecomputedAlgorithm(datasetId: string, algorithm: string): Promise<any> {
  try {
    console.log(`[API] Fetching precomputed data for ${datasetId}/${algorithm} from CDN`);
    
    // Fetch from CDN instead of Railway backend
    const response = await fetch(`${CDN_BASE_URL}/precomputed/${datasetId}/${algorithm}_metadata.json`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded precomputed data for ${algorithm} from CDN`);
    return data;
  } catch (error) {
    console.error(`[API] Error fetching precomputed algorithm data:`, error);
    throw error;
  }
}

/**
 * Fetch precomputed smoothed data from CDN (no runtime computation)
 * @param request - Smoothing request parameters
 * @returns Promise resolving to smoothed data and metrics
 */
export async function smoothTimeSeries(request: {
  seriesId: string;
  method: string;
  sliderLevel?: number;
  usePrecomputed?: boolean;
  returnFeatures?: string[];
  params?: Record<string, any>;
}): Promise<any> {
  try {
    console.log(`[API] Fetching precomputed smoothed data from CDN:`, request);
    
    // Fetch precomputed data from CDN instead of computing at runtime
    const level = request.sliderLevel ?? 0;
    const url = `${CDN_BASE_URL}/precomputed/${request.seriesId}/${request.method}_level_${level}.json`;
    
    console.log(`[API] Fetching: ${url}`);
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded precomputed smoothed data from CDN`);
    return data;
  } catch (error) {
    console.error(`[API] Error fetching precomputed smoothed data:`, error);
    throw error;
  }
}

/**
 * Fetch available datasets from CDN
 * @returns Promise resolving to list of dataset IDs
 */
export async function fetchDatasets(): Promise<string[]> {
  try {
    console.log(`[API] Fetching available datasets from CDN`);
    
    // Fetch from CDN instead of Railway backend
    const response = await fetch(`${CDN_BASE_URL}/datasets.json`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded ${data.length} datasets from CDN`);
    return data;
  } catch (error) {
    console.error(`[API] Error fetching datasets:`, error);
    throw error;
  }
}

/**
 * Fetch available algorithms
 * @returns Promise resolving to list of algorithm names
 */
export async function fetchAlgorithms(): Promise<string[]> {
  try {
    console.log(`[API] Fetching available algorithms`);
    
    const response = await fetch(`${API_BASE}/algorithms`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded ${data.length} algorithms`);
    return data;
  } catch (error) {
    console.error(`[API] Error fetching algorithms:`, error);
    throw error;
  }
}
