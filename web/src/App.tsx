import React, {useEffect, useState} from 'react'
import DatasetPicker from './components/DatasetPicker'
import Controls from './components/Controls'
import ChartPanel from './components/ChartPanel'
import MetricsBar from './components/MetricsBar'
import { getSeries, postSmooth, getPrecomputedInfo } from './api'
import { getAlgorithmColor } from './constants/algorithmColors'

export default function App(){
  const [dataset, setDataset] = useState('stock_aapl_price')
  const [method, setMethod] = useState('gaussian_filter')
  const [param, setParam] = useState(0)  // Start at level 0 (highest PAE, least smoothing)
  const [precomputedInfo, setPrecomputedInfo] = useState<any>(null)
  const [precomputedCache, setPrecomputedCache] = useState<any>(null) // Cache all levels
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
    // Load ALL precomputed levels at once for instant slider response
    console.log(`[PRECOMPUTED] Fetching all levels for ${dataset}/${method}`);
    
    getPrecomputedInfo(dataset, method)
      .then(data => {
        if (!data.available) {
          console.log('[PRECOMPUTED] ✗ Not available');
          setPrecomputedCache(null);
          setPrecomputedInfo({ available: false });
          setPaeValue(null);
          return;
        }
        
        console.log(`[PRECOMPUTED] ✓ Loaded ${data.numLevels} levels`);
        console.log(`[PRECOMPUTED] Backend paramName:`, data.paramName);
        console.log(`[PRECOMPUTED] First level data:`, data.allOutputs[0]);
        
        // Convert all outputs to cache format for instant access
        const allLevels: any = {};
        if (data.allOutputs) {
          for (const levelData of data.allOutputs) {
            // Handle both formats:
            // - Transformers: array of y-values [y1, y2, y3, ...]
            // - Reducers: array of [x, y] tuples [[x1, y1], [x2, y2], ...]
            let yhat;
            if (levelData.output && levelData.output.length > 0) {
              if (Array.isArray(levelData.output[0])) {
                // Reducer format: [[x, y], [x, y], ...]
                // x is already 0-indexed, convert to 1-indexed for chart (t starts at 1)
                yhat = levelData.output.map((pair: [number, number]) => ({t: pair[0] + 1, y: pair[1]}));
                console.log(`[DEBUG] Reducer format detected. First 3 pairs:`, levelData.output.slice(0, 3), '→', yhat.slice(0, 3));
              } else {
                // Transformer format: [y, y, y, ...]
                yhat = levelData.output.map((y: number, idx: number) => ({t: idx + 1, y}));
                console.log(`[DEBUG] Transformer format detected. Length: ${levelData.output.length}`);
              }
            } else {
              yhat = [];
            }
            
            allLevels[levelData.level] = {
              yhat: yhat,
              params: {[data.paramName]: levelData.paramValue},
              banking: {aspect: 1.0, heightPx: 0},
              features: {original: {}, simplified: {}},
              metrics: {},
              pae: levelData.pae,
              paramName: data.paramName,
              paramValue: levelData.paramValue
            };
          }
        }
        
        setPrecomputedCache({ allLevels });
        
        // Use current param value, or default to 0 if param is out of range
        const initialLevel = (param >= 0 && param < data.numLevels) ? param : 0;
        
        const paramInfo = allLevels[initialLevel] ? {
          name: allLevels[initialLevel].paramName,
          value: allLevels[initialLevel].paramValue
        } : null;
        
        console.log(`[PRECOMPUTED] Setting parameterInfo for level ${initialLevel}:`, paramInfo);
        
        setPrecomputedInfo({
          available: true,
          numLevels: data.numLevels,
          parameterInfo: paramInfo
        });
        console.log(`[PRECOMPUTED] ✓ Cache populated with ${data.numLevels} levels for instant slider`);
        
        // Set PAE for current level immediately so it's visible right away
        if (allLevels[initialLevel]) {
          setPaeValue(allLevels[initialLevel].pae || null);
        }
        
        if (param > data.numLevels) {
          setParam(data.numLevels);
        }
        if (param < 0) {
          setParam(0);
        }
      })
      .catch(err => {
        console.error('[PRECOMPUTED] ✗ Failed to load:', err);
        setPrecomputedCache(null);
        setPrecomputedInfo({ available: false });
        setPaeValue(null);
      });
  }, [dataset, method])

  useEffect(()=>{
    // If we have precomputed cache, use it instantly (no network call!)
    if (precomputedCache && precomputedCache.allLevels && precomputedCache.allLevels[param]) {
      console.log(`[PRECOMPUTED] ✓ Using cached level ${param}`);
      const cached = precomputedCache.allLevels[param];
      console.log(`[DEBUG] Setting smooth data: ${cached.yhat.length} points, first 3:`, cached.yhat.slice(0, 3));
      setSmooth(cached.yhat);
      setAspect(cached.banking?.aspect || 1.0);
      setMetrics(cached.metrics);
      setOverlays(cached.features || {});
      setPaeValue(cached.pae || null);
      
      // Update parameter info for current level
      setPrecomputedInfo(prev => ({
        ...prev,
        parameterInfo: {
          name: cached.paramName,
          value: cached.paramValue
        }
      }));
      return;
    }
    
    console.log(`[PRECOMPUTED] ✗ Cache miss for level ${param}, making network request`);
    
    // Otherwise, make a network request
    const returnFeatures = [
      'level', 'mean', 'extrema', 'regimes', 'changePoints', 
      'spikes', 'spikesDips', 'trend', 'noise', 
      'slope', 'curvature', 'regression', 
      'periodicity', 'roughness'
    ];
    
    postSmooth({
      seriesId: dataset,
      method: method,
      usePrecomputed: precomputedInfo?.available ?? true,
      sliderLevel: param,
      returnFeatures: returnFeatures,
      banking: true,
      usePAECalibration: usePAECalibration
    }).then(res => {
      setSmooth(res.yhat)
      setAspect(res.banking.aspect || 1.0)
      setMetrics(res.metrics)
      setOverlays(res.features || {})
      setPaeValue(res.pae || null)  // Capture PAE value
    }).catch(err => {
      console.error('Error applying algorithm:', err);
    })
  }, [dataset, method, param, selectedFeature, orig, usePAECalibration, precomputedCache])

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
            precomputedInfo={precomputedInfo}
            origLength={orig.length}
            smoothLength={smooth.length}
            algorithmColor={getAlgorithmColor(method)}
          />
        </div>
      </div>
    </div>
  )
}