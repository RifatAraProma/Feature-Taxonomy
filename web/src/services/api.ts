/**
 * API Service Layer
 * Centralized module for all backend API calls
 */

import type { FeatureScales } from '../types/scales';

const API_BASE = import.meta.env.VITE_API_URL || '';  // Railway backend URL from environment

/**
 * Fetch global feature preservation scales for a dataset
 * @param datasetId - The dataset identifier (e.g., 'stock_aapl_price')
 * @returns Promise resolving to feature scales object
 */
export async function fetchFeatureScales(datasetId: string): Promise<FeatureScales | null> {
  try {
    console.log(`[API] Fetching feature scales for dataset: ${datasetId}`);
    
    const response = await fetch(`${API_BASE}/precomputed/${datasetId}/feature-scales`);
    
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
    console.error(`[API] Error fetching feature scales:`, error);
    return null;
  }
}

/**
 * Fetch precomputed algorithm metadata and outputs
 * @param datasetId - The dataset identifier
 * @param algorithm - The algorithm name
 * @returns Promise resolving to algorithm data
 */
export async function fetchPrecomputedAlgorithm(datasetId: string, algorithm: string): Promise<any> {
  try {
    console.log(`[API] Fetching precomputed data for ${datasetId}/${algorithm}`);
    
    const response = await fetch(`${API_BASE}/precomputed/${datasetId}/${algorithm}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded precomputed data for ${algorithm}`);
    return data;
  } catch (error) {
    console.error(`[API] Error fetching precomputed algorithm data:`, error);
    throw error;
  }
}

/**
 * Smooth a time series using specified algorithm and parameters
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
    console.log(`[API] Smoothing time series:`, request);
    
    const response = await fetch(`${API_BASE}/smooth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Smoothing complete`);
    return data;
  } catch (error) {
    console.error(`[API] Error smoothing time series:`, error);
    throw error;
  }
}

/**
 * Fetch available datasets
 * @returns Promise resolving to list of dataset IDs
 */
export async function fetchDatasets(): Promise<string[]> {
  try {
    console.log(`[API] Fetching available datasets`);
    
    const response = await fetch(`${API_BASE}/datasets`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✅ Loaded ${data.length} datasets`);
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
