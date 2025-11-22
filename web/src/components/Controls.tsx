import React from 'react'
import { getAlgorithmColor } from '../constants/algorithmColors'

type Props = {
  dataset: string, setDataset: (v:string)=>void,
  method: string, setMethod: (v:string)=>void,
  param: number, setParam: (v:number)=>void,
  selectedFeature: string, setSelectedFeature: (v:string)=>void,
  paeValue: number | null,
  precomputedInfo?: any,
  origLength?: number,
  smoothLength?: number,
  algorithmColor?: string
}

export default function Controls(p: Props) {
  // Get parameter label and description based on method
  const getParamInfo = () => {
    if (p.method.includes('filter') && !p.method.includes('fft') && !p.method.includes('butterworth') && !p.method.includes('chebyshev') && !p.method.includes('elliptical')) {
      if (p.method === 'gaussian_filter') {
        return {
          label: 'Simplification Level',
          description: 'Higher values = more simplification (larger sigma)'
        };
      }
      return {
        label: 'Simplification Level',
        description: 'Higher values = more simplification (larger window)'
      };
    } else if (p.method.includes('butterworth') || p.method.includes('fft') || p.method.includes('chebyshev') || p.method.includes('elliptical')) {
      return {
        label: 'Simplification Level',
        description: 'Higher values = more low-pass filtering (lower cutoff frequency)'
      };
    } else if (p.method.includes('downsample') || p.method.includes('reducer')) {
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
  
  // Debug: Log precomputedInfo to console
  console.log('precomputedInfo:', p.precomputedInfo);
  
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
          <optgroup label="Window-Based Filters">
            <option value="mean_filter">Mean Filter (sliding window average)</option>
            <option value="median_filter">Median Filter (removes spikes)</option>
            <option value="min_filter">Min Filter (local minima)</option>
            <option value="max_filter">Max Filter (local maxima)</option>
            <option value="savitzky_golay_filter">Savitzky-Golay Filter (polynomial fitting)</option>
          </optgroup>
          <optgroup label="Convolution-Based Filters">
            <option value="gaussian_filter">Gaussian Filter (smooth curves)</option>
          </optgroup>
          <optgroup label="Frequency-Domain Filters">
            <option value="fft_cutoff_filter">FFT Cutoff Filter (frequency window)</option>
          </optgroup>
          <optgroup label="IIR Filters">
            <option value="butterworth_filter">Butterworth Filter (smooth transition)</option>
            <option value="chebyshev_filter">Chebyshev Filter (steep rolloff)</option>
            <option value="elliptical_filter">Elliptical (Cauer) Filter (steepest rolloff)</option>
          </optgroup>
          <optgroup label="Reducers (Downsamplers)">
            <option value="lttb_downsample">LTTB Downsample</option>
            <option value="m4_downsample">M4 Downsample</option>
            <option value="minmaxlttb_downsample">MinMax LTTB</option>
            <option value="rdp_downsample">RDP (Douglas-Peucker)</option>
            <option value="uniform_subsample">Uniform Subsample</option>
            <option value="fpcs_downsample">FPCS Downsample</option>
            <option value="tda_downsample">TDA Downsample</option>
            <option value="median_filter_reducer">Median Filter Reducer</option>
            <option value="min_filter_reducer">Min Filter Reducer</option>
            <option value="max_filter_reducer">Max Filter Reducer</option>
          </optgroup>
          <optgroup label="Aggregators">
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
        
        {/* Data Point Count Display */}
        {p.origLength !== undefined && p.smoothLength !== undefined && (
          <div style={{
            padding: 12,
            backgroundColor: '#F0F4FF',
            border: '2px solid #6C8FFF',
            borderRadius: 6
          }}>
            <div style={{
              fontSize: 11,
              fontWeight: 600,
              color: '#3F51B5',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginBottom: 8
            }}>
              Data Point Compression
            </div>
            
            {/* Get algorithm-specific color */}
            {(() => {
              const algoColor = getAlgorithmColor(p.method);
              console.log('Algorithm Color for', p.method, 'is', algoColor);
              const isReducer = p.smoothLength < p.origLength;
              
              return (
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-around',
                  gap: 8
                }}>
                  {/* Original Points - Dark Gray (neutral) */}
                  <div style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: 10,
                    backgroundColor: '#F5F5F5',
                    border: '2px solid #424242',
                    borderRadius: 6
                  }}>
                    <div style={{
                      fontSize: 11,
                      color: '#424242',
                      fontWeight: 600,
                      marginBottom: 4
                    }}>
                      ORIGINAL
                    </div>
                    <div style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: '#212121'
                    }}>
                      {p.origLength}
                    </div>
                  </div>
                  
                  {/* Arrow / Reduction */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 20,
                    color: '#6C8FFF',
                    fontWeight: 700
                  }}>
                    →
                  </div>
                  
                  {/* Output Points - Algorithm-specific color */}
                  <div style={{
                    flex: 1,
                    textAlign: 'center',
                    padding: 10,
                    backgroundColor: algoColor + '22',  // 22 = 13% opacity
                    border: `2px solid ${algoColor}`,
                    borderRadius: 6
                  }}>
                    <div style={{
                      fontSize: 11,
                      color: algoColor,
                      fontWeight: 600,
                      marginBottom: 4
                    }}>
                      {isReducer ? 'REDUCED' : 'TRANSFORMED'}
                    </div>
                    <div style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: algoColor
                    }}>
                      {p.smoothLength}
                    </div>
                  </div>
                </div>
              );
            })()}
            
            {/* Compression Ratio */}
            <div style={{
              marginTop: 10,
              fontSize: 12,
              color: getAlgorithmColor(p.method),
              textAlign: 'center',
              fontWeight: 600
            }}>
              {p.smoothLength < p.origLength 
                ? `Reduced by ${Math.round(((p.origLength - p.smoothLength) / p.origLength) * 100)}%`
                : `Full Resolution (Transformer)`
              }
            </div>
          </div>
        )}
        
        {/* +/- Button Controls */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          marginBottom: 8,
          width: '100%'
        }}>
          <button
            onClick={() => p.setParam(Math.max(0, p.param - 1))}
            disabled={p.param <= 0}
            style={{
              flex: 1,
              padding: '12px 20px',
              fontSize: 18,
              fontWeight: 700,
              borderRadius: 8,
              border: '2px solid #2196F3',
              backgroundColor: p.param <= 0 ? '#f0f0f0' : '#2196F3',
              color: p.param <= 0 ? '#ccc' : '#fff',
              cursor: p.param <= 0 ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: p.param <= 0 ? 'none' : '0 2px 4px rgba(0,0,0,0.2)'
            }}
            onMouseEnter={(e) => {
              if (p.param > 0) {
                e.currentTarget.style.backgroundColor = '#1976D2';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              if (p.param > 0) {
                e.currentTarget.style.backgroundColor = '#2196F3';
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
          >
            −
          </button>
          
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            minWidth: 80
          }}>
            <span style={{
              fontSize: 10,
              color: '#888',
              fontWeight: 600,
              textTransform: 'uppercase',
              marginBottom: 4
            }}>
              Level
            </span>
            <div style={{
              padding: '8px 16px',
              backgroundColor: '#E3F2FD',
              border: '2px solid #2196F3',
              borderRadius: 8,
              textAlign: 'center',
              fontWeight: 700,
              fontSize: 20,
              color: '#1976D2',
              minWidth: 50
            }}>
              {p.param}
            </div>
            <span style={{
              fontSize: 10,
              color: '#888',
              marginTop: 4
            }}>
              of {p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100}
            </span>
          </div>
          
          <button
            onClick={() => {
              const maxLevel = p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100;
              p.setParam(Math.min(maxLevel, p.param + 1));
            }}
            disabled={p.param >= (p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100)}
            style={{
              flex: 1,
              padding: '12px 20px',
              fontSize: 18,
              fontWeight: 700,
              borderRadius: 8,
              border: '2px solid #2196F3',
              backgroundColor: p.param >= (p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100) ? '#f0f0f0' : '#2196F3',
              color: p.param >= (p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100) ? '#ccc' : '#fff',
              cursor: p.param >= (p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100) ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: p.param >= (p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100) ? 'none' : '0 2px 4px rgba(0,0,0,0.2)'
            }}
            onMouseEnter={(e) => {
              const maxLevel = p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100;
              if (p.param < maxLevel) {
                e.currentTarget.style.backgroundColor = '#1976D2';
                e.currentTarget.style.transform = 'translateY(-1px)';
              }
            }}
            onMouseLeave={(e) => {
              const maxLevel = p.precomputedInfo?.available ? p.precomputedInfo.numLevels : 100;
              if (p.param < maxLevel) {
                e.currentTarget.style.backgroundColor = '#2196F3';
                e.currentTarget.style.transform = 'translateY(0)';
              }
            }}
          >
            +
          </button>
        </div>
        
        {/* Slider */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
          marginTop: 8
        }}>
          <div style={{fontSize: 11, fontWeight: 600, color: '#666'}}>MIN</div>
          <input 
            type="range" 
            min={0} 
            max={p.precomputedInfo?.available ? p.precomputedInfo.numLevels - 1 : 100} 
            value={p.param} 
            onChange={e => p.setParam(parseInt(e.target.value))}
            style={{flex: 1}}
          />
          <div style={{fontSize: 11, fontWeight: 600, color: '#666'}}>MAX</div>
        </div>
        
        <div style={{
          fontSize: 12,
          color: '#666',
          lineHeight: 1.4
        }}>
          {paramInfo.description}
        </div>
        
        {/* PAE Calibration Info */}
        {/* <div style={{
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
        </div> */}
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
            <option value="regimesAndChangePoints">Regimes & Change Points (Combined)</option>
            {/* <option value="changePoints">Change Points Only (Regime Boundaries)</option>
            <option value="regimes">Regimes Only (Mean Plateaus)</option> */}
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
