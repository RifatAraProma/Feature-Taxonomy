import React, {useEffect, useState} from 'react'
import DatasetPicker from './components/DatasetPicker'
import Controls from './components/Controls'
import ChartPanel from './components/ChartPanel'
import MetricsBar from './components/MetricsBar'
import { getSeries, postSmooth } from './api'

// Algorithm color mapping - cohesive palette with distinct categories
// Using softer, more harmonious colors
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

export default function App(){
  const [dataset, setDataset] = useState('stock_aapl_price')
  const [method, setMethod] = useState('gaussian_filter')
  const [param, setParam] = useState(0)  // Now 0-100 simplification level
  const [orig, setOrig] = useState<{t:number,y:number}[]>([])
  const [smooth, setSmooth] = useState<{t:number,y:number}[]>([])
  const [metrics, setMetrics] = useState<any>(null)
  const [aspect, setAspect] = useState(1.0)
  const [selectedFeature, setSelectedFeature] = useState('none')
  const [overlays, setOverlays] = useState<any>({})
  const [usePAECalibration, setUsePAECalibration] = useState(true)  // Default to true
  const [paeValue, setPaeValue] = useState<number | null>(null)
  
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
    
    // Determine which features to request based on selectedFeature
    let returnFeatures: string[] = [];
    if (selectedFeature !== 'none') {
      // Request all features for complete overlay support
      // The backend will compute all 12+ features
      returnFeatures = [
        'level', 'mean', 'extrema', 'regimes', 'changePoints', 
        'spikes', 'spikesDips', 'trend', 'noise', 
        'slope', 'curvature', 'regression', 
        'periodicity', 'roughness'
      ];
    }
    
    postSmooth({
      seriesId: dataset,
      method: method,
      params: params,
      returnFeatures: returnFeatures,
      banking: true,
      usePAECalibration: usePAECalibration,
      sliderLevel: param  // Pass the raw slider value (0-100)
    }).then(res => {
      setSmooth(res.yhat)
      setAspect(res.banking.aspect || 1.0)
      setMetrics(res.metrics)
      setOverlays(res.features || {})
      setPaeValue(res.pae || null)  // Capture PAE value
    }).catch(err => {
      console.error('Error applying algorithm:', err);
    })
  }, [dataset, method, param, selectedFeature, orig, usePAECalibration])

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
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
            <div>
              <h1 style={{margin: 0, fontSize: 24, fontWeight: 600, color: '#333'}}>
                Temporal Data Feature Taxonomy
              </h1>
              <p style={{margin: '4px 0 0 0', fontSize: 14, color: '#666'}}>
                Explore and analyze time series data with various algorithms
              </p>
            </div>
          </div>
        </div>

        {/* Chart Area */}
        <div style={{
          flex: 1,
          padding: 24,
          overflow: 'auto'
        }}>
          <ChartPanel orig={orig} smooth={smooth} overlays={overlays} aspect={aspect} method={method} selectedFeature={selectedFeature} />
          <MetricsBar metrics={metrics} />
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
            selectedFeature={selectedFeature}
            setSelectedFeature={setSelectedFeature}
            paeValue={paeValue}
          />
        </div>
      </div>
    </div>
  )
}