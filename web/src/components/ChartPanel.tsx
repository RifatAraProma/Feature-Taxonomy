import React, { useEffect, useRef } from 'react'
import embed from 'vega-embed'
import { lineBase } from '../vega/lineBase'
import { 
  overlayExtrema, 
  overlayChangePoints, 
  overlayRegimes, 
  overlaySpikes,
  overlayTrend,
  overlayNoise,
  overlaySlope,
  overlayCurvature,
  overlayRegression,
  overlayLevel,
  overlayMean,
  overlayPeriodicity,
  overlayRoughness,
  prepareFeatureData
} from '../vega/overlayFeatures'

type Props = {
  orig: {t:number,y:number}[],
  smooth: {t:number,y:number}[],
  overlays: any,
  aspect: number,
  method: string,
  selectedFeature: string
}

// Algorithm color mapping - cohesive palette with distinct categories
const getAlgorithmColor = (method: string): string => {
  const colorMap: Record<string, string> = {
    // Transformers - Cool blues and teals
    'gaussian_filter': '#1E88E5',        // Vivid Blue
    'median_filter': '#039BE5',          // Light Blue
    'mean_filter': '#00ACC1',            // Cyan
    'moving_average': '#00897B',         // Teal
    'savitzky_golay_filter': '#43A047',  // Green
    'butterworth_filter': '#7CB342',     // Light Green
    'fft_cutoff_filter': '#C0CA33',      // Lime
    'chebyshev_filter': '#FDD835',       // Yellow
    
    // Reducers - Warm oranges and reds
    'lttb_downsample': '#FB8C00',        // Orange
    'm4_downsample': '#F4511E',          // Deep Orange
    'rdp_downsample': '#E53935',         // Red
    'minmaxlttb_downsample': '#D81B60',  // Pink
    'uniform_subsample_downsample': '#8E24AA', // Purple
    'fpcs_downsample': '#5E35B1',        // Deep Purple
    'tda_downsample': '#3949AB',         // Indigo
    
    // Aggregators - Browns and earth tones
    'asap_aggregator': '#6D4C41',        // Brown
    'bin_average_aggregator': '#8D6E63', // Light Brown
  };
  
  return colorMap[method] || '#9E9E9E'; // Default to Gray if not found
};

export default function ChartPanel({orig, smooth, overlays, aspect, method, selectedFeature}: Props){
  const ref = useRef<HTMLDivElement>(null)
  
  useEffect(()=>{
    if(!ref.current) return;
    
    console.log('ChartPanel overlays:', overlays);
    console.log('ChartPanel selectedFeature:', selectedFeature);
    
    // Get container dimensions - simple fixed size approach
    const W = 800;  // Fixed width that fits well in the layout
    const H = 450;  // Fixed height for consistent display
    
    const base = lineBase(W, H)
    
    const algorithmColor = getAlgorithmColor(method);
    
    // Show original in gray background, simplified series on top
    const layers:any[] = [
      { 
        data: {name:'orig'}, 
        mark: {
          type:'line', 
          color: '#757575',  // Darker gray for original
          strokeWidth: 1.5,
          opacity: 0.5
        } 
      },
      { 
        data: {name:'smooth'}, 
        mark: {
          type:'line',
          color: algorithmColor,
          strokeWidth: 2.5,
          opacity: 1.0
        } 
      },
    ]
    
    // Add overlay based on selected feature
    // Now handling both original (blue) and simplified (orange) features
    let featureOverlays: any[] = [];
    const datasets: any = {
      orig: orig,
      smooth: smooth
    };
    
    console.log('overlays structure:', overlays);
    console.log('selectedFeature:', selectedFeature);
    
    if (selectedFeature !== 'none' && overlays) {
      const origFeatures = overlays.original || {};
      const simpFeatures = overlays.simplified || {};
      
      console.log('origFeatures:', origFeatures);
      console.log('simpFeatures:', simpFeatures);
      
      const processFeature = (features: any, color: string, suffix: string) => {
        const dataName = selectedFeature + suffix;
        
        switch(selectedFeature) {
          case 'level':
            if (features.level?.interval) {
              datasets[dataName] = features.level.interval;
              return overlayLevel(dataName).map((layer: any) => ({
                ...layer,
                mark: {...layer.mark, color: color}
              }));
            }
            break;
          case 'mean':
            if (features.mean?.mu !== undefined) {
              return overlayMean(features.mean.mu).map((layer: any) => ({
                ...layer,
                mark: {...layer.mark, color: color}
              }));
            }
            break;
          case 'extrema':
            if (features.extrema) {
              datasets[dataName] = features.extrema;
              return overlayExtrema(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'changePoints':
            if (features.changePoints) {
              datasets[dataName] = features.changePoints;
              return overlayChangePoints(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'regimes':
            if (features.regimes) {
              datasets[dataName] = features.regimes.map((r: any) => ({
                ...r,
                baselineMin: r.baseline - 0.5,
                baselineMax: r.baseline + 0.5
              }));
              return overlayRegimes(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'spikesDips':
            if (features.spikesDips) {
              datasets[dataName] = features.spikesDips;
              return overlaySpikes(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'trend':
            if (features.trend?.values) {
              datasets[dataName] = features.trend.values.map((v: number, i: number) => ({t: i+1, value: v}));
              return overlayTrend(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'noise':
            if (features.noise?.values) {
              datasets[dataName] = features.noise.values.map((v: number, i: number) => ({t: i+1, value: v}));
              return overlayNoise(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'slope':
            if (features.slope?.values) {
              datasets[dataName] = features.slope.values.map((v: number, i: number) => ({
                t: features.slope.index?.[i] || i+1,
                value: v
              }));
              return overlaySlope(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'curvature':
            if (features.curvature?.values) {
              datasets[dataName] = features.curvature.values.map((v: number, i: number) => ({
                t: features.curvature.index?.[i] || i+2,
                value: v
              }));
              return overlayCurvature(dataName).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'regression':
            if (features.regression) {
              return overlayRegression(smooth, features.regression.alpha || 0, features.regression.beta || 0).map((layer: any) => ({
                ...layer,
                encoding: {
                  ...layer.encoding,
                  color: {value: color}
                }
              }));
            }
            break;
          case 'periodicity':
            if (features.periodicity) {
              return overlayPeriodicity(features.periodicity.period || 0, features.periodicity.dominant_frequency || 0).map((layer: any) => ({
                ...layer,
                mark: {...layer.mark, color: color}
              }));
            }
            break;
          case 'roughness':
            if (features.roughness?.value !== undefined) {
              return overlayRoughness(features.roughness.value).map((layer: any) => ({
                ...layer,
                mark: {...layer.mark, color: color}
              }));
            }
            break;
        }
        return [];
      };
      
      // Add original features in blue
      const origOverlays = processFeature(origFeatures, '#2196F3', '_orig');
      if (origOverlays.length > 0) {
        featureOverlays.push(...origOverlays);
      }
      
      // Add simplified features in orange
      const simpOverlays = processFeature(simpFeatures, '#FF9800', '_simp');
      if (simpOverlays.length > 0) {
        featureOverlays.push(...simpOverlays);
      }
    }
    
    console.log('Feature overlays:', {
      selectedFeature,
      overlayCount: featureOverlays.length,
      datasetKeys: Object.keys(datasets)
    });
    
    // Add feature overlay layers if available
    if (featureOverlays.length > 0) {
      layers.push(...featureOverlays);
    }

    const spec:any = {
      ...base,
      layer: layers,
      datasets: datasets
    }
    
    console.log('Vega spec:', {
      layerCount: layers.length,
      datasetKeys: Object.keys(datasets)
    });
    
    embed(ref.current, spec, {actions:false})
  }, [orig, smooth, overlays, method, selectedFeature])
  
  return <div ref={ref} style={{width: '100%', maxWidth: '900px'}} />
}