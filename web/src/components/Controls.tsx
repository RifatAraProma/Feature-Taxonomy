import React from 'react'

type Props = {
  dataset: string, setDataset: (v:string)=>void,
  method: string, setMethod: (v:string)=>void,
  param: number, setParam: (v:number)=>void,
  selectedFeature: string, setSelectedFeature: (v:string)=>void,
  paeValue: number | null
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
        {/* Slider Value Display */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 8
        }}>
          <span style={{
            fontSize: 12,
            color: '#666',
            fontWeight: 500
          }}>
            Current Level:
          </span>
          <div style={{
            padding: '6px 12px',
            backgroundColor: '#E3F2FD',
            border: '2px solid #2196F3',
            borderRadius: 6,
            textAlign: 'center',
            fontWeight: 700,
            fontSize: 16,
            color: '#1976D2',
            minWidth: 50
          }}>
            {p.param}
          </div>
        </div>
        
        {/* PAE Value Display */}
        {p.paeValue !== null && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: 8
          }}>
            <span 
              style={{
                fontSize: 12,
                color: '#666',
                fontWeight: 500,
                cursor: 'help'
              }}
              title="Pixel Approximate Entropy - measures visual complexity"
            >
              PAE Value:
            </span>
            <div style={{
              padding: '6px 12px',
              backgroundColor: '#FFF9C4',
              border: '2px solid #FBC02D',
              borderRadius: 6,
              textAlign: 'center',
              fontWeight: 700,
              fontSize: 16,
              color: '#F57F17',
              minWidth: 50
            }}>
              {p.paeValue.toFixed(3)}
            </div>
          </div>
        )}
        
        {/* Slider */}
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
        </div>
        <div style={{
          fontSize: 12,
          color: '#666',
          lineHeight: 1.4
        }}>
          {paramInfo.description}
        </div>
        
        {/* PAE Calibration Info */}
        <div style={{
          marginTop: 12,
          padding: 12,
          backgroundColor: '#FFF9C4',
          borderRadius: 6,
          border: '1px solid #FBC02D'
        }}>
          <div style={{
            fontSize: 12,
            fontWeight: 600,
            color: '#F57F17',
            marginBottom: 4
          }}>
            ⚡ PAE-Based Calibration Active
          </div>
          <div style={{
            fontSize: 11,
            color: '#666',
            lineHeight: 1.4
          }}>
            All algorithms at the same level produce visually similar results (matched by Pixel Approximate Entropy for perceptual equivalence).
          </div>
        </div>
      </div>
      
      {/* Feature Overlay Selection */}
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
          Feature Overlay
        </h3>
        <select 
          value={p.selectedFeature} 
          onChange={e=>p.setSelectedFeature(e.target.value)}
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
          <option value="none">No Overlay</option>
          <optgroup label="Scalar Statistics">
            <option value="level">Level (Point/Interval Values)</option>
            <option value="mean">Mean (Average Value)</option>
          </optgroup>
          <optgroup label="Structural Features">
            <option value="extrema">Local Extrema (Peaks & Valleys)</option>
            <option value="changePoints">Change Points (Regime Boundaries)</option>
            <option value="regimes">Regimes (Mean Plateaus)</option>
            <option value="spikesDips">Spikes & Dips (Outliers)</option>
          </optgroup>
          <optgroup label="Trend & Pattern">
            <option value="trend">Trend (Low-frequency Component)</option>
            <option value="noise">Noise (High-frequency Residual)</option>
            <option value="regression">Regression Line (Linear Fit)</option>
            <option value="periodicity">Periodicity (Frequency Analysis)</option>
          </optgroup>
          <optgroup label="Derivatives & Texture">
            <option value="slope">Slope (Rate of Change)</option>
            <option value="curvature">Curvature (Shape Bending)</option>
            <option value="roughness">Roughness (Variability)</option>
          </optgroup>
        </select>
        <div style={{
          marginTop: 8,
          fontSize: 12,
          color: '#666',
          lineHeight: 1.4
        }}>
          Visualize one feature at a time for clarity
        </div>
      </div>
    </div>
  )
}
