import React from 'react'

type Props = {
  dataset: string, setDataset: (v:string)=>void,
  method: string, setMethod: (v:string)=>void,
  param: number, setParam: (v:number)=>void,
  showExtrema: boolean, setShowExtrema:(v:boolean)=>void,
  showCpts: boolean, setShowCpts:(v:boolean)=>void
}

export default function Controls(p: Props){
  // Get parameter label and description based on method
  const getParamInfo = () => {
    if (p.method.includes('filter') && !p.method.includes('fft') && !p.method.includes('butterworth') && !p.method.includes('chebyshev')) {
      if (p.method === 'gaussian_filter') {
        return {
          label: 'Simplification Level',
          description: 'Higher values = more smoothing (larger sigma)'
        };
      }
      return {
        label: 'Simplification Level',
        description: 'Higher values = more smoothing (larger window)'
      };
    } else if (p.method.includes('butterworth') || p.method.includes('fft') || p.method.includes('chebyshev')) {
      return {
        label: 'Simplification Level',
        description: 'Higher values = more low-pass filtering (lower cutoff frequency)'
      };
    } else if (p.method.includes('downsample')) {
      return {
        label: 'Simplification Level',
        description: 'Higher values = more reduction (fewer output points)'
      };
    } else if (p.method.includes('aggregator')) {
      return {
        label: 'Simplification Level',
        description: p.method === 'asap_aggregator' 
          ? 'Higher values = coarser aggregation (larger windows)'
          : 'Higher values = fewer bins (more aggregation)'
      };
    }
    return {
      label: 'Simplification Level',
      description: 'Adjust to control algorithm behavior'
    };
  };
  
  const paramInfo = getParamInfo();
  
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 20}}>
      {/* Algorithm Selection */}
      <div style={{
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderRadius: 8,
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: 14,
          fontWeight: 600,
          color: '#333',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Algorithm
        </h3>
        <select 
          value={p.method} 
          onChange={e=>p.setMethod(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            fontSize: 14,
            borderRadius: 6,
            border: '1px solid #ccc',
            backgroundColor: '#fff',
            cursor: 'pointer'
          }}
        >
          <optgroup label="🔄 Transformers (Smoothers)">
            <option value="gaussian_filter">Gaussian Filter</option>
            <option value="median_filter">Median Filter</option>
            <option value="mean_filter">Mean Filter</option>
            <option value="moving_average">Moving Average</option>
            <option value="savitzky_golay_filter">Savitzky-Golay</option>
            <option value="butterworth_filter">Butterworth Filter</option>
            <option value="fft_cutoff_filter">FFT Cutoff Filter</option>
            <option value="chebyshev_filter">Chebyshev Filter</option>
          </optgroup>
          <optgroup label="📉 Reducers (Downsamplers)">
            <option value="lttb_downsample">LTTB Downsample</option>
            <option value="m4_downsample">M4 Downsample</option>
            <option value="rdp_downsample">RDP (Douglas-Peucker)</option>
            <option value="minmaxlttb_downsample">MinMax LTTB</option>
            <option value="uniform_subsample_downsample">Uniform Subsample</option>
            <option value="fpcs_downsample">FPCS Downsample</option>
            <option value="tda_downsample">TDA Downsample</option>
          </optgroup>
          <optgroup label="📊 Aggregators">
            <option value="asap_aggregator">ASAP Aggregator</option>
            <option value="bin_average_aggregator">Bin Average</option>
          </optgroup>
        </select>
      </div>
      
      {/* Parameter Control */}
      <div style={{
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderRadius: 8,
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: 14,
          fontWeight: 600,
          color: '#333',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          {paramInfo.label}
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
          width: '100%'
        }}>
          <div style={{
            fontSize: 11,
            color: '#888',
            fontWeight: 600,
            minWidth: 28,
            flexShrink: 0
          }}>
            MIN
          </div>
          <input 
            type="range" 
            min={0} 
            max={100} 
            step={1}
            value={p.param} 
            onChange={e=>p.setParam(parseInt(e.target.value))}
            style={{flex: 1, minWidth: 0}}
          />
          <div style={{
            fontSize: 11,
            color: '#888',
            fontWeight: 600,
            minWidth: 28,
            textAlign: 'right',
            flexShrink: 0
          }}>
            MAX
          </div>
          <div style={{
            minWidth: 40,
            width: 40,
            padding: '6px 8px',
            backgroundColor: '#fff',
            border: '1px solid #ccc',
            borderRadius: 4,
            textAlign: 'center',
            fontWeight: 600,
            fontSize: 14,
            flexShrink: 0
          }}>
            {p.param}
          </div>
        </div>
        <div style={{
          fontSize: 12,
          color: '#666',
          lineHeight: 1.4
        }}>
          {paramInfo.description}
        </div>
      </div>
      
      {/* Feature Overlays */}
      <div style={{
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderRadius: 8,
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: 14,
          fontWeight: 600,
          color: '#333',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Feature Overlays
        </h3>
        <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            cursor: 'pointer',
            padding: '8px 12px',
            backgroundColor: p.showExtrema ? '#e3f2fd' : '#fff',
            borderRadius: 6,
            border: `1px solid ${p.showExtrema ? '#1976d2' : '#ccc'}`,
            transition: 'all 0.2s'
          }}>
            <input 
              type="checkbox" 
              checked={p.showExtrema} 
              onChange={e=>p.setShowExtrema(e.target.checked)}
              style={{width: 18, height: 18, cursor: 'pointer'}}
            />
            <span style={{fontSize: 14, fontWeight: 500}}>Show Extrema Points</span>
          </label>
          
          <label style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            cursor: 'pointer',
            padding: '8px 12px',
            backgroundColor: p.showCpts ? '#e3f2fd' : '#fff',
            borderRadius: 6,
            border: `1px solid ${p.showCpts ? '#1976d2' : '#ccc'}`,
            transition: 'all 0.2s'
          }}>
            <input 
              type="checkbox" 
              checked={p.showCpts} 
              onChange={e=>p.setShowCpts(e.target.checked)}
              style={{width: 18, height: 18, cursor: 'pointer'}}
            />
            <span style={{fontSize: 14, fontWeight: 500}}>Show Change Points</span>
          </label>
        </div>
      </div>
    </div>
  )
}
