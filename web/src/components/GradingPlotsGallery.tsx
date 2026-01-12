import React, { useState, useEffect } from 'react';
import { getPlotUrl } from '../config/cdn';

// List of key grading visualizations from plots/fc_visualizations/
const GRADING_PLOTS = [
  {
    title: 'Algorithm Grades by Dataset',
    description: 'Purple heatmap showing mode grades for each algorithm across all 80 datasets (aggregated across metrics)',
    path: 'algorithm_dataset_mode_grades.svg'
  },
  {
    title: 'Algorithm Performance by Metric',
    description: 'Purple heatmap showing mode grades for each algorithm-metric combination (aggregated across datasets)',
    path: 'algorithm_metric_mode_grades.svg'
  }
];

// All available metrics with readable names (flat list, no noise_auc)
const METRICS = [
  { key: 'level_l1', label: 'Level (L1)' },
  { key: 'level_linf', label: 'Level (L∞)' },
  { key: 'mean_delta', label: 'Mean' },
  { key: 'extrema_bottleneck', label: 'Extrema (Bottleneck)' },
  { key: 'extrema_wasserstein', label: 'Extrema (Wasserstein)' },
  { key: 'regimes_delta', label: 'Regimes' },
  { key: 'change_points_delta', label: 'Change Points' },
  { key: 'spikes_dips_bottleneck', label: 'Spikes/Dips (Bottleneck)' },
  { key: 'spikes_dips_wasserstein', label: 'Spikes/Dips (Wasserstein)' },
  { key: 'slope_l1', label: 'Slope (L1)' },
  { key: 'slope_linf', label: 'Slope (L∞)' },
  { key: 'curvature_l1', label: 'Curvature (L1)' },
  { key: 'curvature_linf', label: 'Curvature (L∞)' },
  { key: 'roughness_delta', label: 'Roughness' },
  { key: 'trend_l1', label: 'Trend (L1)' },
  { key: 'trend_linf', label: 'Trend (L∞)' },
  { key: 'noise_l1', label: 'Noise (L1)' },
  { key: 'noise_linf', label: 'Noise (L∞)' },
  { key: 'periodicity_amplitude_delta', label: 'Periodicity (Amplitude)' },
  { key: 'periodicity_num_periods_delta', label: 'Periodicity (# Periods)' },
  { key: 'regression_l1', label: 'Regression (L1)' },
  { key: 'regression_linf', label: 'Regression (L∞)' }
];

export default function GradingPlotsGallery() {
  const [selectedPlot, setSelectedPlot] = useState<{title: string, path: string} | null>(null);
  const [loadedImages, setLoadedImages] = useState<Set<string>>(new Set());
  const [selectedMetric, setSelectedMetric] = useState<string>('level_l1');

  const handleImageLoad = (path: string) => {
    setLoadedImages(prev => new Set([...prev, path]));
  };

  return (
    <div style={{
      flex: 1,
      overflow: 'auto',
      backgroundColor: '#f5f5f5'
    }}>
      {/* Description Header */}
      <div style={{
        padding: '20px 24px',
        backgroundColor: '#e8f5e9',
        borderBottom: '2px solid #4CAF50',
        marginBottom: 0
      }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: 18, fontWeight: 600, color: '#2E7D32' }}>
          📊 Grading Analysis
        </h2>
        <p style={{ margin: 0, fontSize: 14, color: '#555', lineHeight: 1.6 }}>
          <strong>Grading measures consistency:</strong> After computing FC scores and assigning quartile-based ratings across all 100 levels, 
          we calculate letter grades (A-F) for each algorithm-metric and algorithm-dataset combination following the process described in
          <span style={{ color: '#1976D2', fontWeight: 600 }}> "Evaluation Pipeline" tab.</span>
        </p>
      </div>

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
            Algorithm Grading Visualizations
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
                {METRICS.map(metric => (
                  <option key={metric.key} value={metric.key}>
                    {metric.label}
                  </option>
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
                  marginBottom: 0
                }}>
                  {METRICS.find(m => m.key === selectedMetric)?.label}
                </h3>
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
