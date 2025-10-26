import React, { useState } from 'react'

export default function MetricsBar({metrics}:{metrics:any}){
  if(!metrics) return null
  
  const [activeToast, setActiveToast] = useState<string | null>(null);
  
  const featurePreservation = metrics.featurePreservation || {};
  
  // Group feature preservation metrics by feature
  const groupMetricsByFeature = () => {
    const groups: Record<string, any> = {
      level: {},
      mean: {},
      regimes: {},
      changepoints: {},
      extrema: {},
      spikes: {},
      slope: {},
      curvature: {},
      trend: {},
      noise: {},
      regression: {},
      periodicity: {},
      roughness: {}
    };
    
    Object.entries(featurePreservation).forEach(([key, value]) => {
      const lowerKey = key.toLowerCase();
      if (lowerKey.includes('level')) groups.level[key] = value;
      else if (lowerKey.includes('mean')) groups.mean[key] = value;
      else if (lowerKey.includes('regime')) groups.regimes[key] = value;
      else if (lowerKey.includes('changepoint')) groups.changepoints[key] = value;
      else if (lowerKey.includes('extrema')) groups.extrema[key] = value;
      else if (lowerKey.includes('spike')) groups.spikes[key] = value;
      else if (lowerKey.includes('slope')) groups.slope[key] = value;
      else if (lowerKey.includes('curvature')) groups.curvature[key] = value;
      else if (lowerKey.includes('trend')) groups.trend[key] = value;
      else if (lowerKey.includes('noise')) groups.noise[key] = value;
      else if (lowerKey.includes('regression')) groups.regression[key] = value;
      else if (lowerKey.includes('periodicity')) groups.periodicity[key] = value;
      else if (lowerKey.includes('roughness')) groups.roughness[key] = value;
    });
    
    // Remove empty groups
    return Object.fromEntries(
      Object.entries(groups).filter(([_, metrics]) => Object.keys(metrics).length > 0)
    );
  };
  
  const groupedFeatureMetrics = groupMetricsByFeature();
  
  const pointwiseMetrics = {
    L1: metrics.L1,
    Linf: metrics.Linf,
    rho: metrics.rho,
    roughnessRatio: metrics.roughnessRatio,
    hpEnergyLoss: metrics.hpEnergyLoss
  };
  
  // Color coding for metrics
  const getColor = (key: string, value: number) => {
    // Ratios close to 1 are good, correlations close to 1 are good
    if (key.includes('retention') || key.includes('correlation') || key === 'rho' || key.includes('Ratio') || key.includes('similarity')) {
      if (value >= 0.9) return '#4CAF50'; // Green - Excellent
      if (value >= 0.7) return '#FF9800'; // Orange - Good
      return '#f44336'; // Red - Poor
    }
    // Errors and losses - lower is better
    if (key.includes('error') || key === 'L1' || key === 'Linf' || key.includes('Loss') || key.includes('distance')) {
      if (value <= 0.05) return '#4CAF50'; // Green - Excellent
      if (value <= 0.15) return '#FF9800'; // Orange - Good
      return '#f44336'; // Red - Poor
    }
    // Default for any other metrics - treat as higher is better
    if (value >= 0.9) return '#4CAF50';
    if (value >= 0.7) return '#FF9800';
    return '#f44336';
  };
  
  // Format metric names for display
  const formatMetricName = (key: string) => {
    return key
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, str => str.toUpperCase())
      .trim();
  };
  
  // Get detailed explanation for each metric
  const getMetricExplanation = (key: string): { description: string, formula: string } => {
    const explanations: Record<string, { description: string, formula: string }> = {
      'L1': {
        description: 'Mean Absolute Error - Average absolute difference between original and simplified values at each point.',
        formula: 'L1 = (1/n) × Σ|y_orig[i] - y_simp[i]|'
      },
      'Linf': {
        description: 'Maximum Absolute Error - The largest absolute difference at any single point.',
        formula: 'L∞ = max(|y_orig[i] - y_simp[i]|)'
      },
      'rho': {
        description: 'Pearson Correlation Coefficient - Measures linear relationship between original and simplified series. Values range from -1 to 1, where 1 indicates perfect positive correlation.',
        formula: 'ρ = Cov(y_orig, y_simp) / (σ_orig × σ_simp)'
      },
      'roughnessRatio': {
        description: 'Roughness Ratio - Ratio of simplified roughness to original roughness. Measures how much variability is preserved.',
        formula: 'Ratio = roughness(y_simp) / roughness(y_orig)'
      },
      'hpEnergyLoss': {
        description: 'High-Pass Energy Loss - Percentage of high-frequency energy lost during simplification. Indicates how much detail/noise was removed.',
        formula: 'Loss = 1 - (E_hp_simp / E_hp_orig)'
      },
      'level_interval_correlation': {
        description: 'Level Interval Correlation - Correlation between level values computed over intervals in original and simplified series.',
        formula: 'ρ = Corr(level_orig, level_simp)'
      },
      'level_interval_mae': {
        description: 'Level Interval MAE - Mean absolute error between interval level values.',
        formula: 'MAE = (1/n) × Σ|level_orig[i] - level_simp[i]|'
      },
      'level_point_mae': {
        description: 'Level Point MAE - Mean absolute error between point-based level values.',
        formula: 'MAE = (1/n) × Σ|level_orig[t] - level_simp[t]|'
      },
      'extrema_retention': {
        description: 'Extrema Retention Rate - Percentage of local maxima and minima from the original series that are preserved in the simplified version.',
        formula: 'Retention = |extrema_simp ∩ extrema_orig| / |extrema_orig|'
      },
      'extrema_positional_error': {
        description: 'Extrema Position Error - Average distance between matched extrema positions in original and simplified series.',
        formula: 'Error = (1/n) × Σ|t_orig[i] - t_simp[i]|'
      },
      'changepoint_retention': {
        description: 'Change Point Retention - Percentage of regime change boundaries that are preserved.',
        formula: 'Retention = |cp_simp ∩ cp_orig| / |cp_orig|'
      },
      'regime_correlation': {
        description: 'Regime Correlation - Correlation between regime baseline values in original and simplified series.',
        formula: 'ρ = Corr(baseline_orig, baseline_simp)'
      },
      'spike_retention': {
        description: 'Spike Retention Rate - Percentage of outlier spikes/dips that are preserved.',
        formula: 'Retention = |spikes_simp ∩ spikes_orig| / |spikes_orig|'
      },
      'trend_similarity': {
        description: 'Trend Similarity - Cosine similarity between trend components of original and simplified series.',
        formula: 'Similarity = (trend_orig · trend_simp) / (||trend_orig|| × ||trend_simp||)'
      },
      'slope_correlation': {
        description: 'Slope Correlation - Correlation between first derivatives (rate of change) of both series.',
        formula: 'ρ = Corr(dy/dt_orig, dy/dt_simp)'
      },
      'curvature_similarity': {
        description: 'Curvature Similarity - Similarity between second derivatives (shape bending) of both series.',
        formula: 'Similarity = Corr(d²y/dt²_orig, d²y/dt²_simp)'
      },
      'regression_error': {
        description: 'Regression Coefficient Error - Difference between linear regression parameters (slope and intercept).',
        formula: 'Error = √((α_orig - α_simp)² + (β_orig - β_simp)²)'
      }
    };
    
    return explanations[key] || {
      description: 'Metric measuring the preservation of this feature between original and simplified series.',
      formula: 'See documentation for details'
    };
  };
  
  return (
    <div style={{
      marginTop: 24, 
      padding: '20px 24px',
      backgroundColor: '#fff',
      borderRadius: 12,
      border: '1px solid #e0e0e0',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 20,
        paddingBottom: 12,
        borderBottom: '2px solid #FF1493'
      }}>
        <h2 style={{
          margin: 0, 
          fontSize: 18, 
          fontWeight: 700, 
          color: '#333'
        }}>
          Algorithm Performance Metrics
        </h2>
        
        {/* Color Legend */}
        <div style={{
          display: 'flex',
          gap: 16,
          alignItems: 'center',
          fontSize: 12,
          fontWeight: 500
        }}>
          <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: '#4CAF50',
              borderRadius: 4,
              border: '2px solid #4CAF50'
            }}></div>
            <span style={{color: '#666'}}>Excellent</span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: '#FF9800',
              borderRadius: 4,
              border: '2px solid #FF9800'
            }}></div>
            <span style={{color: '#666'}}>Good</span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: 6}}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: '#f44336',
              borderRadius: 4,
              border: '2px solid #f44336'
            }}></div>
            <span style={{color: '#666'}}>Poor</span>
          </div>
        </div>
      </div>
      
      {/* Point-wise Metrics */}
      <div style={{marginBottom: 24}}>
        <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12}}>
          <h3 style={{
            margin: 0, 
            fontSize: 14, 
            fontWeight: 600, 
            color: '#666',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Point-wise Metrics
          </h3>
          <button
            onClick={() => setActiveToast(activeToast === 'pointwise' ? null : 'pointwise')}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              display: 'flex',
              alignItems: 'center',
              color: '#2196F3',
              fontSize: 16
            }}
            title="Click for more info"
          >
            ℹ️
          </button>
        </div>
        
        {/* Toast for Point-wise Metrics */}
        {activeToast === 'pointwise' && (
          <div style={{
            marginBottom: 12,
            padding: '12px 16px',
            backgroundColor: '#E3F2FD',
            border: '1px solid #2196F3',
            borderRadius: 8,
            fontSize: 13,
            lineHeight: 1.6,
            color: '#0D47A1'
          }}>
            <strong>Point-wise Metrics</strong> measure how closely the simplified series follows the original series at each point:
            <ul style={{margin: '8px 0 0 0', paddingLeft: 20}}>
              <li><strong>L1:</strong> Average absolute difference between points</li>
              <li><strong>Linf:</strong> Maximum absolute difference at any point</li>
              <li><strong>rho (ρ):</strong> Correlation coefficient (1 = perfect correlation)</li>
              <li><strong>Roughness Ratio:</strong> Ratio of simplified to original roughness</li>
              <li><strong>HP Energy Loss:</strong> High-pass energy lost during simplification</li>
            </ul>
          </div>
        )}
        
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 12
        }}>
          {Object.entries(pointwiseMetrics)
            .filter(([k,v]) => v !== undefined)
            .map(([k, v]) => {
              const explanation = getMetricExplanation(k);
              return (
                <div 
                  key={k}
                  style={{
                    padding: '12px 16px',
                    borderRadius: 8,
                    background: `linear-gradient(135deg, ${getColor(k, v as number)}15, ${getColor(k, v as number)}05)`,
                    border: `2px solid ${getColor(k, v as number)}`,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 4,
                    position: 'relative',
                    cursor: 'pointer'
                  }}
                  title={`${explanation.description}\n\n${explanation.formula}`}
                  onMouseEnter={(e) => {
                    const tooltip = e.currentTarget.querySelector('.metric-tooltip') as HTMLElement;
                    if (tooltip) tooltip.style.display = 'block';
                  }}
                  onMouseLeave={(e) => {
                    const tooltip = e.currentTarget.querySelector('.metric-tooltip') as HTMLElement;
                    if (tooltip) tooltip.style.display = 'none';
                  }}
                >
                  <div style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: '#666',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {formatMetricName(k)}
                  </div>
                  <div style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: getColor(k, v as number)
                  }}>
                    {Number(v).toFixed(4)}
                  </div>
                  
                  {/* Tooltip */}
                  <div 
                    className="metric-tooltip"
                    style={{
                      display: 'none',
                      position: 'absolute',
                      bottom: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      marginBottom: 8,
                      padding: '12px 16px',
                      backgroundColor: '#263238',
                      color: '#fff',
                      borderRadius: 8,
                      fontSize: 12,
                      lineHeight: 1.5,
                      width: '280px',
                      zIndex: 1000,
                      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                      pointerEvents: 'none'
                    }}
                  >
                    <div style={{fontWeight: 600, marginBottom: 6}}>{explanation.description}</div>
                    <div style={{
                      fontFamily: 'monospace',
                      fontSize: 11,
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      padding: '6px 8px',
                      borderRadius: 4,
                      marginTop: 6
                    }}>
                      {explanation.formula}
                    </div>
                    {/* Tooltip arrow */}
                    <div style={{
                      position: 'absolute',
                      top: '100%',
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: 0,
                      height: 0,
                      borderLeft: '8px solid transparent',
                      borderRight: '8px solid transparent',
                      borderTop: '8px solid #263238'
                    }}></div>
                  </div>
                </div>
              );
            })
          }
        </div>
      </div>
      
      {/* Feature Preservation Metrics */}
      {Object.keys(featurePreservation).length > 0 && (
        <div>
          <div style={{display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12}}>
            <h3 style={{
              margin: 0, 
              fontSize: 14, 
              fontWeight: 600, 
              color: '#666',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Feature Preservation Metrics
            </h3>
            <button
              onClick={() => setActiveToast(activeToast === 'feature' ? null : 'feature')}
              style={{
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                color: '#2196F3',
                fontSize: 16
              }}
              title="Click for more info"
            >
              ℹ️
            </button>
          </div>
          
          {/* Toast for Feature Preservation Metrics */}
          {activeToast === 'feature' && (
            <div style={{
              marginBottom: 12,
              padding: '12px 16px',
              backgroundColor: '#E3F2FD',
              border: '1px solid #2196F3',
              borderRadius: 8,
              fontSize: 13,
              lineHeight: 1.6,
              color: '#0D47A1'
            }}>
              <strong>Feature Preservation Metrics</strong> measure how well the simplified series maintains important visual features of the original:
              <ul style={{margin: '8px 0 0 0', paddingLeft: 20}}>
                <li><strong>Retention:</strong> Percentage of features retained (e.g., extrema, change points)</li>
                <li><strong>Correlation:</strong> How similar feature values are between original and simplified</li>
                <li><strong>Error/MAE:</strong> Average difference in feature locations or magnitudes</li>
                <li><strong>Ratio:</strong> Ratio of simplified to original feature values</li>
              </ul>
              <div style={{marginTop: 8, fontSize: 12, fontStyle: 'italic'}}>
                Higher values are better for retention/correlation. Lower values are better for errors. Ratios close to 1.0 indicate good preservation.
              </div>
            </div>
          )}
          
          {/* Grouped Feature Metrics */}
          {Object.entries(groupedFeatureMetrics).map(([featureName, featureMetrics]) => (
            <div key={featureName} style={{marginBottom: 20}}>
              <h4 style={{
                margin: '0 0 10px 0',
                fontSize: 13,
                fontWeight: 700,
                color: '#FF1493',
                textTransform: 'capitalize',
                letterSpacing: '0.5px'
              }}>
                {featureName}
              </h4>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 12
              }}>
                {Object.entries(featureMetrics as Record<string, any>).map(([k, v]) => {
                  const explanation = getMetricExplanation(k);
                  return (
                    <div 
                      key={k}
                      style={{
                        padding: '12px 16px',
                        borderRadius: 8,
                        background: `linear-gradient(135deg, ${getColor(k, v as number)}15, ${getColor(k, v as number)}05)`,
                        border: `2px solid ${getColor(k, v as number)}`,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: 4,
                        position: 'relative',
                        cursor: 'pointer'
                      }}
                      title={`${explanation.description}\n\n${explanation.formula}`}
                      onMouseEnter={(e) => {
                        const tooltip = e.currentTarget.querySelector('.metric-tooltip') as HTMLElement;
                        if (tooltip) tooltip.style.display = 'block';
                      }}
                      onMouseLeave={(e) => {
                        const tooltip = e.currentTarget.querySelector('.metric-tooltip') as HTMLElement;
                        if (tooltip) tooltip.style.display = 'none';
                      }}
                    >
                      <div style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: '#666',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px'
                      }}>
                        {formatMetricName(k.replace(featureName + '_', ''))}
                      </div>
                      <div style={{
                        fontSize: 20,
                        fontWeight: 700,
                        color: getColor(k, v as number)
                      }}>
                        {typeof v === 'number' ? v.toFixed(4) : String(v)}
                      </div>
                      
                      {/* Tooltip */}
                      <div 
                        className="metric-tooltip"
                        style={{
                          display: 'none',
                          position: 'absolute',
                          bottom: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          marginBottom: 8,
                          padding: '12px 16px',
                          backgroundColor: '#263238',
                          color: '#fff',
                          borderRadius: 8,
                          fontSize: 12,
                          lineHeight: 1.5,
                          width: '280px',
                          zIndex: 1000,
                          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                          pointerEvents: 'none'
                        }}
                      >
                        <div style={{fontWeight: 600, marginBottom: 6}}>{explanation.description}</div>
                        <div style={{
                          fontFamily: 'monospace',
                          fontSize: 11,
                          backgroundColor: 'rgba(255,255,255,0.1)',
                          padding: '6px 8px',
                          borderRadius: 4,
                          marginTop: 6
                        }}>
                          {explanation.formula}
                        </div>
                        {/* Tooltip arrow */}
                        <div style={{
                          position: 'absolute',
                          top: '100%',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: 0,
                          height: 0,
                          borderLeft: '8px solid transparent',
                          borderRight: '8px solid transparent',
                          borderTop: '8px solid #263238'
                        }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}