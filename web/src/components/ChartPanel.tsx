import React, { useEffect, useRef, useState } from 'react'
import embed from 'vega-embed'
import { lineBase } from '../vega/lineBase'
import { overlayExtrema } from '../vega/overlayExtrema'
import { overlayChangePoints } from '../vega/overlayRegimes'

type Props = {
  orig: {t:number,y:number}[],
  smooth: {t:number,y:number}[],
  overlays: {extrema?: any[], changePoints?: any[]},
  aspect: number,
  method: string
}

// Algorithm color mapping - distinctive colors for each algorithm
const getAlgorithmColor = (method: string): string => {
  const colorMap: Record<string, string> = {
    // Transformers - Blue/Purple tones
    'gaussian_filter': '#2196F3',        // Blue
    'median_filter': '#9C27B0',          // Purple
    'mean_filter': '#3F51B5',            // Indigo
    'moving_average': '#673AB7',         // Deep Purple
    'savitzky_golay_filter': '#00BCD4',  // Cyan
    'butterworth_filter': '#03A9F4',     // Light Blue
    'fft_cutoff_filter': '#006064',      // Dark Cyan
    'chebyshev_filter': '#1A237E',       // Dark Blue
    
    // Reducers - Green/Teal tones
    'lttb_downsample': '#4CAF50',        // Green
    'm4_downsample': '#009688',          // Teal
    'rdp_downsample': '#8BC34A',         // Light Green
    'minmaxlttb_downsample': '#00796B',  // Dark Teal
    'uniform_subsample_downsample': '#558B2F', // Olive Green
    'fpcs_downsample': '#2E7D32',        // Dark Green
    'tda_downsample': '#1B5E20',         // Very Dark Green
    
    // Aggregators - Orange/Red tones
    'asap_aggregator': '#FF5722',        // Deep Orange
    'bin_average_aggregator': '#FF9800', // Orange
  };
  
  return colorMap[method] || '#E91E63'; // Default to Pink if not found
};

export default function ChartPanel({orig, smooth, overlays, aspect, method}: Props){
  const ref = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({width: 800, height: 400})
  
  useEffect(() => {
    if(!ref.current) return;
    
    // Measure the actual available width in the container
    const containerWidth = ref.current.parentElement?.clientWidth || 800;
    // Account for padding (24px on each side from App.tsx)
    const availableWidth = containerWidth - 48;
    const W = Math.max(400, Math.min(availableWidth, 900)); // Cap at 900px for readability
    
    // Height calculation for 45° banking
    // aspect is the median slope (|dy/dx|)
    // For 45° visual angle: physical_height / physical_width = aspect
    const H = Math.max(250, Math.min(Math.round(W * aspect), 600)); // Cap at 600px
    
    setDimensions({width: W, height: H});
  }, []); // Only calculate once on mount, don't change with aspect
  
  useEffect(()=>{
    if(!ref.current) return;
    
    const {width: W, height: H} = dimensions;
    const base = lineBase(W, H)
    
    const algorithmColor = getAlgorithmColor(method);
    
    const layers:any[] = [
      { 
        data: {name:'orig'}, 
        mark: {
          type:'line', 
          color: '#BDBDBD',  // Faint gray for original
          strokeWidth: 1.5,
          opacity: 0.5
        } 
      },
      { 
        data: {name:'smooth'}, 
        mark: {
          type:'line',
          color: algorithmColor,
          strokeWidth: 2.5
        } 
      },
    ]
    
    if(overlays.extrema) layers.push(...overlayExtrema() as any)
    if(overlays.changePoints) layers.push(...overlayChangePoints() as any)

    const spec:any = {
      ...base,
      layer: layers,
      datasets:{
        orig: orig,
        smooth: smooth,
        extrema: overlays.extrema || [],
        changePoints: overlays.changePoints || []
      }
    }
    embed(ref.current, spec, {actions:false})
  }, [orig, smooth, overlays, method, dimensions])
  
  return <div ref={ref} style={{width: '100%', maxWidth: '100%', overflow: 'visible'}} />
}