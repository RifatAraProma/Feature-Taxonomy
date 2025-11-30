import React, {useEffect, useState} from 'react'
import DatasetPicker from './components/DatasetPicker'
import Controls from './components/Controls'
import ChartPanel from './components/ChartPanel'
import MetricsBar from './components/MetricsBar'
import PlotsGallery from './components/PlotsGallery'
import OriginalPlotsGallery from './components/OriginalPlotsGallery'
import PrecomputedPlotsGallery from './components/PrecomputedPlotsGallery'
import RankingsViewer from './components/RankingsViewer'
import { getSeries, postSmooth, getPrecomputedInfo } from './api'
import { getAlgorithmColor } from './constants/algorithmColors'

export default function App(){
  const [activeTab, setActiveTab] = useState<'explorer' | 'plots' | 'original' | 'pae' | 'rankings'>('explorer')
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
        let level0Features = {};  // Store level 0 features to use as "original" for all levels
        
        if (data.allOutputs) {
          for (const levelData of data.allOutputs) {
            // Handle both formats:
            // - Transformers: array of y-values [y1, y2, y3, ...]
            // - Reducers: array of [x, y] tuples [[x1, y1], [x2, y2], ...]
            let yhat;
            let xValues: number[] = [];  // Extract x-coordinates for feature mapping
            
            if (levelData.output && levelData.output.length > 0) {
              if (Array.isArray(levelData.output[0])) {
                // Reducer format: [[x, y], [x, y], ...]
                // x is already 0-indexed, convert to 1-indexed for chart (t starts at 1)
                xValues = levelData.output.map((pair: [number, number]) => pair[0] + 1);
                yhat = levelData.output.map((pair: [number, number]) => ({t: pair[0] + 1, y: pair[1]}));
                console.log(`[DEBUG] Reducer format detected. First 3 pairs:`, levelData.output.slice(0, 3), '→', yhat.slice(0, 3));
              } else {
                // Transformer format: [y, y, y, ...]
                xValues = levelData.output.map((_: number, idx: number) => idx + 1);
                yhat = levelData.output.map((y: number, idx: number) => ({t: idx + 1, y}));
                console.log(`[DEBUG] Transformer format detected. Length: ${levelData.output.length}`);
              }
            } else {
              yhat = [];
            }
            
            // Add x-coordinates to position-dependent features for correct overlay positioning
            const features = levelData.features ? {...levelData.features} : {};
            
            if (features.extrema && xValues.length > 0) {
              // Map extrema indices to actual x-coordinates
              if (features.extrema.minima) {
                features.extrema.minima = features.extrema.minima.map((ext: any) => ({
                  ...ext,
                  x: xValues[ext.t - 1] || ext.t  // t is 1-indexed, xValues is 0-indexed
                }));
              }
              if (features.extrema.maxima) {
                features.extrema.maxima = features.extrema.maxima.map((ext: any) => ({
                  ...ext,
                  x: xValues[ext.t - 1] || ext.t
                }));
              }
            }
            
            if (features.regimes && features.regimes.regimes && xValues.length > 0) {
              // Map regime boundaries to actual x-coordinates
              features.regimes.regimes = features.regimes.regimes.map((regime: any) => ({
                ...regime,
                start_x: xValues[regime.start] || regime.start,
                end_x: xValues[regime.end] || regime.end,
                a: xValues[regime.start] || regime.start,  // For Vega spec compatibility
                b: xValues[regime.end] || regime.end,       // For Vega spec compatibility
                baseline: regime.baseline_mean  // Ensure baseline field exists
              }));
            }
            
            if (features.regimes && features.regimes.change_points && xValues.length > 0) {
              // Store x-coordinates for change points
              features.regimes.change_points_x = features.regimes.change_points.map((idx: number) => 
                xValues[idx] || idx + 1
              );
            }
            
            if (features.spikes_dips && xValues.length > 0) {
              // Map spike/dip indices to actual x-coordinates
              if (features.spikes_dips.spikes) {
                features.spikes_dips.spikes = features.spikes_dips.spikes.map((spike: any) => ({
                  ...spike,
                  x: xValues[spike.index] || spike.index + 1
                }));
              }
              if (features.spikes_dips.dips) {
                features.spikes_dips.dips = features.spikes_dips.dips.map((dip: any) => ({
                  ...dip,
                  x: xValues[dip.index] || dip.index + 1
                }));
              }
            }
            
            // Save level 0 features as the "original" for all levels
            if (levelData.level === 0) {
              level0Features = features;
            }
            
            allLevels[levelData.level] = {
              yhat: yhat,
              params: {[data.paramName]: levelData.paramValue},
              banking: {aspect: 1.0, heightPx: 0},
              features: features,  // Store features with x-coordinates added
              metrics: {
                featurePreservation: levelData.featurePreservation || {}
              },
              pae: levelData.pae,
              paramName: data.paramName,
              paramValue: levelData.paramValue
            };
          }
          
          // Now add "original" (level 0) features to all levels
          for (const level in allLevels) {
            allLevels[level].features = {
              original: level0Features,
              simplified: allLevels[level].features
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
      
      // Check if features exist in cache
      const hasCachedFeatures = cached.features && 
        (Object.keys(cached.features.original || {}).length > 0 || 
         Object.keys(cached.features.simplified || {}).length > 0);
      
      if (hasCachedFeatures) {
        console.log('[PRECOMPUTED] ✓ Using cached features (no network call)');
        setOverlays(cached.features);
      } else if (selectedFeature !== 'none') {
        // Features not in cache but user wants to see them - fetch from backend
        console.log('[PRECOMPUTED] Features missing, fetching from backend for overlay');
        const returnFeatures = [
          'level', 'mean', 'extrema', 'regimes', 'changePoints', 
          'spikes', 'spikesDips', 'trend', 'noise', 
          'slope', 'curvature', 'regression', 
          'periodicity', 'roughness'
        ];
        
        // Fetch features for BOTH the current level AND level 0 (original)
        Promise.all([
          // Current level (simplified)
          postSmooth({
            seriesId: dataset,
            method: method,
            usePrecomputed: true,
            sliderLevel: param,
            returnFeatures: returnFeatures,
            banking: true,
            usePAECalibration: usePAECalibration
          }),
          // Level 0 (original) - only fetch if not already at level 0
          param === 0 ? Promise.resolve(null) : postSmooth({
            seriesId: dataset,
            method: method,
            usePrecomputed: true,
            sliderLevel: 0,
            returnFeatures: returnFeatures,
            banking: true,
            usePAECalibration: usePAECalibration
          })
        ]).then(([currentRes, level0Res]) => {
          setOverlays({
            original: level0Res ? level0Res.allFeaturesSimp : currentRes.allFeaturesOrig,
            simplified: currentRes.allFeaturesSimp || {}
          });
        }).catch(err => {
          console.error('Error fetching features:', err);
        });
      } else {
        setOverlays({original: {}, simplified: {}});
      }
      
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
      // Backend returns allFeaturesOrig and allFeaturesSimp, not nested in features
      setOverlays({
        original: res.allFeaturesOrig || {},
        simplified: res.allFeaturesSimp || {}
      })
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
        {/* Header with Tabs */}
        <div style={{
          padding: '20px 24px 0 24px',
          backgroundColor: '#fff',
          borderBottom: '1px solid #e0e0e0',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16}}>
            <div>
              <h1 style={{margin: 0, fontSize: 24, fontWeight: 600, color: '#333'}}>
                Temporal Data Feature Taxonomy
              </h1>
              <p style={{margin: '4px 0 0 0', fontSize: 14, color: '#666'}}>
                Explore and analyze time series data with various algorithms
              </p>
            </div>
          </div>

          {/* Tab Navigation */}
          <div style={{display: 'flex', gap: 4}}>
            <button
              onClick={() => setActiveTab('explorer')}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: activeTab === 'explorer' ? '3px solid #1E88E5' : '3px solid transparent',
                backgroundColor: activeTab === 'explorer' ? '#E3F2FD' : 'transparent',
                color: activeTab === 'explorer' ? '#1E88E5' : '#666',
                fontSize: 14,
                fontWeight: activeTab === 'explorer' ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              🔍 Data Explorer
            </button>
            <button
              onClick={() => setActiveTab('plots')}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: activeTab === 'plots' ? '3px solid #1E88E5' : '3px solid transparent',
                backgroundColor: activeTab === 'plots' ? '#E3F2FD' : 'transparent',
                color: activeTab === 'plots' ? '#1E88E5' : '#666',
                fontSize: 14,
                fontWeight: activeTab === 'plots' ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              📊 Plots Gallery
            </button>
            <button
              onClick={() => setActiveTab('original')}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: activeTab === 'original' ? '3px solid #1E88E5' : '3px solid transparent',
                backgroundColor: activeTab === 'original' ? '#E3F2FD' : 'transparent',
                color: activeTab === 'original' ? '#1E88E5' : '#666',
                fontSize: 14,
                fontWeight: activeTab === 'original' ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              📈 Original Data
            </button>
            <button
              onClick={() => setActiveTab('pae')}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: activeTab === 'pae' ? '3px solid #1E88E5' : '3px solid transparent',
                backgroundColor: activeTab === 'pae' ? '#E3F2FD' : 'transparent',
                color: activeTab === 'pae' ? '#1E88E5' : '#666',
                fontSize: 14,
                fontWeight: activeTab === 'pae' ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              📉 PAE Analysis
            </button>
            <button
              onClick={() => setActiveTab('rankings')}
              style={{
                padding: '10px 20px',
                border: 'none',
                borderBottom: activeTab === 'rankings' ? '3px solid #1E88E5' : '3px solid transparent',
                backgroundColor: activeTab === 'rankings' ? '#E3F2FD' : 'transparent',
                color: activeTab === 'rankings' ? '#1E88E5' : '#666',
                fontSize: 14,
                fontWeight: activeTab === 'rankings' ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              🏆 Rankings
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'explorer' ? (
          <div style={{
            flex: 1,
            padding: 24,
            overflow: 'auto'
          }}>
            <ChartPanel orig={orig} smooth={smooth} overlays={overlays} aspect={aspect} method={method} selectedFeature={selectedFeature} />
            <MetricsBar metrics={metrics} datasetId={dataset} />
          </div>
        ) : activeTab === 'plots' ? (
          <PlotsGallery />
        ) : activeTab === 'original' ? (
          <OriginalPlotsGallery />
        ) : activeTab === 'pae' ? (
          <PrecomputedPlotsGallery />
        ) : (
          <RankingsViewer />
        )}
      </div>

      {/* Right Control Panel - Only show for Explorer tab */}
      {activeTab === 'explorer' && (
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
      )}
    </div>
  )
}