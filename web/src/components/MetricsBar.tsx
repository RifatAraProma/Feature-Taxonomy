import React, { useState, useEffect } from 'react'

// Import SVG icons for features
import levelIcon from '../assets/level-BVrd9aTO.svg'
import meanIcon from '../assets/mean-C4r5Zle_.svg'
import extremaIcon from '../assets/extrema-D8Lyjuiy.svg'
import regimeIcon from '../assets/regime_change_points-DPLc5JL4.svg'
import spikesIcon from '../assets/spikes_dips-C20W9XTv.svg'
import slopeIcon from '../assets/slope--78G2iKV.svg'
import curvatureIcon from '../assets/curvature-qAbKdR2r.svg'
import trendIcon from '../assets/trend-D9yq8e2r.svg'
import noiseIcon from '../assets/noise-DhIzstjx.svg'
import regressionIcon from '../assets/regression_fit-9NEP8li0.svg'
import periodicityIcon from '../assets/periodicity-BxCgNHWG.svg'
import roughnessIcon from '../assets/roughness-CC_JSp_R.svg'

// Import API service
import { fetchFeatureScales } from '../services/api'
import type { FeatureScales } from '../types/scales'

export default function MetricsBar({metrics, datasetId}:{metrics:any, datasetId: string}){
  if(!metrics) return null
  
  const [activeToast, setActiveToast] = useState<string | null>(null);
  const [globalScales, setGlobalScales] = useState<FeatureScales | null>(null);
  
  // Fetch global scales when dataset changes
  useEffect(() => {
    if (!datasetId) {
      console.log(`[MetricsBar] No datasetId provided, skipping scales fetch`);
      return;
    }
    
    // Use API service instead of direct fetch
    fetchFeatureScales(datasetId)
      .then(scales => {
        if (scales) {
          setGlobalScales(scales);
        } else {
          console.log(`[MetricsBar] No scales available for ${datasetId}`);
          setGlobalScales(null);
        }
      })
      .catch(err => {
        console.error(`[MetricsBar] Error loading scales:`, err);
        setGlobalScales(null);
      });
  }, [datasetId]);
  
  const rawFeaturePreservation = metrics.featurePreservation || {};
  
  // DEBUG: Log what we're working with
  console.log('[MetricsBar] Raw featurePreservation keys:', Object.keys(rawFeaturePreservation));
  
  // CRITICAL: Only process valid preservation metric categories
  // Filter out any raw feature data that may have leaked in
  const VALID_PRESERVATION_METRICS = [
    'level', 'mean', 'regimes', 'change_points',
    'extrema', 'spikes_dips',
    'slope', 'curvature',
    'trend', 'noise', 'roughness',
    'periodicity', 'regression'
  ];
  
  const featurePreservation = Object.fromEntries(
    Object.entries(rawFeaturePreservation).filter(([key]) => {
      const isValid = VALID_PRESERVATION_METRICS.includes(key);
      if (!isValid) {
        console.warn(`[MetricsBar] Filtering out invalid metric: ${key}`);
      }
      return isValid;
    })
  );
  
  console.log('[MetricsBar] Filtered featurePreservation keys:', Object.keys(featurePreservation));
  
  // Map feature names to their SVG icons
  const featureIcons: Record<string, string> = {
    level: levelIcon,
    mean: meanIcon,
    extrema: extremaIcon,
    regimes: regimeIcon,
    change_points: regimeIcon,  // Using same icon for change_points
    spikes: spikesIcon,
    slope: slopeIcon,
    curvature: curvatureIcon,
    trend: trendIcon,
    noise: noiseIcon,
    regression: regressionIcon,
    periodicity: periodicityIcon,
    roughness: roughnessIcon
  };
  
  // Group feature preservation metrics by feature
  const groupMetricsByFeature = () => {
    const groups: Record<string, any> = {
      level: {},
      mean: {},
      regimes: {},
      change_points: {},  // Match the actual key from backend
      extrema: {},
      spikes: {},
      slope: {},
      curvature: {},
      trend: {},
      noise: {},
      regression: {},
      periodicity: {},
      roughness: {}
    };
    
    Object.entries(featurePreservation).forEach(([key, value]) => {
      const lowerKey = key.toLowerCase();
      
      // Handle nested objects (e.g., level: {l1: ..., linf: ...})
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        // Flatten the nested object
        Object.entries(value).forEach(([subKey, subValue]) => {
          const fullKey = `${key}_${subKey}`;
          if (lowerKey.includes('level')) groups.level[fullKey] = subValue;
          else if (lowerKey.includes('mean')) groups.mean[fullKey] = subValue;
          else if (key === 'regimes') groups.regimes[fullKey] = subValue;
          else if (key === 'change_points') groups.regimes[fullKey] = subValue; // Merge into regimes group
          else if (lowerKey.includes('extrema')) groups.extrema[fullKey] = subValue;
          else if (lowerKey.includes('spike')) groups.spikes[fullKey] = subValue;
          else if (key === 'slope') groups.slope[fullKey] = subValue;
          else if (lowerKey.includes('curvature')) groups.curvature[fullKey] = subValue;
          else if (lowerKey.includes('trend')) groups.trend[fullKey] = subValue;
          else if (lowerKey.includes('noise')) groups.noise[fullKey] = subValue;
          else if (lowerKey.includes('regression')) groups.regression[fullKey] = subValue;
          else if (lowerKey.includes('periodicity')) groups.periodicity[fullKey] = subValue;
          else if (lowerKey.includes('roughness')) groups.roughness[fullKey] = subValue;
        });
      } else {
        // Handle primitive values
        if (lowerKey.includes('level')) groups.level[key] = value;
        else if (lowerKey.includes('mean')) groups.mean[key] = value;
        else if (key === 'regimes') groups.regimes[key] = value;
        else if (key === 'change_points') groups.regimes[key] = value; // Merge into regimes group
        else if (lowerKey.includes('extrema')) groups.extrema[key] = value;
        else if (lowerKey.includes('spike')) groups.spikes[key] = value;
        else if (lowerKey.includes('slope')) groups.slope[key] = value;
        else if (lowerKey.includes('curvature')) groups.curvature[key] = value;
        else if (lowerKey.includes('trend')) groups.trend[key] = value;
        else if (lowerKey.includes('noise')) groups.noise[key] = value;
        else if (lowerKey.includes('regression')) groups.regression[key] = value;
        else if (lowerKey.includes('periodicity')) groups.periodicity[key] = value;
        else if (lowerKey.includes('roughness')) groups.roughness[key] = value;
      }
    });
    
    // Remove empty groups
    return Object.fromEntries(
      Object.entries(groups).filter(([_, metrics]) => Object.keys(metrics).length > 0)
    );
  };
  
  const groupedFeatureMetrics = groupMetricsByFeature();
  
  // Use precomputed global thresholds if available, otherwise calculate from current view
  const getThresholds = (metricKey: string, featureMetrics: Record<string, any>, metricType: 'error' | 'ratio' | 'correlation', featureName?: string) => {
    // Try to use global scales first - look up by the EXACT metric key
    if (globalScales) {
      // For nested metrics (like slope.l1, level.l1), construct the full key
      const fullKey = featureName ? `${featureName}_${metricKey}` : metricKey;
      
      // Try exact match first
      if (globalScales[metricKey]) {
        const scale = globalScales[metricKey];
        console.log(`[SCALES] Using global scale for ${metricKey}:`, scale);
        return {
          excellent: scale.excellent !== undefined ? scale.excellent : (scale.good !== undefined ? scale.good : 0),
          good: scale.good !== undefined ? scale.good : (scale.fair !== undefined ? scale.fair : 0),
          fair: scale.fair !== undefined ? scale.fair : (scale.poor !== undefined ? scale.poor : 0),
          poor: scale.poor
        };
      }
      
      // Try full key match (e.g., slope_l1, level_l1)
      if (globalScales[fullKey]) {
        const scale = globalScales[fullKey];
        console.log(`[SCALES] Using global scale for ${fullKey} (from ${featureName}.${metricKey}):`, scale);
        return {
          excellent: scale.excellent !== undefined ? scale.excellent : (scale.good !== undefined ? scale.good : 0),
          good: scale.good !== undefined ? scale.good : (scale.fair !== undefined ? scale.fair : 0),
          fair: scale.fair !== undefined ? scale.fair : (scale.poor !== undefined ? scale.poor : 0),
          poor: scale.poor
        };
      }
      
      // Try case-insensitive match
      const matchingKey = Object.keys(globalScales).find(k => k.toLowerCase() === metricKey.toLowerCase() || k.toLowerCase() === fullKey.toLowerCase());
      if (matchingKey) {
        const scale = globalScales[matchingKey];
        console.log(`[SCALES] Using global scale for ${metricKey} (matched ${matchingKey}):`, scale);
        return {
          excellent: scale.excellent !== undefined ? scale.excellent : (scale.good !== undefined ? scale.good : 0),
          good: scale.good !== undefined ? scale.good : (scale.fair !== undefined ? scale.fair : 0),
          fair: scale.fair !== undefined ? scale.fair : (scale.poor !== undefined ? scale.poor : 0),
          poor: scale.poor
        };
      }
      
      console.log(`[SCALES] No global scale found for ${metricKey} or ${fullKey}, falling back to local calculation`);
    }
    
    // Fallback: calculate from current view (old behavior)
    const values = Object.values(featureMetrics).filter(v => typeof v === 'number') as number[];
    if (values.length === 0) return null;
    
    values.sort((a, b) => a - b);
    
    if (metricType === 'error') {
      // For errors: use 25th, 50th, 75th percentiles
      const p25 = values[Math.floor(values.length * 0.25)];
      const p50 = values[Math.floor(values.length * 0.50)];
      const p75 = values[Math.floor(values.length * 0.75)];
      return { excellent: p25, good: p50, fair: p75 };
    } else if (metricType === 'ratio') {
      // For ratios: calculate deviation from 1.0
      const deviations = values.map(v => Math.abs(v - 1.0)).sort((a, b) => a - b);
      const p25 = deviations[Math.floor(deviations.length * 0.25)];
      const p50 = deviations[Math.floor(deviations.length * 0.50)];
      const p75 = deviations[Math.floor(deviations.length * 0.75)];
      return { excellent: p25, good: p50, fair: p75 };
    } else {
      // For correlation: use 25th, 50th, 75th percentiles (but reversed since higher is better)
      const p25 = values[Math.floor(values.length * 0.25)];
      const p50 = values[Math.floor(values.length * 0.50)];
      const p75 = values[Math.floor(values.length * 0.75)];
      return { poor: p25, fair: p50, good: p75 }; // reversed order
    }
  };
  
  // Calculate dynamic thresholds based on actual data distribution (DEPRECATED - kept for fallback)
  const calculateDynamicThresholds = (featureMetrics: Record<string, any>, metricType: 'error' | 'ratio' | 'correlation') => {
    const values = Object.values(featureMetrics).filter(v => typeof v === 'number') as number[];
    if (values.length === 0) return null;
    
    values.sort((a, b) => a - b);
    
    if (metricType === 'error') {
      // For errors: use 25th, 50th, 75th percentiles
      const p25 = values[Math.floor(values.length * 0.25)];
      const p50 = values[Math.floor(values.length * 0.50)];
      const p75 = values[Math.floor(values.length * 0.75)];
      return { excellent: p25, good: p50, fair: p75 };
    } else if (metricType === 'ratio') {
      // For ratios: calculate deviation from 1.0
      const deviations = values.map(v => Math.abs(v - 1.0)).sort((a, b) => a - b);
      const p25 = deviations[Math.floor(deviations.length * 0.25)];
      const p50 = deviations[Math.floor(deviations.length * 0.50)];
      const p75 = deviations[Math.floor(deviations.length * 0.75)];
      return { excellent: p25, good: p50, fair: p75 };
    } else {
      // For correlation: use 25th, 50th, 75th percentiles (but reversed since higher is better)
      const p25 = values[Math.floor(values.length * 0.25)];
      const p50 = values[Math.floor(values.length * 0.50)];
      const p75 = values[Math.floor(values.length * 0.75)];
      return { poor: p25, fair: p50, good: p75 }; // reversed order
    }
  };
  
  // Determine metric type and color scale
  const getMetricType = (key: string): 'error' | 'ratio' | 'correlation' => {
    if (key.includes('error') || key === 'L1' || key === 'Linf' || key.includes('Loss') || 
        key.includes('distance') || key.includes('l1') || key.includes('linf') || key.includes('mae') || key.includes('delta') ||
        key.includes('bottleneck') || key.includes('wasserstein')) {
      return 'error';
    }
    if (key.includes('retention') || key.includes('correlation') || key === 'rho' || key.includes('similarity')) {
      return 'correlation';
    }
    if (key.includes('Ratio') || key.includes('ratio')) {
      return 'ratio';
    }
    return 'correlation'; // Default
  };
  
  // Color coding for metrics with global scales (or dynamic fallback)
  const getColor = (key: string, value: number, featureMetrics: Record<string, any>, featureName?: string) => {
    const type = getMetricType(key);
    const thresholds = getThresholds(key, featureMetrics, type, featureName);
    
    if (!thresholds) {
      // Fallback to gray if no thresholds
      return '#9E9E9E';
    }
    
    if (type === 'error') {
      // Error metrics: lower is better (0 = best)
      if (value <= thresholds.excellent) return '#2E7D32'; // Dark Green - Excellent
      if (value <= thresholds.good) return '#66BB6A'; // Light Green - Good
      if (value <= thresholds.fair) return '#FFA726'; // Orange - Fair
      return '#E53935'; // Red - Poor
    } else if (type === 'ratio') {
      // Ratio metrics: close to 1.0 is best
      const diff = Math.abs(value - 1.0);
      if (diff <= thresholds.excellent) return '#2E7D32'; // Dark Green - Excellent
      if (diff <= thresholds.good) return '#66BB6A'; // Light Green - Good
      if (diff <= thresholds.fair) return '#FFA726'; // Orange - Fair
      return '#E53935'; // Red - Poor
    } else {
      // Correlation/retention metrics: higher is better (1.0 = best)
      if (value >= thresholds.good) return '#2E7D32'; // Dark Green - Excellent
      if (value >= thresholds.fair) return '#66BB6A'; // Light Green - Good
      if (value >= thresholds.poor!) return '#FFA726'; // Orange - Fair
      return '#E53935'; // Red - Poor
    }
  };
  
  // Get color legend for a feature with global thresholds (or dynamic fallback)
  const getColorLegend = (featureMetrics: Record<string, any>, featureName?: string) => {
    // Determine the primary metric type for this feature
    const keys = Object.keys(featureMetrics);
    if (keys.length === 0) return null;
    
    const primaryKey = keys[0];
    const type = getMetricType(primaryKey);
    const thresholds = getThresholds(primaryKey, featureMetrics, type, featureName);
    
    if (!thresholds) return null;
    
    // Safety checks for undefined values
    if (thresholds.excellent === undefined || thresholds.good === undefined || thresholds.fair === undefined) {
      console.warn(`[SCALES] Invalid thresholds for ${primaryKey}:`, thresholds);
      return null;
    }
    
    if (type === 'error') {
      return {
        title: 'Error Scale (Lower is Better) - Global Dataset Scale',
        ranges: [
          { color: '#2E7D32', label: 'Excellent', range: thresholds.excellent === 0 ? `= ${thresholds.excellent.toFixed(3)}` : `≤ ${thresholds.excellent.toFixed(3)}` },
          { color: '#66BB6A', label: 'Good', range: `≤ ${thresholds.good.toFixed(3)}` },
          { color: '#FFA726', label: 'Fair', range: `≤ ${thresholds.fair.toFixed(3)}` },
          { color: '#E53935', label: 'Poor', range: `> ${thresholds.fair.toFixed(3)}` }
        ]
      };
    } else if (type === 'ratio') {
      return {
        title: 'Ratio Scale (1.0 is Perfect) - Global Dataset Scale',
        ranges: [
          { color: '#2E7D32', label: 'Excellent', range: `±${thresholds.excellent.toFixed(3)}` },
          { color: '#66BB6A', label: 'Good', range: `±${thresholds.good.toFixed(3)}` },
          { color: '#FFA726', label: 'Fair', range: `±${thresholds.fair.toFixed(3)}` },
          { color: '#E53935', label: 'Poor', range: `>±${thresholds.fair.toFixed(3)}` }
        ]
      };
    } else {
      // Correlation type needs 'poor' threshold
      if (thresholds.poor === undefined) {
        console.warn(`[SCALES] Missing 'poor' threshold for correlation metric ${primaryKey}:`, thresholds);
        return null;
      }
      return {
        title: 'Preservation Scale (Higher is Better) - Global Dataset Scale',
        ranges: [
          { color: '#2E7D32', label: 'Excellent', range: `≥ ${thresholds.good.toFixed(3)}` },
          { color: '#66BB6A', label: 'Good', range: `≥ ${thresholds.fair.toFixed(3)}` },
          { color: '#FFA726', label: 'Fair', range: `≥ ${thresholds.poor.toFixed(3)}` },
          { color: '#E53935', label: 'Poor', range: `< ${thresholds.poor.toFixed(3)}` }
        ]
      };
    }
  };
  
  // Format metric names for display
  const formatMetricName = (key: string) => {
    // Special handling for L1 and Linf
    if (key.toLowerCase().includes('l1') || key.toLowerCase() === 'l1') {
      return 'L¹ (Average Case)';
    }
    if (key.toLowerCase().includes('linf') || key.toLowerCase() === 'linf') {
      return 'L∞ (Worst Case)';
    }
    // Special handling for topological distance metrics
    if (key.toLowerCase().includes('bottleneck')) {
      return 'Bottleneck (Worst Case)';
    }
    if (key.toLowerCase().includes('wasserstein')) {
      return 'Wasserstein (Average Case)';
    }
    
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  };
  
  // Format feature names for display
  const formatFeatureName = (key: string) => {
    const displayNames: Record<string, string> = {
      'regimes': 'Regimes & Change Points',
      'change_points': 'Change Points',
      'level': 'Level',
      'mean': 'Mean',
      'extrema': 'Extrema',
      'spikes': 'Spikes & Dips',
      'slope': 'Slope',
      'curvature': 'Curvature',
      'trend': 'Trend',
      'noise': 'Noise',
      'regression': 'Regression Fit',
      'periodicity': 'Periodicity',
      'roughness': 'Roughness'
    };
    
    return displayNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  // Get detailed explanation for each metric
  const getMetricExplanation = (key: string): { description: string, formula: string } => {
    const explanations: Record<string, { description: string, formula: string }> = {
      'level_l1': {
        description: 'L1 Distance (Average Case) - Mean absolute error between original and simplified values. Lower is better (0 = perfect preservation).',
        formula: 'L1 = (1/n) × Σ|y_orig[i] - y_simp[i]|'
      },
      'level_linf': {
        description: 'L∞ Distance (Worst Case) - Maximum absolute error at any single point. Lower is better (0 = perfect preservation).',
        formula: 'L∞ = max(|y_orig[i] - y_simp[i]|)'
      },
      
      // Mean metrics (nested under 'mean')
      'mean_mae': {
        description: 'Mean Absolute Error - Absolute difference between the mean values of original and simplified series.',
        formula: 'MAE = |mean(y_orig) - mean(y_simp)|'
      },
      
      // Regime metrics (nested under 'regimes' and 'change_points')
      'regimes_delta': {
        description: 'Regime Count Delta - Absolute difference in number of detected regimes between original and simplified series. Lower is better (0 = perfect preservation).',
        formula: 'Delta = |num_regimes_orig - num_regimes_simp|'
      },
      'change_points_delta': {
        description: 'Change Point Count Delta - Absolute difference in number of detected change points. Lower is better (0 = perfect preservation).',
        formula: 'Delta = |num_changepoints_orig - num_changepoints_simp|'
      },
      // NOTE: L1 and L∞ displacement metrics commented out due to performance concerns
      // Uncomment below if backend computation is re-enabled
      // 'change_points_l1': {
      //   description: 'Change Points L1 Distance (Average Displacement) - Average positional displacement of change points between original and simplified series. Measures how far change points have shifted on average. Lower is better (0 = no displacement).',
      //   formula: 'L1 = (1/n) × Σ|pos_orig[i] - pos_simp[i]|'
      // },
      // 'change_points_linf': {
      //   description: 'Change Points L∞ Distance (Maximum Displacement) - Maximum positional displacement of any change point. Captures worst-case drift in change point locations. Lower is better (0 = no displacement).',
      //   formula: 'L∞ = max|pos_orig[i] - pos_simp[i]|'
      // },
      
      // Standalone preservation metrics
      'extrema': {
        description: 'Extrema Preservation - Topological distances between persistence diagrams of local maxima/minima.',
        formula: 'Bottleneck (L∞) and Wasserstein (L1) distances'
      },
      'extrema_bottleneck': {
        description: 'Extrema Bottleneck Distance - L∞ topological distance measuring worst-case matching between persistence diagrams. Quantifies the maximum distortion of extrema patterns. Lower is better (0 = perfect preservation).',
        formula: 'Bottleneck = max{min{d(p,q) | q ∈ Q}} for p ∈ P'
      },
      'extrema_wasserstein': {
        description: 'Extrema Wasserstein Distance - L1 topological distance measuring average-case matching between persistence diagrams. Quantifies the average distortion of extrema patterns. Lower is better (0 = perfect preservation).',
        formula: 'Wasserstein = min{Σd(p,q)} over all matchings'
      },
      'spikes_dips_bottleneck': {
        description: 'Spikes/Dips Bottleneck Distance - L∞ topological distance measuring worst-case matching between persistence diagrams of outlier points (y > μ+σ or y < μ-σ). Captures maximum distortion of spike/dip patterns. Lower is better (0 = perfect preservation).',
        formula: 'Bottleneck = min{max|p-q|} over all matchings'
      },
      'spikes_dips_wasserstein': {
        description: 'Spikes/Dips Wasserstein Distance - L1 topological distance measuring average-case matching between persistence diagrams of outlier points. Quantifies the average distortion of spike/dip patterns. Lower is better (0 = perfect preservation).',
        formula: 'Wasserstein = min{Σd(p,q)} over all matchings'
      },
      'slope': {
        description: 'Slope Preservation - L1 (average) and L∞ (maximum) distance between consecutive absolute differences (|y[i+1] - y[i]|) of both series. Lower values indicate better preservation of rate-of-change patterns.',
        formula: 'L1 = mean(|slope_orig - slope_simp|), L∞ = max(|slope_orig - slope_simp|)'
      },
      'curvature': {
        description: 'Curvature Preservation - L1 (average) and L∞ (maximum) distance between curvature values (kappa) of both series. Measures how well the bending/shape is preserved.',
        formula: 'κ = |y\'\'| / (1 + (y\')²)^(3/2), L1 = mean(|κ_orig - κ_simp|), L∞ = max(|κ_orig - κ_simp|)'
      },
      'trend': {
        description: 'Trend Preservation - L1 and L∞ distance between low-frequency trend components.',
        formula: 'L1 = Σ|trend_orig - trend_simp|, L∞ = max|trend_orig - trend_simp|'
      },
      'regression': {
        description: 'Regression Fit Preservation - L1 and L∞ distance between fitted regression lines (y = α + βt).',
        formula: 'L1 = Σ|fitted_orig - fitted_simp|, L∞ = max|fitted_orig - fitted_simp|'
      },
      'periodicity': {
        description: 'Periodicity Preservation - Measures amplitude and period differences in periodic patterns.',
        formula: 'Δ_amplitude = |amp_orig - amp_simp|, Δ_period = |period_orig - period_simp|'
      },
      'roughness': {
        description: 'Roughness Preservation - Absolute difference between roughness values. Roughness is the standard deviation of first differences.',
        formula: 'Δ_roughness = |roughness_orig - roughness_simp|'
      },
      'noise': {
        description: 'Noise Preservation - L1 and L∞ distance between high-frequency noise components.',
        formula: 'L1 = Σ|noise_orig - noise_simp|, L∞ = max|noise_orig - noise_simp|'
      }
    };
    
    return explanations[key] || {
      description: 'Metric measuring the preservation of this feature between original and simplified series.',
      formula: 'See documentation for details'
    };
  };
  
  return (
    <div style={{
      marginTop: 100, 
      padding: '20px 24px',
      backgroundColor: '#fff',
      borderRadius: 12,
      border: '1px solid #e0e0e0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
    }}>
      {/* Global Header */}
      <div style={{
        marginBottom: 24,
        paddingBottom: 16,
        borderBottom: '3px solid #FF1493'
      }}>
      </div>
      
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        paddingBottom: 12,
        borderBottom: '2px solid #E0E0E0'
      }}>
        <h2 style={{
          margin: 0, 
          fontSize: 24, 
          fontWeight: 700, 
          color: '#1059c6ff'
        }}>
          Feature Preservation Performance Metrics
        </h2>
        
        {/* Info button for quality scales explanation */}
        <button
          onClick={() => setActiveToast(activeToast === 'scales' ? null : 'scales')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '4px 8px',
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            color: '#FF1493',
            fontSize: 14,
            fontWeight: 600,
            borderRadius: 6,
            transition: 'background-color 0.2s'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#FF149310'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          title="How are quality thresholds calculated?"
        >
          ℹ️ Quality Scales
        </button>
      </div>
      
      {/* Toast for Quality Scales Explanation */}
      {activeToast === 'scales' && (
        <div style={{
          marginBottom: 20,
          padding: '16px 20px',
          backgroundColor: '#FFF0F5',
          border: '2px solid #FF1493',
          borderRadius: 12,
          fontSize: 13,
          lineHeight: 1.6,
          color: '#333'
        }}>
          <div style={{fontWeight: 700, fontSize: 15, marginBottom: 8, color: '#FF1493'}}>
            📊 How Quality Thresholds Are Calculated
          </div>
          <p style={{margin: '0 0 12px 0'}}>
            The <strong>Excellent/Good/Fair/Poor</strong> categories are calculated using <strong>percentile-based statistical analysis</strong> on real algorithm performance:
          </p>
          <ol style={{margin: '0 0 12px 0', paddingLeft: 24}}>
            <li style={{marginBottom: 6}}>
              <strong>Massive dataset collection:</strong> We run all ~19 algorithms at 100 smoothing levels each → <strong>~24,700 metric samples</strong> per dataset
            </li>
            <li style={{marginBottom: 6}}>
              <strong>Statistical analysis:</strong> For each metric (like L¹ error), we sort all values and calculate percentiles:
              <ul style={{marginTop: 4, marginLeft: 16}}>
                <li><strong style={{color: '#2E7D32'}}>Excellent</strong> = ≤ 25th percentile (top 25% of algorithms)</li>
                <li><strong style={{color: '#66BB6A'}}>Good</strong> = ≤ 50th percentile (better than median)</li>
                <li><strong style={{color: '#FFA726'}}>Fair</strong> = ≤ 75th percentile (better than worst 25%)</li>
                <li><strong style={{color: '#E53935'}}>Poor</strong> = &gt; 75th percentile (bottom 25%)</li>
              </ul>
            </li>
            <li style={{marginBottom: 6}}>
              <strong>Example:</strong> For stock_aapl_price L¹ metric, "Excellent" means error ≤ 1.599 because that's what the top 25% of smoothing operations achieved
            </li>
          </ol>
          <div style={{
            marginTop: 12,
            padding: '8px 12px',
            backgroundColor: '#fff',
            borderRadius: 6,
            fontSize: 12,
            fontStyle: 'italic',
            border: '1px solid #FF149330'
          }}>
            ✅ <strong>Why this works:</strong> Thresholds are data-driven (not arbitrary), dataset-specific, and based on what algorithms actually achieve across ~25,000 real smoothing operations.
          </div>
        </div>
      )}
      
      {/* Feature Preservation Metrics */}
      {Object.keys(featurePreservation).length > 0 ? (
        <div>
          <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12}}>
            <button
              onClick={() => setActiveToast(activeToast === 'feature' ? null : 'feature')}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                color: '#2196F3',
                fontSize: 16
              }}
              title="Click for more info"
            >
              ℹ️
            </button>
          </div>
          
          {/* Toast for Feature Preservation Metrics */}
          {activeToast === 'feature' && (
            <div style={{
              marginBottom: 12,
              padding: '12px 16px',
              backgroundColor: '#E3F2FD',
              border: '1px solid #2196F3',
              borderRadius: 8,
              fontSize: 13,
              lineHeight: 1.6,
              color: '#0D47A1'
            }}>
              <strong>Feature Preservation Metrics</strong> measure how well the simplified series maintains important visual features of the original:
              <ul style={{margin: '8px 0 0 0', paddingLeft: 20}}>
                <li><strong>Retention:</strong> Percentage of features retained (e.g., extrema, change points)</li>
                <li><strong>Correlation:</strong> How similar feature values are between original and simplified</li>
                <li><strong>Error/MAE:</strong> Average difference in feature locations or magnitudes</li>
                <li><strong>Ratio:</strong> Ratio of simplified to original feature values</li>
              </ul>
              <div style={{marginTop: 8, fontSize: 12, fontStyle: 'italic'}}>
                Higher values are better for retention/correlation. Lower values are better for errors. Ratios close to 1.0 indicate good preservation.
              </div>
            </div>
          )}
          
          {/* Grouped Feature Metrics */}
          {Object.entries(groupedFeatureMetrics).map(([featureName, featureMetrics], index) => {
            const legend = getColorLegend(featureMetrics as Record<string, any>, featureName);
            
            return (
            <div key={featureName}>
              
              <div style={{marginBottom: 24}}>
              {/* Feature Title */}
              <h4 style={{
                margin: '0 0 16px 0',
                fontSize: 24,
                fontWeight: 700,
                color: '#FF1493',
                letterSpacing: '0.5px',
                textAlign: 'left'
              }}>
                {formatFeatureName(featureName)}
              </h4>
              
              {/* Icon and Content Container */}
              <div style={{
                display: 'flex',
                gap: 32,
                alignItems: 'flex-start'
              }}>
                {/* Feature Icon - Fixed Width */}
                {featureIcons[featureName] && (
                  <div style={{
                    width: 350,
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <img 
                      src={featureIcons[featureName]} 
                      alt={`${featureName} icon`}
                      style={{
                        width: '100%',
                        height: 'auto',
                        maxHeight: 350,
                        objectFit: 'contain'
                      }}
                    />
                  </div>
                )}

                {/* Right Side Content - Flex Grow */}
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 20
                }}>
                  {/* Metrics with Legends and Distribution */}
                  {Object.entries(featureMetrics as Record<string, any>).map(([metricKey, metricValue]) => {
                    const type = getMetricType(metricKey);
                    const legend = getColorLegend({[metricKey]: metricValue}, featureName);
                    const thresholds = getThresholds(metricKey, featureMetrics as Record<string, any>, type, featureName);
                    const explanation = getMetricExplanation(metricKey);
                    
                    if (!legend || !thresholds) return null;
                    
                    // Get scale range for distribution visualization
                    // Try full key first (e.g., slope_l1), then fallback to metricKey
                    const fullKey = `${featureName}_${metricKey}`;
                    const scaleInfo = globalScales?.[fullKey] || globalScales?.[metricKey] || globalScales?.[Object.keys(globalScales).find(k => k.toLowerCase() === metricKey.toLowerCase() || k.toLowerCase() === fullKey.toLowerCase()) || ''];
                    const scaleMin = scaleInfo?.min ?? 0;
                    // Use the actual max value to ensure all values can be displayed without overflow
                    const scaleMax = scaleInfo?.max ?? (thresholds.fair * 1.5);
                    
                    // Helper function to normalize positions to [0, 100]% based on scale range
                    const normalizePosition = (value: number) => {
                      const range = scaleMax - scaleMin;
                      if (range === 0) return 0;
                      return ((value - scaleMin) / range) * 100;
                    };
                    
                    return (
                      <div key={`metric-${metricKey}`} style={{
                        padding: '16px 20px',
                        backgroundColor: '#FAFAFA',
                        borderRadius: 12,
                        border: '2px solid #E0E0E0'
                      }}>
                        {/* Metric Header */}
                        <div style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          marginBottom: 12
                        }}>
                          <div style={{
                            fontSize: 14,
                            fontWeight: 700,
                            color: '#333',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                          }}>
                            {formatMetricName(metricKey)}
                          </div>
                          <div style={{
                            fontSize: 24,
                            fontWeight: 700,
                            color: getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName),
                            padding: '4px 12px',
                            backgroundColor: '#fff',
                            borderRadius: 8,
                            border: `2px solid ${getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName)}`
                          }}>
                            {typeof metricValue === 'number' ? metricValue.toFixed(3) : String(metricValue)}
                          </div>
                        </div>

                        {/* Two Column Layout: Legend | Distribution */}
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr 1fr',
                          gap: 16
                        }}>
                          {/* Left: Color Legend */}
                          <div>
                            <div style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color: '#666',
                              marginBottom: 8,
                              textTransform: 'uppercase'
                            }}>
                              {legend.title}
                            </div>
                            <div style={{
                              display: 'flex',
                              flexDirection: 'column',
                              gap: 6
                            }}>
                              {legend.ranges.map((range, idx) => (
                                <div key={idx} style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  gap: 8
                                }}>
                                  <div style={{
                                    width: 20,
                                    height: 20,
                                    borderRadius: 4,
                                    backgroundColor: range.color,
                                    flexShrink: 0,
                                    border: '1px solid rgba(0,0,0,0.1)'
                                  }} />
                                  <div style={{fontSize: 12, color: '#555', fontWeight: 500}}>
                                    <span style={{fontWeight: 700}}>{range.label}:</span> {range.range}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>

                          {/* Right: Distribution Chart */}
                          <div>
                            <div style={{
                              fontSize: 11,
                              fontWeight: 600,
                              color: '#666',
                              marginBottom: 12,
                              textTransform: 'uppercase'
                            }}>
                              Sample Distribution (Count-Based)
                            </div>
                            
                            {/* Value Distribution Bar - Widths proportional to sample counts */}
                            <div style={{
                              position: 'relative',
                              height: 60,
                              backgroundColor: '#fff',
                              borderRadius: 8,
                              border: '1px solid #E0E0E0',
                              overflow: 'visible',
                              marginBottom: 50,
                              marginTop: 24
                            }}>
                              {(() => {
                                // Get distribution counts from global scales
                                const fullKey = `${featureName}_${metricKey}`;
                                const distribution = scaleInfo?.distribution || globalScales?.[fullKey]?.distribution || globalScales?.[metricKey]?.distribution;
                                
                                // Calculate zone widths based on sample counts (proportional to data points)
                                let excellentWidth = 25, goodWidth = 25, fairWidth = 25, poorWidth = 25; // Default equal widths
                                
                                if (distribution && distribution.total > 0) {
                                  const total = distribution.total;
                                  excellentWidth = (distribution.excellent / total) * 100;
                                  goodWidth = (distribution.good / total) * 100;
                                  fairWidth = (distribution.fair / total) * 100;
                                  poorWidth = (distribution.poor / total) * 100;
                                }
                                
                                // Minimum width threshold for showing labels (in percentage)
                                const MIN_WIDTH_FOR_LABEL = 5;
                                
                                return type === 'error' ? (
                                <>
                                  {/* Excellent zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    width: `${excellentWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#2E7D3230',
                                    borderRight: '2px solid #2E7D32'
                                  }}>
                                    {excellentWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#2E7D32',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #2E7D32',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Excellent
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && excellentWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#2E7D32'
                                      }}>
                                        {distribution.excellent}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      left: 0,
                                      fontSize: 9,
                                      color: '#666'
                                    }}>
                                      0
                                    </div>
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#2E7D32',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.excellent.toFixed(1)}
                                    </div>
                                  </div>
                                  
                                  {/* Good zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${excellentWidth}%`,
                                    top: 0,
                                    width: `${goodWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#66BB6A30',
                                    borderRight: '2px solid #66BB6A'
                                  }}>
                                    {goodWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#66BB6A',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #66BB6A',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Good
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && goodWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#66BB6A'
                                      }}>
                                        {distribution.good}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#66BB6A',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.good.toFixed(1)}
                                    </div>
                                  </div>
                                  
                                  {/* Fair zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${excellentWidth + goodWidth}%`,
                                    top: 0,
                                    width: `${fairWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#FFA72630',
                                    borderRight: '2px solid #FFA726'
                                  }}>
                                    {fairWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#FFA726',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #FFA726',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Fair
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && fairWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#FFA726'
                                      }}>
                                        {distribution.fair}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#FFA726',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.fair.toFixed(1)}
                                    </div>
                                  </div>
                                  
                                  {/* Poor zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${excellentWidth + goodWidth + fairWidth}%`,
                                    top: 0,
                                    width: `${poorWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#E5393530'
                                  }}>
                                    {poorWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#E53935',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #E53935',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Poor
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && poorWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#E53935'
                                      }}>
                                        {distribution.poor}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: 0,
                                      fontSize: 9,
                                      color: '#666'
                                    }}>
                                      {scaleMax.toFixed(1)}
                                    </div>
                                  </div>
                                  
                                  {/* Current value indicator - position based on quality zone */}
                                  {(() => {
                                    // Calculate position within the appropriate zone
                                    let zoneLeft = 0;
                                    let zoneWidth = 0;
                                    let positionInZone = 0.5; // Default to middle of zone
                                    
                                    if (metricValue <= thresholds.excellent) {
                                      // Excellent zone
                                      zoneLeft = 0;
                                      zoneWidth = excellentWidth;
                                      positionInZone = thresholds.excellent > 0 ? (metricValue / thresholds.excellent) : 0.5;
                                    } else if (metricValue <= thresholds.good) {
                                      // Good zone
                                      zoneLeft = excellentWidth;
                                      zoneWidth = goodWidth;
                                      positionInZone = (metricValue - thresholds.excellent) / (thresholds.good - thresholds.excellent);
                                    } else if (metricValue <= thresholds.fair) {
                                      // Fair zone
                                      zoneLeft = excellentWidth + goodWidth;
                                      zoneWidth = fairWidth;
                                      positionInZone = (metricValue - thresholds.good) / (thresholds.fair - thresholds.good);
                                    } else {
                                      // Poor zone
                                      zoneLeft = excellentWidth + goodWidth + fairWidth;
                                      zoneWidth = poorWidth;
                                      positionInZone = Math.min((metricValue - thresholds.fair) / (scaleMax - thresholds.fair), 1);
                                    }
                                    
                                    const indicatorPosition = zoneLeft + (zoneWidth * positionInZone);
                                    
                                    return (
                                      <>
                                        <div style={{
                                          position: 'absolute',
                                          left: `${indicatorPosition}%`,
                                          top: 0,
                                          width: 3,
                                          height: '100%',
                                          backgroundColor: getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName),
                                          boxShadow: '0 0 6px rgba(0,0,0,0.4)',
                                          zIndex: 10
                                        }} />
                                        
                                        <div style={{
                                          position: 'absolute',
                                          left: `${indicatorPosition}%`,
                                          top: '50%',
                                          transform: 'translate(-50%, -50%)',
                                          backgroundColor: getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName),
                                          color: '#fff',
                                          padding: '3px 10px',
                                          borderRadius: 4,
                                          fontSize: 11,
                                          fontWeight: 700,
                                          whiteSpace: 'nowrap',
                                          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                          zIndex: 11
                                        }}>
                                          {metricValue.toFixed(2)}
                                        </div>
                                      </>
                                    );
                                  })()}
                                </>
                              ) : type === 'correlation' && thresholds.poor !== undefined ? (
                                <>
                                  {/* For correlation: reversed order (poor → fair → good → excellent) */}
                                  {/* Poor zone (lowest correlations) */}
                                  <div style={{
                                    position: 'absolute',
                                    left: 0,
                                    top: 0,
                                    width: `${poorWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#E5393530',
                                    borderRight: '2px solid #E53935'
                                  }}>
                                    {poorWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#E53935',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #E53935',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Poor
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && poorWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#E53935'
                                      }}>
                                        {distribution.poor}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      left: 0,
                                      fontSize: 9,
                                      color: '#666'
                                    }}>
                                      0
                                    </div>
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#E53935',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.poor.toFixed(2)}
                                    </div>
                                  </div>
                                  
                                  {/* Fair zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${poorWidth}%`,
                                    top: 0,
                                    width: `${fairWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#FFA72630',
                                    borderRight: '2px solid #FFA726'
                                  }}>
                                    {fairWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#FFA726',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #FFA726',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Fair
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && fairWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#FFA726'
                                      }}>
                                        {distribution.fair}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#FFA726',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.fair.toFixed(2)}
                                    </div>
                                  </div>
                                  
                                  {/* Good zone */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${poorWidth + fairWidth}%`,
                                    top: 0,
                                    width: `${goodWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#66BB6A30',
                                    borderRight: '2px solid #66BB6A'
                                  }}>
                                    {goodWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#66BB6A',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #66BB6A',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Good
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && goodWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#66BB6A'
                                      }}>
                                        {distribution.good}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: -10,
                                      fontSize: 10,
                                      color: '#66BB6A',
                                      fontWeight: 700
                                    }}>
                                      {thresholds.good.toFixed(2)}
                                    </div>
                                  </div>
                                  
                                  {/* Excellent zone (highest correlations) */}
                                  <div style={{
                                    position: 'absolute',
                                    left: `${poorWidth + fairWidth + goodWidth}%`,
                                    top: 0,
                                    width: `${excellentWidth}%`,
                                    height: '100%',
                                    backgroundColor: '#2E7D3230'
                                  }}>
                                    {excellentWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: -20,
                                        left: '50%',
                                        transform: 'translateX(-50%)',
                                        fontSize: 9,
                                        fontWeight: 700,
                                        color: '#2E7D32',
                                        backgroundColor: '#fff',
                                        padding: '2px 6px',
                                        borderRadius: 3,
                                        border: '1px solid #2E7D32',
                                        whiteSpace: 'nowrap'
                                      }}>
                                        Excellent
                                      </div>
                                    )}
                                    {/* Show count inside the box */}
                                    {distribution && excellentWidth >= MIN_WIDTH_FOR_LABEL && (
                                      <div style={{
                                        position: 'absolute',
                                        top: '50%',
                                        left: '50%',
                                        transform: 'translate(-50%, -50%)',
                                        fontSize: 11,
                                        fontWeight: 700,
                                        color: '#2E7D32'
                                      }}>
                                        {distribution.excellent}
                                      </div>
                                    )}
                                    <div style={{
                                      position: 'absolute',
                                      bottom: -32,
                                      right: 0,
                                      fontSize: 9,
                                      color: '#666'
                                    }}>
                                      {scaleMax.toFixed(2)}
                                    </div>
                                  </div>
                                  
                                  {/* Current value indicator - position based on quality zone (correlation) */}
                                  {(() => {
                                    // For correlation: reversed zones (poor → fair → good → excellent)
                                    let zoneLeft = 0;
                                    let zoneWidth = 0;
                                    let positionInZone = 0.5; // Default to middle of zone
                                    
                                    if (metricValue < thresholds.poor!) {
                                      // Poor zone (lowest correlations)
                                      zoneLeft = 0;
                                      zoneWidth = poorWidth;
                                      positionInZone = thresholds.poor! > 0 ? (metricValue / thresholds.poor!) : 0.5;
                                    } else if (metricValue < thresholds.fair) {
                                      // Fair zone
                                      zoneLeft = poorWidth;
                                      zoneWidth = fairWidth;
                                      positionInZone = (metricValue - thresholds.poor!) / (thresholds.fair - thresholds.poor!);
                                    } else if (metricValue < thresholds.good) {
                                      // Good zone
                                      zoneLeft = poorWidth + fairWidth;
                                      zoneWidth = goodWidth;
                                      positionInZone = (metricValue - thresholds.fair) / (thresholds.good - thresholds.fair);
                                    } else {
                                      // Excellent zone (highest correlations)
                                      zoneLeft = poorWidth + fairWidth + goodWidth;
                                      zoneWidth = excellentWidth;
                                      positionInZone = Math.min((metricValue - thresholds.good) / (scaleMax - thresholds.good), 1);
                                    }
                                    
                                    const indicatorPosition = zoneLeft + (zoneWidth * positionInZone);
                                    
                                    return (
                                      <>
                                        <div style={{
                                          position: 'absolute',
                                          left: `${indicatorPosition}%`,
                                          top: 0,
                                          width: 3,
                                          height: '100%',
                                          backgroundColor: getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName),
                                          boxShadow: '0 0 6px rgba(0,0,0,0.4)',
                                          zIndex: 10
                                        }} />
                                        
                                        <div style={{
                                          position: 'absolute',
                                          left: `${indicatorPosition}%`,
                                          top: '50%',
                                          transform: 'translate(-50%, -50%)',
                                          backgroundColor: getColor(metricKey, metricValue as number, featureMetrics as Record<string, any>, featureName),
                                          color: '#fff',
                                          padding: '3px 10px',
                                          borderRadius: 4,
                                          fontSize: 11,
                                          fontWeight: 700,
                                          whiteSpace: 'nowrap',
                                          boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                                          zIndex: 11
                                        }}>
                                          {metricValue.toFixed(2)}
                                        </div>
                                      </>
                                    );
                                  })()}
                                </>
                              ) : null;
                              })()}
                            </div>
                            
                            {/* Metric explanation */}
                            <div style={{
                              marginTop: 20,
                              fontSize: 11,
                              color: '#666',
                              lineHeight: 1.4
                            }}>
                              {explanation.description}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              </div>
              
              {/* Divider (except after last feature) */}
              {index < Object.entries(groupedFeatureMetrics).length - 1 && (
                <hr style={{
                  border: 'none',
                  borderTop: '2px solid #E0E0E0',
                  margin: '0px 0 24px 0',
                  opacity: 0.5
                }} />
              )}
            </div>
            );
          })}
        </div>
      ) : (
        <div style={{
          padding: '40px 20px',
          textAlign: 'center',
          color: '#999',
          fontSize: 14
        }}>
          No feature preservation metrics available. Run a smoothing operation to see results.
        </div>
      )}
    </div>
  )
}
