import React, { useState, useEffect } from 'react';

// List of key grading visualizations from plots/fc_visualizations/
const GRADING_PLOTS = [
  {
    title: 'Algorithm Grades by Dataset',
    description: 'Comprehensive heatmap showing letter grades (A+ to F) for each algorithm across all 80 datasets',
    path: 'algorithm_grades_by_dataset_green.svg'
  },
  {
    title: 'Algorithm Grade Distribution',
    description: 'Bar chart showing the distribution of letter grades across all algorithms',
    path: 'algorithm_grade_distribution_barchart.svg'
  },
  {
    title: 'Algorithm Performance by Metric',
    description: 'Green heatmap showing average algorithm performance broken down by individual feature metrics',
    path: 'algorithm_metric_average_grades_colored.svg'
  },
  {
    title: 'Metric Grade Distribution',
    description: 'Bar chart showing how difficult each metric is (grade distribution per metric type)',
    path: 'metric_grade_distribution_barchart.svg'
  }
];

// All available metrics with readable names
const METRICS = [
  { key: 'level_l1', label: 'Level (L1)', category: 'Level' },
  { key: 'level_linf', label: 'Level (L∞)', category: 'Level' },
  { key: 'mean_delta', label: 'Mean', category: 'Level' },
  { key: 'extrema_bottleneck', label: 'Extrema (Bottleneck)', category: 'Shape' },
  { key: 'extrema_wasserstein', label: 'Extrema (Wasserstein)', category: 'Shape' },
  { key: 'regimes_delta', label: 'Regimes', category: 'Shape' },
  { key: 'change_points_delta', label: 'Change Points', category: 'Shape' },
  { key: 'spikes_dips_bottleneck', label: 'Spikes/Dips (Bottleneck)', category: 'Shape' },
  { key: 'spikes_dips_wasserstein', label: 'Spikes/Dips (Wasserstein)', category: 'Shape' },
  { key: 'slope_l1', label: 'Slope (L1)', category: 'Derivatives' },
  { key: 'slope_linf', label: 'Slope (L∞)', category: 'Derivatives' },
  { key: 'curvature_l1', label: 'Curvature (L1)', category: 'Derivatives' },
  { key: 'curvature_linf', label: 'Curvature (L∞)', category: 'Derivatives' },
  { key: 'roughness_delta', label: 'Roughness', category: 'Derivatives' },
  { key: 'trend_l1', label: 'Trend (L1)', category: 'Frequency' },
  { key: 'trend_linf', label: 'Trend (L∞)', category: 'Frequency' },
  { key: 'noise_l1', label: 'Noise (L1)', category: 'Frequency' },
  { key: 'noise_linf', label: 'Noise (L∞)', category: 'Frequency' },
  { key: 'noise_auc_delta', label: 'Noise (AUC)', category: 'Frequency' },
  { key: 'periodicity_amplitude_delta', label: 'Periodicity (Amplitude)', category: 'Frequency' },
  { key: 'periodicity_num_periods_delta', label: 'Periodicity (# Periods)', category: 'Frequency' },
  { key: 'regression_l1', label: 'Regression (L1)', category: 'Statistics' },
  { key: 'regression_linf', label: 'Regression (L∞)', category: 'Statistics' }
];

export default function GradingPlotsGallery() {
  const [selectedPlot, setSelectedPlot] = useState<{title: string, path: string} | null>(null);
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());
  const [selectedMetric, setSelectedMetric] = useState<string>('level_l1');

  const handleImageLoad = (path: string) => {
    setLoadedImages(prev => new Set([...prev, path]));
  };

  // Group metrics by category for organized dropdown
  const metricsByCategory = METRICS.reduce((acc, metric) => {
    if (!acc[metric.category]) acc[metric.category] = [];
    acc[metric.category].push(metric);
    return acc;
  }, {} as Record<string, typeof METRICS>);

  return (
    <div style={{
      flex: 1,
      overflow: 'auto',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{
        maxWidth: 1400,
        margin: '0 auto',
        padding: 32
      }}>
        {/* Header */}
        <div style={{
          marginBottom: 32
        }}>
          <h1 style={{
            fontSize: 32,
            fontWeight: 700,
            color: '#1a1a1a',
            marginBottom: 8
          }}>
            📊 Algorithm Grading Visualizations
          </h1>
          <p style={{
            fontSize: 16,
            color: '#666',
            lineHeight: 1.6
          }}>
            Comprehensive analysis of algorithm performance across datasets, metrics, and feature categories.
            Click any plot to view in full screen.
          </p>
        </div>

        {/* Plots Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(600px, 1fr))',
          gap: 24
        }}>
          {GRADING_PLOTS.map((plot, idx) => (
            <div
              key={idx}
              style={{
                backgroundColor: '#fff',
                borderRadius: 8,
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                overflow: 'hidden',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
              }}
            >
              {/* Plot Info */}
              <div style={{ padding: 20, borderBottom: '1px solid #e0e0e0' }}>
                <h3 style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: '#333',
                  marginBottom: 8
                }}>
                  {plot.title}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: '#666',
                  marginBottom: 12
                }}>
                  {plot.description}
                </p>
                
                {/* Action Buttons */}
                <div style={{
                  display: 'flex',
                  gap: 8
                }}>
                  <button
                    onClick={() => setSelectedPlot({ title: plot.title, path: plot.path })}
                    style={{
                      padding: '6px 16px',
                      fontSize: 13,
                      fontWeight: 500,
                      border: '1px solid #1E88E5',
                      backgroundColor: '#1E88E5',
                      color: '#fff',
                      borderRadius: 4,
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#1565C0';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#1E88E5';
                    }}
                  >
                    View Full Size
                  </button>
                  <a
                    href={getPlotUrl(`fc_visualizations/${plot.path}`)}
                    download
                    style={{
                      padding: '6px 16px',
                      fontSize: 13,
                      fontWeight: 500,
                      border: '1px solid #666',
                      backgroundColor: '#fff',
                      color: '#666',
                      borderRadius: 4,
                      textDecoration: 'none',
                      display: 'inline-flex',
                      alignItems: 'center',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = '#f5f5f5';
                      e.currentTarget.style.color = '#333';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#fff';
                      e.currentTarget.style.color = '#666';
                    }}
                  >
                    Download SVG
                  </a>
                </div>
              </div>

              {/* Preview Image */}
              <div style={{
                padding: 16,
                backgroundColor: '#fafafa',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 300
              }}>
                {!loadedImages.has(plot.path) && (
                  <div style={{ color: '#999', fontSize: 14 }}>Loading preview...</div>
                )}
                <img
                  src={getPlotUrl(`fc_visualizations/${plot.path}`)}
                  alt={plot.title}
                  onLoad={() => handleImageLoad(plot.path)}
                  onClick={() => setSelectedPlot({ title: plot.title, path: plot.path })}
                  style={{
                    maxWidth: '100%',
                    maxHeight: 400,
                    objectFit: 'contain',
                    cursor: 'pointer',
                    display: loadedImages.has(plot.path) ? 'block' : 'none'
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Metric-Specific Breakdown Section */}
        <div style={{
          marginTop: 48,
          padding: 24,
          backgroundColor: '#fff',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ marginBottom: 20 }}>
            <h2 style={{
              fontSize: 24,
              fontWeight: 600,
              color: '#333',
              marginBottom: 8
            }}>
              📊 Grades by Individual Metric
            </h2>
            <p style={{
              fontSize: 14,
              color: '#666',
              marginBottom: 16
            }}>
              View algorithm performance for a specific feature metric. Select a metric from the dropdown to see detailed heatmaps.
            </p>

            {/* Metric Selector */}
            <div style={{ marginBottom: 20 }}>
              <label style={{
                display: 'block',
                fontSize: 13,
                fontWeight: 600,
                color: '#555',
                marginBottom: 8,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Select Metric:
              </label>
              <select
                value={selectedMetric}
                onChange={(e) => setSelectedMetric(e.target.value)}
                style={{
                  width: '100%',
                  maxWidth: 500,
                  padding: '10px 14px',
                  fontSize: 14,
                  border: '2px solid #e0e0e0',
                  borderRadius: 6,
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#1E88E5'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#e0e0e0'}
              >
                {Object.entries(metricsByCategory).map(([category, metrics]) => (
                  <optgroup key={category} label={category}>
                    {metrics.map(metric => (
                      <option key={metric.key} value={metric.key}>
                        {metric.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>
          </div>

          {/* Selected Metric Display */}
          <div style={{
            backgroundColor: '#fafafa',
            borderRadius: 8,
            padding: 24,
            border: '1px solid #e0e0e0'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: 16
            }}>
              <div>
                <h3 style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: '#333',
                  marginBottom: 4
                }}>
                  {METRICS.find(m => m.key === selectedMetric)?.label}
                </h3>
                <span style={{
                  display: 'inline-block',
                  padding: '4px 10px',
                  fontSize: 11,
                  fontWeight: 600,
                  backgroundColor: '#E3F2FD',
                  color: '#1E88E5',
                  borderRadius: 4,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {METRICS.find(m => m.key === selectedMetric)?.category}
                </span>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => setSelectedPlot({
                    title: METRICS.find(m => m.key === selectedMetric)?.label || '',
                    path: `by_metric/${selectedMetric}_colored.svg`
                  })}
                  style={{
                    padding: '8px 16px',
                    fontSize: 13,
                    fontWeight: 500,
                    border: '1px solid #1E88E5',
                    backgroundColor: '#1E88E5',
                    color: '#fff',
                    borderRadius: 4,
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#1565C0';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#1E88E5';
                  }}
                >
                  View Full Size
                </button>
                <a
                  href={getPlotUrl(`fc_visualizations/by_metric/${selectedMetric}_colored.svg`)}
                  download
                  style={{
                    padding: '8px 16px',
                    fontSize: 13,
                    fontWeight: 500,
                    border: '1px solid #666',
                    backgroundColor: '#fff',
                    color: '#666',
                    borderRadius: 4,
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#f5f5f5';
                    e.currentTarget.style.color = '#333';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#fff';
                    e.currentTarget.style.color = '#666';
                  }}
                >
                  Download SVG
                </a>
              </div>
            </div>

            {/* Metric Image */}
            <div style={{
              backgroundColor: '#fff',
              borderRadius: 6,
              padding: 16,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: 500
            }}>
              {!loadedImages.has(`${selectedMetric}_colored.svg`) && (
                <div style={{ color: '#999', fontSize: 14 }}>Loading metric visualization...</div>
              )}
              <img
                src={getPlotUrl(`fc_visualizations/by_metric/${selectedMetric}_colored.svg`)}
                alt={METRICS.find(m => m.key === selectedMetric)?.label}
                onLoad={() => handleImageLoad(`${selectedMetric}_colored.svg`)}
                onClick={() => setSelectedPlot({
                  title: METRICS.find(m => m.key === selectedMetric)?.label || '',
                  path: `by_metric/${selectedMetric}_colored.svg`
                })}
                style={{
                  maxWidth: '100%',
                  maxHeight: 600,
                  objectFit: 'contain',
                  cursor: 'pointer',
                  display: loadedImages.has(`${selectedMetric}_colored.svg`) ? 'block' : 'none'
                }}
              />
            </div>
          </div>
        </div>

        {/* CSV Data Tables */}
        <div style={{
          marginTop: 48,
          padding: 24,
          backgroundColor: '#fff',
          borderRadius: 8,
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{
            fontSize: 24,
            fontWeight: 600,
            color: '#333',
            marginBottom: 16
          }}>
            📋 Data Tables
          </h2>
          <p style={{
            fontSize: 14,
            color: '#666',
            marginBottom: 16
          }}>
            Download raw grading data in CSV format:
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
            gap: 12
          }}>
            {[
              'algorithm_grade_summary.csv',
              'algorithm_ranking_by_gpa.csv',
              'dataset_algorithm_grades.csv',
              'dataset_algorithm_metric_grades.csv',
              'metric_difficulty.csv',
              'algorithm_performance_by_category.csv',
              'algorithm_overall_consistency.csv'
            ].map((csv, idx) => (
              <a
                key={idx}
                href={getPlotUrl(`fc_visualizations/${csv}`)}
                download
                style={{
                  padding: '10px 16px',
                  fontSize: 13,
                  fontWeight: 500,
                  border: '1px solid #e0e0e0',
                  backgroundColor: '#fff',
                  color: '#333',
                  borderRadius: 4,
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                  e.currentTarget.style.borderColor = '#1E88E5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#fff';
                  e.currentTarget.style.borderColor = '#e0e0e0';
                }}
              >
                <span>📄</span>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {csv.replace(/_/g, ' ').replace('.csv', '')}
                </span>
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* Fullscreen Modal */}
      {selectedPlot && (
        <div
          onClick={() => setSelectedPlot(null)}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.9)',
            zIndex: 1000,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 40,
            cursor: 'pointer'
          }}
        >
          <div style={{
            color: '#fff',
            fontSize: 24,
            fontWeight: 600,
            marginBottom: 20,
            textAlign: 'center'
          }}>
            {selectedPlot.title}
          </div>
          <img
            src={getPlotUrl(`fc_visualizations/${selectedPlot.path}`)}
            alt={selectedPlot.title}
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '95%',
              maxHeight: '85%',
              objectFit: 'contain',
              cursor: 'default'
            }}
          />
          <div style={{
            color: '#fff',
            fontSize: 14,
            marginTop: 20,
            opacity: 0.7
          }}>
            Click outside to close
          </div>
        </div>
      )}
    </div>
  );
}
