/**
 * Type definitions for feature preservation scales
 */

export interface FrequencyDistribution {
  excellent: number;
  good: number;
  fair: number;
  poor: number;
  total: number;
}

export interface ScaleThresholds {
  type: 'error' | 'ratio' | 'correlation';
  excellent?: number;
  good?: number;
  fair?: number;
  poor?: number;
  min: number;
  max: number;
  distribution?: FrequencyDistribution;
}

export interface FeatureScales {
  [metricName: string]: ScaleThresholds;
}

export interface DynamicThresholds {
  excellent: number;
  good: number;
  fair: number;
  poor?: number;  // Optional for non-correlation metrics
}
