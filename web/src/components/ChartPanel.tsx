import React, { useEffect, useRef, useState } from 'react'
import embed from 'vega-embed'
import { lineBase } from '../vega/lineBase'
import { getAlgorithmColor } from '../constants/algorithmColors'
import './ChartPanel.css'
import { 
  overlayExtrema, 
  overlayChangePoints, 
  overlayRegimes,
  overlayRegimesAndChangePoints, 
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

export default function ChartPanel({orig, smooth, overlays, aspect, method, selectedFeature}: Props){
  const ref = useRef<HTMLDivElement>(null)
  const [origFeatures, setOrigFeatures] = useState<any>(null)
  
  // Fetch original features (level 0) for overlay comparison - only when needed
  useEffect(() => {
    if (selectedFeature !== 'none' && selectedFeature !== 'none') {
      // For now, use whatever is in overlays.original
      // TODO: Could fetch level 0 features here if needed
      setOrigFeatures(overlays?.original || null)
    } else {
      setOrigFeatures(null)
    }
  }, [selectedFeature, overlays])
  
  useEffect(()=>{
    if(!ref.current) return;
    
    console.log('ChartPanel overlays:', overlays);
    console.log('ChartPanel selectedFeature:', selectedFeature);
    
    // Use LineSmooth dimensions for consistency across all charts
    const W = 1000;  // LineSmooth width: 1000px
    const H = 375;   // LineSmooth height: 375px
    
    const base = lineBase(W, H)
    
    const algorithmColor = getAlgorithmColor(method);
    
    // Show original in light gray background, simplified series on top in algorithm color
    const layers:any[] = [
      { 
        data: {name:'orig'}, 
        mark: {
          type:'line', 
          color: '#757575',  // Darker gray for original
          strokeWidth: 3,
          opacity: 0.5
        } 
      },
      { 
        data: {name:'smooth'}, 
        mark: {
          type:'line',
          color: algorithmColor,
          strokeWidth: 3,  // Thicker for better visibility
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
      
      console.log('[ChartPanel] selectedFeature:', selectedFeature);
      console.log('[ChartPanel] origFeatures:', origFeatures);
      console.log('[ChartPanel] simpFeatures:', simpFeatures);
      console.log('[ChartPanel] origFeatures.regimes:', origFeatures.regimes);
      console.log('[ChartPanel] simpFeatures.regimes:', simpFeatures.regimes);
      
      const processFeature = (features: any, color: string, suffix: string) => {
        const dataName = selectedFeature + suffix;
        const seriesType = suffix === '_orig' ? 'original' : 'simplified';
        
        switch(selectedFeature) {
          case 'level':
            // Show vertical lines from each y point down to 0
            const baseData = suffix === '_orig' ? orig : smooth;
            if (baseData && baseData.length > 0) {
              datasets[dataName] = baseData.map((d: any) => ({
                t: d.t,
                y: d.y,
                series: seriesType
              }));
              
              return overlayLevel(dataName, color, seriesType);
            }
            break;
          case 'mean':
            console.log('[ChartPanel] Processing mean feature:', features.mean);
            if (features.mean?.value !== undefined) {
              console.log('[ChartPanel] Creating mean overlay with value:', features.mean.value, 'color:', color, 'series:', seriesType);
              return overlayMean(features.mean.value, color, seriesType);
            } else {
              console.log('[ChartPanel] Mean feature missing or no value property');
              return [];
            }
            break;
          case 'regression':
            console.log('[ChartPanel] Processing regression feature:', features.regression);
            if (features.regression?.slope !== undefined && features.regression?.intercept !== undefined && features.regression?.fitted) {
              console.log('[ChartPanel] Creating regression overlay:', features.regression);
              return overlayRegression(features.regression, color, seriesType);
            } else {
              console.log('[ChartPanel] Regression feature missing or incomplete');
              return [];
            }
            break;
          case 'extrema':
            if (features.extrema) {
              console.log('[ChartPanel] Processing extrema feature:', features.extrema);
              // Combine minima and maxima
              const extremaPoints = [
                ...(features.extrema.minima || []),
                ...(features.extrema.maxima || [])
              ];
              if (extremaPoints.length > 0) {
                datasets[dataName] = extremaPoints.map((e: any) => ({
                  ...e,
                  series: seriesType
                }));
                console.log('[ChartPanel] Creating extrema overlay with', extremaPoints.length, 'points');
                return overlayExtrema(dataName, color, seriesType);
              }
            }
            break;
          case 'changePoints':
            // Change points are nested inside the regimes feature
            const cpRegimesData = features.regimes;
            if (cpRegimesData && (cpRegimesData.change_points_x || cpRegimesData.change_points)) {
              console.log('[ChartPanel] changePoints feature:', cpRegimesData);
              // Use change_points_x (actual x-coordinates) if available, otherwise fall back to indices
              const cpXValues = cpRegimesData.change_points_x || cpRegimesData.change_points;
              if (Array.isArray(cpXValues) && cpXValues.length > 0) {
                // For vertical rules to work, we need to know the y extent
                // Get min/max y from the smooth data
                const yValues = smooth.map(d => d.y);
                const yMin = Math.min(...yValues);
                const yMax = Math.max(...yValues);
                
                // Convert to format expected by overlay: array of {x, yMin, yMax, series}
                datasets[dataName] = cpXValues.map((x: number) => ({
                  x,
                  yMin: yMin,
                  yMax: yMax,
                  series: seriesType
                }));
                console.log('[ChartPanel] changePoints data:', datasets[dataName]);
                // Pass color and seriesType to overlayChangePoints
                return overlayChangePoints(dataName, color, seriesType);
              }
            }
            break;
          case 'regimesAndChangePoints':
            // Show change points as simple vertical dashed lines
            const combinedRegimesData = features.regimes;
            if (combinedRegimesData && (combinedRegimesData.change_points_x || combinedRegimesData.change_points)) {
              console.log('[ChartPanel] regimesAndChangePoints feature:', combinedRegimesData);
              // Use change_points_x (actual x-coordinates) if available, otherwise fall back to indices
              const cpXValues = combinedRegimesData.change_points_x || combinedRegimesData.change_points;
              if (Array.isArray(cpXValues) && cpXValues.length > 0) {
                // For vertical rules to work, we need to know the y extent
                // Get min/max y from the smooth data
                const yValues = smooth.map(d => d.y);
                const yMin = Math.min(...yValues);
                const yMax = Math.max(...yValues);
                
                // Convert to format expected by overlay: array of {x, yMin, yMax, series}
                datasets[dataName] = cpXValues.map((x: number) => ({
                  x,
                  yMin: yMin,
                  yMax: yMax,
                  series: seriesType
                }));
                console.log('[ChartPanel] regimesAndChangePoints data:', datasets[dataName]);
                // Pass color and seriesType to overlayChangePoints
                return overlayChangePoints(dataName, color, seriesType);
              }
            }
            break;
          case 'spikesDips':
            if (features.spikes_dips) {
              console.log('[ChartPanel] Processing spikes_dips feature:', features.spikes_dips);
              // Combine spikes and dips arrays
              const spikesData = (features.spikes_dips.spikes || []).map((s: any) => ({
                x: s.x || s.index + 1,  // Use x-coordinate if available, fallback to index
                y: s.value,
                type: 'spike',
                series: seriesType
              }));
              const dipsData = (features.spikes_dips.dips || []).map((d: any) => ({
                x: d.x || d.index + 1,  // Use x-coordinate if available, fallback to index
                y: d.value,
                type: 'dip',
                series: seriesType
              }));
              const outliers = [...spikesData, ...dipsData];
              if (outliers.length > 0) {
                datasets[dataName] = outliers;
                console.log('[ChartPanel] Creating spikes/dips overlay with', outliers.length, 'points');
                return overlaySpikes(dataName, color, seriesType);
              }
            }
            break;
          case 'trend':
            console.log('[ChartPanel] Processing trend feature:', features.trend);
            if (features.trend?.trend) {
              datasets[dataName] = features.trend.trend.map((v: number, i: number) => ({
                t: i, 
                value: v,
                series: seriesType
              }));
              console.log('[ChartPanel] Creating trend overlay with', features.trend.trend.length, 'points');
              return overlayTrend(dataName, color, seriesType);
            } else {
              console.log('[ChartPanel] Trend feature missing or no trend array');
              return [];
            }
            break;
          case 'noise':
            console.log('[ChartPanel] Processing noise feature:', features.noise);
            if (features.noise?.values) {
              datasets[dataName] = features.noise.values.map((v: number, i: number) => ({
                t: i, 
                value: v,
                series: seriesType
              }));
              console.log('[ChartPanel] Creating noise overlay with', features.noise.values.length, 'points');
              return overlayNoise(dataName, color, seriesType);
            } else {
              console.log('[ChartPanel] Noise feature missing or no values array');
              return [];
            }
            break;
          case 'slope':
            if (features.slope?.values) {
              console.log('[ChartPanel] Processing slope feature:', features.slope);
              // Slope values array has length n-1 (differences between consecutive points)
              datasets[dataName] = features.slope.values.map((v: number, i: number) => ({
                t: i,
                value: v,
                series: seriesType
              }));
              console.log('[ChartPanel] Creating slope overlay with', features.slope.values.length, 'points');
              return overlaySlope(dataName, color, seriesType);
            }
            break;
          case 'curvature':
            if (features.curvature?.values) {
              console.log('[ChartPanel] Processing curvature feature:', features.curvature);
              // Curvature values array has NaN/null at endpoints, valid values for interior points
              // Filter out null values for cleaner visualization
              const curvaturePoints = features.curvature.values
                .map((v: number | null, i: number) => ({
                  t: i,
                  value: v,
                  series: seriesType
                }))
                .filter((p: any) => p.value !== null && !isNaN(p.value));
              
              if (curvaturePoints.length > 0) {
                datasets[dataName] = curvaturePoints;
                console.log('[ChartPanel] Creating curvature overlay with', curvaturePoints.length, 'points');
                return overlayCurvature(dataName, color, seriesType);
              }
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
            console.log('[ChartPanel] Processing periodicity feature:', features.periodicity);
            if (features.periodicity?.periodic_component) {
              datasets[dataName] = features.periodicity.periodic_component.map((v: number, i: number) => ({
                t: i,
                value: v,
                series: seriesType,
                num_periods: features.periodicity.num_periods,
                amplitude: features.periodicity.amplitude
              }));
              console.log('[ChartPanel] Creating periodicity overlay with', features.periodicity.periodic_component.length, 'points');
              return overlayPeriodicity(dataName, color, seriesType);
            } else {
              console.log('[ChartPanel] Periodicity feature missing or no periodic_component array');
              return [];
            }
            break;
          case 'roughness':
            if (features.roughness?.value !== undefined) {
              console.log('[ChartPanel] Processing roughness feature:', features.roughness);
              console.log('[ChartPanel] Creating roughness overlay with value', features.roughness.value);
              return overlayRoughness(features.roughness.value, color, seriesType);
            }
            break;
        }
        return [];
      };
      
      // Add original features in steel blue (high contrast, doesn't conflict with algorithms)
      const origOverlays = processFeature(origFeatures, '#4682B4', '_orig');
      if (origOverlays.length > 0) {
        console.log('[ChartPanel] Adding', origOverlays.length, 'original feature overlays in steel blue');
        featureOverlays.push(...origOverlays);
      }
      
      // Add simplified features in dark orange (high contrast, doesn't conflict with algorithms)
      const simpOverlays = processFeature(simpFeatures, '#FF8C00', '_simp');
      if (simpOverlays.length > 0) {
        console.log('[ChartPanel] Adding', simpOverlays.length, 'simplified feature overlays in dark orange');
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
      
      // Add legend for feature overlays
      const legendItems = [
        {label: 'Original', color: '#4682B4'},      // Steel blue
        {label: 'Simplified', color: '#FF8C00'}     // Dark orange
      ];
      
      datasets.legend = legendItems;
      
      // Add legend layer (positioned below the chart to avoid overlap)
      layers.push({
        data: {name: 'legend'},
        mark: {
          type: 'point',
          filled: true,
          size: 150,  // Larger size for visibility
          shape: 'square'  // Square shape
        },
        encoding: {
          color: {
            field: 'label',
            type: 'nominal',
            scale: {
              domain: legendItems.map(i => i.label),
              range: legendItems.map(i => i.color)
            },
            legend: {
              title: 'Feature Overlay',
              orient: 'bottom',
              direction: 'horizontal',
              titleFontSize: 14,
              labelFontSize: 12,
              symbolSize: 150,  // Match the mark size
              symbolType: 'square',  // Square symbols in legend
              offset: 10
            }
          }
        }
      });
    }

    const spec:any = {
      ...base,
      layer: layers,
      datasets: datasets
    }
    
    console.log('Vega spec:', {
      layerCount: layers.length,
      datasetKeys: Object.keys(datasets),
      layers: layers,
      datasets: datasets
    });
    
    embed(ref.current, spec, {
      actions: {
        export: true,
        source: true,
        compiled: false,
        editor: true
      }
    })
  }, [orig, smooth, overlays, method, selectedFeature])
  
  return <div className="chart-container"><div ref={ref} /></div>
}