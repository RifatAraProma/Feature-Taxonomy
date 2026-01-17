import React from 'react';
import { getPlotUrl } from '../config/cdn';

// Paper figures from plots/paper  figures/
const PAPER_FIGURES = [
  {
    title: 'Fig 1',
    description: 'Feature taxonomy overview',
    path: 'Fig 1.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 input',
    description: 'Input time series',
    path: 'Fig 2 input.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 gaussian',
    description: 'Gaussian filter example',
    path: 'Fig 2 gaussian.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 chebyshev',
    description: 'Chebyshev filter example',
    path: 'Fig 2 chebyshev.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 douglas-peucker',
    description: 'Douglas-Peucker simplification example',
    path: 'Fig 2 douglas-peucker.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 paa',
    description: 'Piecewise Aggregate Approximation example',
    path: 'Fig 2 paa.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 uniform-subsample',
    description: 'Uniform subsampling example',
    path: 'Fig 2 uniform-subsample.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 2 asap',
    description: 'ASAP aggregation example',
    path: 'Fig 2 asap.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 3 a',
    description: 'Performance by dataset type',
    path: 'Fig 3 a.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 3 b',
    description: 'Algorithm specialization',
    path: 'Fig 3 b.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 3 c',
    description: 'Feature category breakdown',
    path: 'Fig 3 c.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 a',
    description: 'Grading methodology',
    path: 'Fig 4 a.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 b',
    description: 'Grade distribution',
    path: 'Fig 4 b.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 c',
    description: 'Algorithm ranking',
    path: 'Fig 4 c.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 d',
    description: 'Dataset difficulty',
    path: 'Fig 4 d.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 e',
    description: 'Performance consistency',
    path: 'Fig 4 e.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 f',
    description: 'Feature-wise grades',
    path: 'Fig 4 f.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 g',
    description: 'Metric comparison',
    path: 'Fig 4 g.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 h',
    description: 'Statistical analysis',
    path: 'Fig 4 h.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 4 i',
    description: 'Additional analysis',
    path: 'Fig 4 i.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 5 a',
    description: 'Case study A',
    path: 'Fig 5 a.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 5 b',
    description: 'Case study B',
    path: 'Fig 5 b.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 5 c',
    description: 'Case study C',
    path: 'Fig 5 c.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 6 a',
    description: 'Conclusions part A',
    path: 'Fig 6 a.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 6 b',
    description: 'Conclusions part B',
    path: 'Fig 6 b.svg',
    category: 'Main Figures'
  },
  {
    title: 'Fig 6 c',
    description: 'Conclusions part C',
    path: 'Fig 6 c.svg',
    category: 'Main Figures'
  },
  {
    title: 'Level Features',
    description: 'Point values and interval averages',
    path: 'feature illustrations/level.svg',
    category: 'Feature Details'
  },
  {
    title: 'Extrema',
    description: 'Local peaks and valleys',
    path: 'feature illustrations/extrema.svg',
    category: 'Feature Details'
  },
  {
    title: 'Regime & Change Points',
    description: 'Structural changes in time series',
    path: 'feature illustrations/regime_change_points.svg',
    category: 'Feature Details'
  },
  {
    title: 'Spikes & Dips',
    description: 'Anomalous points detection',
    path: 'feature illustrations/spikes_dips.svg',
    category: 'Feature Details'
  },
  {
    title: 'Slope',
    description: 'First derivative analysis',
    path: 'feature illustrations/slope.svg',
    category: 'Feature Details'
  },
  {
    title: 'Curvature',
    description: 'Second derivative analysis',
    path: 'feature illustrations/curvature.svg',
    category: 'Feature Details'
  },
  {
    title: 'Roughness',
    description: 'High-frequency variation',
    path: 'feature illustrations/roughness.svg',
    category: 'Feature Details'
  },
  {
    title: 'Trend',
    description: 'Long-term directional movement',
    path: 'feature illustrations/trend.svg',
    category: 'Feature Details'
  },
  {
    title: 'Noise',
    description: 'Random fluctuation analysis',
    path: 'feature illustrations/noise.svg',
    category: 'Feature Details'
  },
  {
    title: 'Periodicity',
    description: 'Cyclic pattern detection',
    path: 'feature illustrations/periodicity.svg',
    category: 'Feature Details'
  },
  {
    title: 'Mean',
    description: 'Central tendency',
    path: 'feature illustrations/mean.svg',
    category: 'Feature Details'
  },
  {
    title: 'Regression Fit',
    description: 'Linear trend approximation',
    path: 'feature illustrations/regression_fit.svg',
    category: 'Feature Details'
  }
];

export default function PaperFiguresGallery() {
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
            📄 Paper Figures
          </h1>
          <p style={{
            fontSize: 16,
            color: '#666',
            lineHeight: 1.6
          }}>
            Publication-ready figures with optimized spacing and typography. These figures are formatted
            for academic paper submission with consistent styling and readable fonts.
          </p>
        </div>

        {/* Figures Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(600px, 1fr))',
          gap: 24
        }}>
          {PAPER_FIGURES.map((figure, idx) => (
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
              {/* Figure Info */}
              <div style={{ padding: 20, borderBottom: '1px solid #e0e0e0' }}>
                <div style={{
                  display: 'inline-block',
                  padding: '4px 12px',
                  fontSize: 11,
                  fontWeight: 600,
                  backgroundColor: '#E3F2FD',
                  color: '#1E88E5',
                  borderRadius: 4,
                  marginBottom: 12,
                  textTransform: 'uppercase',
                  letterSpacing: '0.5px'
                }}>
                  {figure.category}
                </div>
                <h3 style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: '#333',
                  marginBottom: 8
                }}>
                  {figure.title}
                </h3>
                <p style={{
                  fontSize: 14,
                  color: '#666',
                  marginBottom: 12
                }}>
                  {figure.description}
                </p>
                
                {/* Action Buttons */}
                <div style={{
                  display: 'flex',
                  gap: 8
                }}>
                  <button
                    onClick={() => window.open(getPlotUrl(`paper  figures/${encodeURIComponent(figure.path)}`), '_blank')}
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
                      e.currentTarget.style.borderColor = '#1565C0';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#1E88E5';
                      e.currentTarget.style.borderColor = '#1E88E5';
                    }}
                  >
                    View Full Size
                  </button>
                  <a
                    href={getPlotUrl(`paper  figures/${encodeURIComponent(figure.path)}`)}
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
                      e.currentTarget.style.borderColor = '#333';
                      e.currentTarget.style.color = '#333';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = '#fff';
                      e.currentTarget.style.borderColor = '#666';
                      e.currentTarget.style.color = '#666';
                    }}
                  >
                    Download SVG
                  </a>
                </div>
              </div>

              {/* Preview - SVG Embedded */}
              <div style={{
                padding: 24,
                backgroundColor: '#fafafa',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 400
              }}>
                <img 
                  src={getPlotUrl(`paper  figures/${encodeURIComponent(figure.path)}`)} 
                  alt={figure.title}
                  style={{
                    maxWidth: '100%',
                    height: 'auto',
                    border: '1px solid #e0e0e0',
                    borderRadius: 4
                  }}
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.parentElement!.innerHTML = `
                      <div style="text-align: center; color: #999; font-size: 14px;">
                        <div style="font-size: 48px; margin-bottom: 16px;">🖼️</div>
                        <div>SVG Preview</div>
                        <div style="margin-top: 8px; font-size: 12px;">Click "View Full Size" to view the figure</div>
                      </div>
                    `;
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fullscreen Modal - Removed since SVGs open in new tab */}
    </div>
  );
}
