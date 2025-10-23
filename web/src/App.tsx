import React, {useEffect, useState} from 'react'
import DatasetPicker from './components/DatasetPicker'
import Controls from './components/Controls'
import ChartPanel from './components/ChartPanel'
import MetricsBar from './components/MetricsBar'
import { getSeries, postSmooth } from './api'

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

export default function App(){
  const [dataset, setDataset] = useState('series_001')
  const [method, setMethod] = useState('gaussian_filter')
  const [param, setParam] = useState(0)  // Now 0-100 simplification level
  const [orig, setOrig] = useState<{t:number,y:number}[]>([])
  const [smooth, setSmooth] = useState<{t:number,y:number}[]>([])
  const [metrics, setMetrics] = useState<any>(null)
  const [aspect, setAspect] = useState(1.0)
  const [showExtrema, setShowExtrema] = useState(true)
  const [showCpts, setShowCpts] = useState(true)
  const [overlays, setOverlays] = useState<any>({})

  useEffect(()=>{
    getSeries(dataset).then(d => {
      const pts = d.y.map((v:number,i:number)=>({t:i+1,y:v}))
      setOrig(pts)
    })
  }, [dataset])

  useEffect(()=>{
    // Map simplification level (0-100) to algorithm-specific parameters
    // Level 0 = minimal/no change, Level 100 = maximum simplification
    const dataLength = orig.length;
    let params = {};
    
    if (method.includes('filter') && !method.includes('fft') && !method.includes('butterworth') && !method.includes('chebyshev')) {
      if (method === 'gaussian_filter') {
        // sigma: 0 (no smoothing) to dataLength/10 (heavy smoothing)
        const maxSigma = Math.max(10, dataLength / 10);
        params = { sigma: Math.max(0.01, (param / 100) * maxSigma) };
      } else {
        // window_size: 1 (no change) to 51 (heavy smoothing), must be odd
        const windowSize = Math.max(1, Math.floor((param / 100) * 50) * 2 + 1);
        params = { window_size: windowSize };
      }
    } else if (method.includes('butterworth') || method.includes('fft') || method.includes('chebyshev')) {
      // cutoff_freq_normalized: higher param = lower frequency = more filtering
      // 0.5 (no filtering) down to 0.01 (heavy filtering)
      const cutoff = 0.5 - (param / 100) * 0.49;
      params = { cutoff_freq_normalized: cutoff };
    } else if (method.includes('downsample')) {
      // output_length: dataLength (no reduction) down to 50 points (heavy reduction)
      const minPoints = Math.max(50, dataLength * 0.05);
      const outputLength = Math.max(minPoints, Math.floor(dataLength - (param / 100) * (dataLength - minPoints)));
      params = { output_length: outputLength };
    } else if (method === 'asap_aggregator') {
      // max_window: 1 (no aggregation) to 100 (heavy aggregation)
      const maxWindow = Math.max(1, Math.floor(1 + (param / 100) * 99));
      params = { max_window: maxWindow };
    } else if (method === 'bin_average_aggregator') {
      // bins: dataLength (no aggregation) down to 10 bins (heavy aggregation)
      const minBins = 10;
      const bins = Math.max(minBins, Math.floor(dataLength - (param / 100) * (dataLength - minBins)));
      params = { bins: bins };
    } else {
      // Fallback
      params = { w: Math.max(1, Math.floor(1 + (param / 100) * 50)) };
    }
    
    postSmooth({
      seriesId: dataset,
      method: method,
      params: params,
      returnFeatures: [showExtrema?'extrema':null, showCpts?'regimes':''].filter(Boolean),
      banking: true
    }).then(res => {
      setSmooth(res.yhat)
      setAspect(res.banking.aspect || 1.0)
      setMetrics(res.metrics)
      setOverlays({
        extrema: res.features?.extrema || [],
        changePoints: res.features?.changePoints || []
      })
    }).catch(err => {
      console.error('Error applying algorithm:', err);
    })
  }, [dataset, method, param, showExtrema, showCpts, orig])

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      fontFamily: 'Inter, system-ui, sans-serif',
      backgroundColor: '#f5f5f5'
    }}>
      {/* Main Content Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          backgroundColor: '#fff',
          borderBottom: '1px solid #e0e0e0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h1 style={{margin: 0, fontSize: 24, fontWeight: 600, color: '#333'}}>
            Temporal Data Feature Taxonomy
          </h1>
          <p style={{margin: '4px 0 0 0', fontSize: 14, color: '#666'}}>
            Explore and analyze time series data with various algorithms
          </p>
        </div>

        {/* Chart Area */}
        <div style={{
          flex: 1,
          padding: 24,
          overflow: 'auto'
        }}>
          <ChartPanel orig={orig} smooth={smooth} overlays={overlays} aspect={aspect} method={method} />
          <MetricsBar metrics={metrics} />
          <div style={{marginTop: 12, display: 'flex', gap: 16, alignItems: 'center'}}>
            <div style={{fontSize: 13, color: '#666'}}>
              Aspect ratio (45° banking): {aspect.toFixed(2)}
            </div>
            <div style={{
              display: 'flex',
              gap: 16,
              fontSize: 13,
              fontWeight: 500
            }}>
              <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                <div style={{width: 20, height: 3, backgroundColor: '#BDBDBD', opacity: 0.5}}></div>
                <span style={{color: '#666'}}>Original</span>
              </div>
              <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
                <div style={{width: 20, height: 3, backgroundColor: getAlgorithmColor(method)}}></div>
                <span style={{color: '#333'}}>{method.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Right Control Panel */}
      <div style={{
        width: 360,
        backgroundColor: '#fff',
        borderLeft: '1px solid #e0e0e0',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '-2px 0 8px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fafafa'
        }}>
          <h2 style={{margin: 0, fontSize: 18, fontWeight: 600, color: '#333'}}>
            Controls
          </h2>
        </div>
        
        <div style={{
          flex: 1,
          padding: 24,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 24
        }}>
          <DatasetPicker value={dataset} onChange={setDataset} />
          
          <Controls
            dataset={dataset}
            setDataset={setDataset}
            method={method}
            setMethod={setMethod}
            param={param}
            setParam={setParam}
            showExtrema={showExtrema}
            setShowExtrema={setShowExtrema}
            showCpts={showCpts}
            setShowCpts={setShowCpts}
          />
        </div>
      </div>
    </div>
  )
}