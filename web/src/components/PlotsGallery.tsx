import React, { useState, useEffect } from 'react';

interface Dataset {
  id: string;
  n: number;
  category?: string;
}

interface PlotsGalleryProps {}

// All metrics available (23 total)
const METRICS = [
  'level_l1', 'level_linf',
  'mean_delta',
  'extrema_bottleneck', 'extrema_wasserstein',
  'curvature_l1', 'curvature_linf',
  'regression_l1', 'regression_linf',
  'roughness_delta',
  'slope_l1', 'slope_linf',
  'trend_l1', 'trend_linf',
  'noise_l1', 'noise_linf', 'noise_auc_delta',
  'periodicity_amplitude_delta', 'periodicity_num_periods_delta',
  'spikes_dips_bottleneck', 'spikes_dips_wasserstein',
  'regimes_delta',
  'change_points_delta'
];

// Organize by feature category
const METRIC_CATEGORIES = {
  'Level': ['level_l1', 'level_linf'],
  'Mean': ['mean_delta'],
  'Extrema': ['extrema_bottleneck', 'extrema_wasserstein'],
  'Curvature': ['curvature_l1', 'curvature_linf'],
  'Regression': ['regression_l1', 'regression_linf'],
  'Roughness': ['roughness_delta'],
  'Slope': ['slope_l1', 'slope_linf'],
  'Trend': ['trend_l1', 'trend_linf'],
  'Noise': ['noise_l1', 'noise_linf', 'noise_auc_delta'],
  'Periodicity': ['periodicity_amplitude_delta', 'periodicity_num_periods_delta'],
  'Spikes/Dips': ['spikes_dips_bottleneck', 'spikes_dips_wasserstein'],
  'Regimes': ['regimes_delta'],
  'Change Points': ['change_points_delta']
};

export default function PlotsGallery({}: PlotsGalleryProps) {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('stock_price');
  const [selectedDataset, setSelectedDataset] = useState<string>('stock_aapl_price');
  const [selectedMetric, setSelectedMetric] = useState('level_l1');
  const [viewMode, setViewMode] = useState<'ranking' | 'zscore' | 'both'>('both');
  const [showLegend, setShowLegend] = useState(true);
  const [showAllRanks, setShowAllRanks] = useState(false);

  // Fetch datasets on mount
  useEffect(() => {
    fetch('/datasets')
      .then(res => res.json())
      .then((data: Dataset[]) => {
        setDatasets(data);
        // Set initial dataset to first in stock_price category if available
        const stockPriceDatasets = data.filter(d => d.category === 'stock_price');
        if (stockPriceDatasets.length > 0) {
          setSelectedDataset(stockPriceDatasets[0].id);
        } else if (data.length > 0) {
          setSelectedDataset(data[0].id);
          setSelectedCategory(data[0].category || 'other');
        }
      })
      .catch(err => console.error('Failed to fetch datasets:', err));
  }, []);

  // Group datasets by category
  const groupedDatasets = datasets.reduce((acc, dataset) => {
    const category = dataset.category || 'other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(dataset);
    return acc;
  }, {} as Record<string, Dataset[]>);

  // Get categories sorted
  const categories = Object.keys(groupedDatasets).sort();

  // Get datasets for selected category
  const filteredDatasets = groupedDatasets[selectedCategory] || [];

  // Handle category change
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    // Auto-select first dataset in new category
    if (groupedDatasets[category] && groupedDatasets[category].length > 0) {
      setSelectedDataset(groupedDatasets[category][0].id);
    }
  };

  // Base path for plots - now in ranking subdirectory
  const basePath = `/plots/${selectedDataset}/ranking`;

  return (
    <div style={{ height: '100%', display: 'flex' }}>
      {/* Left Sidebar - All Controls */}
      <div style={{
        width: 320,
        borderRight: '1px solid #e0e0e0',
        backgroundColor: '#fafafa',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fff'
        }}>
          <h2 style={{ margin: '0 0 4px 0', fontSize: 16, fontWeight: 600, color: '#333' }}>
            📊 Plots Gallery
          </h2>
          <p style={{ margin: 0, fontSize: 11, color: '#666', lineHeight: 1.4 }}>
            Compare algorithm performance across metrics
          </p>
        </div>

        {/* Dataset Category Selector */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fff'
        }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: '#666', marginBottom: 8, display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Dataset Category:
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => handleCategoryChange(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: 4,
              fontSize: 13,
              cursor: 'pointer',
              backgroundColor: '#fff',
              fontWeight: 500
            }}
          >
            {categories.map(cat => (
              <option key={cat} value={cat}>
                {cat.toUpperCase()} ({groupedDatasets[cat].length})
              </option>
            ))}
          </select>
        </div>

        {/* Dataset File Selector */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fff'
        }}>
          <label style={{ fontSize: 11, fontWeight: 600, color: '#666', marginBottom: 8, display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Data File:
          </label>
          <select
            value={selectedDataset}
            onChange={(e) => setSelectedDataset(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              border: '1px solid #ddd',
              borderRadius: 4,
              fontSize: 13,
              cursor: 'pointer',
              backgroundColor: '#fff'
            }}
          >
            {filteredDatasets.map(d => (
              <option key={d.id} value={d.id}>
                {d.id} ({d.n.toLocaleString()} pts)
              </option>
            ))}
          </select>
          {filteredDatasets.find(d => d.id === selectedDataset) && (
            <div style={{
              marginTop: 8,
              padding: 8,
              backgroundColor: '#e3f2fd',
              borderRadius: 4,
              fontSize: 11,
              color: '#555'
            }}>
              <strong style={{ color: '#1976d2' }}>{selectedDataset}</strong>
              <div style={{ fontSize: 10, marginTop: 2 }}>
                {filteredDatasets.find(d => d.id === selectedDataset)?.n.toLocaleString()} data points
              </div>
            </div>
          )}
        </div>

        {/* Show All Ranks Checkbox */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fff'
        }}>
          <label style={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            fontSize: 13,
            fontWeight: 500,
            color: '#333'
          }}>
            <input
              type="checkbox"
              checked={showAllRanks}
              onChange={(e) => setShowAllRanks(e.target.checked)}
              style={{
                marginRight: 8,
                width: 16,
                height: 16,
                cursor: 'pointer'
              }}
            />
            Show All Rank Plots
          </label>
          <p style={{ margin: '8px 0 0 24px', fontSize: 11, color: '#666', lineHeight: 1.4 }}>
            Display ranking plots for all features and metrics
          </p>
        </div>

        {/* View Mode Selector - Only show if not showing all ranks */}
        {!showAllRanks && (
          <div style={{
            padding: '16px',
            borderBottom: '1px solid #e0e0e0',
            backgroundColor: '#fff'
          }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#666', marginBottom: 8, display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              View Mode:
            </label>
            <select
              value={viewMode}
              onChange={(e) => setViewMode(e.target.value as 'ranking' | 'zscore' | 'both')}
              style={{
                width: '100%',
                padding: '8px 12px',
                border: '1px solid #ddd',
                borderRadius: 4,
                fontSize: 13,
                cursor: 'pointer',
                backgroundColor: '#fff'
              }}
            >
              <option value="both">Both Plots</option>
              <option value="ranking">Ranking Only</option>
              <option value="zscore">Z-Score Only</option>
            </select>
          </div>
        )}

        {/* Legend Toggle */}
        <div style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#fff'
        }}>
          <button
            onClick={() => setShowLegend(!showLegend)}
            style={{
              width: '100%',
              padding: '8px 16px',
              border: '1px solid #ddd',
              borderRadius: 4,
              fontSize: 13,
              cursor: 'pointer',
              backgroundColor: showLegend ? '#1E88E5' : '#fff',
              color: showLegend ? '#fff' : '#333',
              fontWeight: 500,
              transition: 'all 0.2s'
            }}
          >
            {showLegend ? '✓ Legend Visible' : 'Show Legend'}
          </button>
        </div>

        {/* Metric Selector - Only show if not showing all ranks */}
        {!showAllRanks && (
          <div style={{
            padding: '16px',
            backgroundColor: '#fff',
            flex: 1,
            overflow: 'auto'
          }}>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#666', marginBottom: 12, display: 'block', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Select Metric:
            </label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {Object.entries(METRIC_CATEGORIES).map(([category, metrics]) => (
                <div key={category}>
                  <div style={{ 
                    fontSize: 10, 
                    fontWeight: 700, 
                    color: '#999', 
                    marginBottom: 6, 
                    textTransform: 'uppercase', 
                    letterSpacing: '0.5px',
                    paddingBottom: 4,
                    borderBottom: '1px solid #f0f0f0'
                  }}>
                    {category}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {metrics.map(metric => (
                      <button
                        key={metric}
                        onClick={() => setSelectedMetric(metric)}
                        style={{
                          padding: '6px 12px',
                          border: selectedMetric === metric ? '2px solid #1E88E5' : '1px solid #e0e0e0',
                          borderRadius: 4,
                          fontSize: 12,
                          cursor: 'pointer',
                          backgroundColor: selectedMetric === metric ? '#E3F2FD' : '#fff',
                          color: selectedMetric === metric ? '#1E88E5' : '#333',
                          fontWeight: selectedMetric === metric ? 600 : 400,
                          textAlign: 'left',
                          transition: 'all 0.15s'
                        }}
                      >
                        {metric}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Right Side - Plot Display Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        backgroundColor: '#f5f5f5'
      }}>
        {/* All Rank Plots View */}
        {showAllRanks ? (
          <div style={{
            flex: 1,
            padding: 16
          }}>
            <div style={{
              marginBottom: 16,
              padding: 16,
              backgroundColor: '#fff',
              borderRadius: 4,
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}>
              <h3 style={{ margin: '0 0 8px 0', fontSize: 16, fontWeight: 600, color: '#333' }}>
                📊 All Ranking Plots for {selectedDataset}
              </h3>
              <p style={{ margin: 0, fontSize: 13, color: '#666' }}>
                Showing all {METRICS.length} feature preservation metrics organized by category
              </p>
            </div>

            {/* Display all metrics organized by category */}
            {Object.entries(METRIC_CATEGORIES).map(([category, metrics]) => (
              <div key={category} style={{
                marginBottom: 24,
                backgroundColor: '#fff',
                borderRadius: 4,
                padding: 16,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
              }}>
                <h4 style={{
                  margin: '0 0 16px 0',
                  fontSize: 14,
                  fontWeight: 700,
                  color: '#1E88E5',
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px',
                  paddingBottom: 8,
                  borderBottom: '2px solid #1E88E5'
                }}>
                  {category}
                </h4>
                
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))',
                  gap: 16
                }}>
                  {metrics.map(metric => (
                    <div key={metric} style={{
                      backgroundColor: '#fafafa',
                      borderRadius: 4,
                      padding: 12,
                      border: '1px solid #e0e0e0'
                    }}>
                      <h5 style={{
                        margin: '0 0 12px 0',
                        fontSize: 13,
                        fontWeight: 600,
                        color: '#333',
                        fontFamily: 'monospace'
                      }}>
                        {metric}
                      </h5>
                      <img
                        src={`${basePath}/${metric}_ranking.svg`}
                        alt={`Ranking plot for ${metric}`}
                        style={{ 
                          width: '100%', 
                          height: 'auto',
                          display: 'block',
                          backgroundColor: '#fff',
                          borderRadius: 2
                        }}
                        onError={(e) => {
                          const img = e.target as HTMLImageElement;
                          img.style.display = 'none';
                          const parent = img.parentElement;
                          if (parent && !parent.querySelector('.error-message')) {
                            const error = document.createElement('div');
                            error.className = 'error-message';
                            error.style.padding = '40px 20px';
                            error.style.textAlign = 'center';
                            error.style.color = '#999';
                            error.style.backgroundColor = '#fff';
                            error.innerHTML = `
                              <p style="margin: 0; font-size: 12px;">📊 Plot not found</p>
                              <p style="margin: 4px 0 0 0; font-size: 11px;">Run generate_vegalite_plots.py</p>
                            `;
                            parent.appendChild(error);
                          }
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Single Metric View - Plot Display */
          <div style={{
            flex: 1,
            padding: 16,
            display: 'grid',
            gridTemplateColumns: viewMode === 'both' ? '1fr 1fr 400px' : viewMode === 'ranking' ? '1fr 400px' : '1fr 400px',
            gap: 16,
            alignItems: 'start',
            alignContent: 'start'
          }}>
            {/* Ranking Plot */}
            {(viewMode === 'both' || viewMode === 'ranking') && (
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 4,
              padding: 16,
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              height: '600px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#333' }}>
                📊 Algorithm Ranking
              </h3>
              <img
                src={`${basePath}/${selectedMetric}_ranking.svg`}
                alt={`Ranking plot for ${selectedMetric}`}
                style={{ 
                  width: '100%', 
                  height: '100%',
                  objectFit: 'contain',
                  display: 'block'
                }}
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.style.display = 'none';
                  const parent = img.parentElement;
                  if (parent) {
                    const error = document.createElement('div');
                    error.style.padding = '60px 20px';
                    error.style.textAlign = 'center';
                    error.style.color = '#999';
                    error.innerHTML = `
                      <p style="margin: 0; font-size: 14px;">📊 Plot not found</p>
                      <p style="margin: 8px 0 0 0; font-size: 12px;">Run generate_vegalite_plots.py to create plots</p>
                    `;
                    parent.appendChild(error);
                  }
                }}
              />
            </div>
          )}

          {/* Z-Score Plot */}
          {(viewMode === 'both' || viewMode === 'zscore') && (
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 4,
              padding: 16,
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              height: '600px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#333' }}>
                📈 Z-Score Breakdown
              </h3>
              <img
                src={`${basePath}/${selectedMetric}_zscore_fc.svg`}
                alt={`Z-score plot for ${selectedMetric}`}
                style={{ 
                  width: '100%', 
                  height: '100%',
                  objectFit: 'contain',
                  display: 'block'
                }}
                onError={(e) => {
                  const img = e.target as HTMLImageElement;
                  img.style.display = 'none';
                  const parent = img.parentElement;
                  if (parent) {
                    const error = document.createElement('div');
                    error.style.padding = '60px 20px';
                    error.style.textAlign = 'center';
                    error.style.color = '#999';
                    error.innerHTML = `
                      <p style="margin: 0; font-size: 14px;">📈 Plot not found</p>
                      <p style="margin: 8px 0 0 0; font-size: 12px;">Run generate_vegalite_plots.py to create plots</p>
                    `;
                    parent.appendChild(error);
                  }
                }}
              />
            </div>
          )}

          {/* Legend - Always visible in single metric view */}
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 4,
            padding: 16,
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            height: '600px',
            display: 'flex',
            flexDirection: 'column',
            textAlign: 'center'
          }}>
            {/* <h3 style={{ margin: '0 0 12px 0', fontSize: 14, fontWeight: 600, color: '#333' }}>
              🎨 Algorithm Legend
            </h3> */}
            <img
              src={`${basePath}/algorithm_legend.svg`}
              alt="Algorithm Color Legend"
              style={{ 
                maxWidth: '100%', 
                height: '100%',
                objectFit: 'contain'
              }}
              onError={(e) => {
                const img = e.target as HTMLImageElement;
                img.style.display = 'none';
                const parent = img.parentElement;
                if (parent && !parent.querySelector('.error-message')) {
                  const error = document.createElement('div');
                  error.className = 'error-message';
                  error.style.padding = '40px 20px';
                  error.style.textAlign = 'center';
                  error.style.color = '#999';
                  error.innerHTML = `
                    <p style="margin: 0; font-size: 12px;">🎨 Legend not found</p>
                    <p style="margin: 4px 0 0 0; font-size: 11px;">Run generate_vegalite_plots.py</p>
                  `;
                  parent.appendChild(error);
                }
              }}
            />
          </div>
        </div>
        )}

        {/* Help Text - Only show when not in all ranks mode */}
        {!showAllRanks && (
          <div style={{
            margin: 16,
            marginTop: 0,
            padding: 16,
            backgroundColor: '#fff',
            borderRadius: 4,
            fontSize: 12,
            color: '#666',
            lineHeight: 1.6,
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <div style={{ marginBottom: 12 }}>
              <strong style={{ fontSize: 13, color: '#333' }}>📖 How to Read These Charts</strong>
            </div>
            
            <div style={{ marginBottom: 12 }}>
              <strong style={{ color: '#1E88E5' }}>📊 Algorithm Ranking (Left)</strong>
              <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
                <li><strong>FC Score</strong> = Feature-Complexity Score = (Feature_z) - (PAE_z)</li>
                <li><strong>Higher is better:</strong> Good feature preservation with low visual complexity</li>
                <li><strong>Numbers on bars:</strong> Mean FC score across all 101 levels</li>
                <li><strong>Error bars:</strong> Standard deviation showing consistency</li>
                <li><strong>Top algorithms:</strong> Best tradeoff between preservation and simplicity</li>
              </ul>
            </div>
            
            <div style={{ marginBottom: 12 }}>
              <strong style={{ color: '#FB8C00' }}>📈 Z-Score Breakdown (Right)</strong>
              <ul style={{ margin: '4px 0 0 0', paddingLeft: 20 }}>
                <li><strong>X-axis (PAE Z-Score):</strong> Visual complexity (left = simpler, right = complex)</li>
                <li><strong>Y-axis (Feature Z-Score):</strong> Feature preservation quality</li>
                <li><strong>Each dot:</strong> One smoothing level (101 levels × 19 algorithms)</li>
                <li><strong>Ideal region:</strong> Bottom-left quadrant (low PAE, high preservation)</li>
                <li><strong>Red lines:</strong> Reference at z=0 (mean values)</li>
              </ul>
            </div>
            
            <div style={{ 
              padding: 10, 
              backgroundColor: '#E3F2FD', 
              borderLeft: '3px solid #1E88E5',
              borderRadius: 4,
              fontSize: 11
            }}>
              <strong style={{ color: '#1565C0' }}>💡 Pro Tip:</strong> Compare the same metric across datasets to see how algorithm performance varies with data characteristics. Algorithms with small error bars are more consistent across different smoothing levels.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
