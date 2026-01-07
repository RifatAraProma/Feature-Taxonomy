import React from 'react';
import { getPlotUrl } from '../config/cdn';

// Paper figures from plots/paper figures/
const PAPER_FIGURES = [
  {
    title: 'Figure 1a',
    description: 'Overview',
    path: 'Fig 1 a.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1b (Chebyshev)',
    description: 'Chebyshev filter example',
    path: 'Fig 1 b chebyshev.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1b (Douglas-Peucker)',
    description: 'Douglas-Peucker simplification example',
    path: 'Fig 1 b douglas-peucker.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1b (Gaussian)',
    description: 'Gaussian filter example',
    path: 'Fig 1 b gaussian.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1b (PAA)',
    description: 'Piecewise Aggregate Approximation example',
    path: 'Fig 1 b paa.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1b (Uniform Subsample)',
    description: 'Uniform subsampling example',
    path: 'Fig 1 b uniform-subsample.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 1c',
    description: 'Feature taxonomy',
    path: 'Fig 1 c.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 2a',
    description: 'Algorithm performance',
    path: 'Fig 2 a.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 2b',
    description: 'Feature preservation comparison',
    path: 'Fig 2 b.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 2c',
    description: 'Dataset characteristics',
    path: 'Fig 2 c.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 3a',
    description: 'Performance by dataset type',
    path: 'Fig 3 a.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 3b',
    description: 'Algorithm specialization',
    path: 'Fig 3 b.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 3c',
    description: 'Feature category breakdown',
    path: 'Fig 3 c.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4a',
    description: 'Grading methodology',
    path: 'Fig 4 a.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4b',
    description: 'Grade distribution',
    path: 'Fig 4 b.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4c',
    description: 'Algorithm ranking',
    path: 'Fig 4 c.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4d',
    description: 'Dataset difficulty',
    path: 'Fig 4 d.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4e',
    description: 'Performance consistency',
    path: 'Fig 4 e.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4f',
    description: 'Feature-wise grades',
    path: 'Fig 4 f.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4g',
    description: 'Metric comparison',
    path: 'Fig 4 g.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 4h',
    description: 'Statistical analysis',
    path: 'Fig 4 h.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 5a',
    description: 'Case study A',
    path: 'Fig 5 a.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 5b',
    description: 'Case study B',
    path: 'Fig 5 b.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 5c',
    description: 'Case study C',
    path: 'Fig 5 c.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Figure 6',
    description: 'Conclusions and future work',
    path: 'Fig 6.pdf',
    category: 'Main Figures'
  },
  {
    title: 'Level Features',
    description: 'Point values and interval averages',
    path: 'level.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Extrema',
    description: 'Local peaks and valleys',
    path: 'extrema.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Regime & Change Points',
    description: 'Structural changes in time series',
    path: 'regime_change_points.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Spikes & Dips',
    description: 'Anomalous points detection',
    path: 'spikes_dips.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Slope',
    description: 'First derivative analysis',
    path: 'slope.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Curvature',
    description: 'Second derivative analysis',
    path: 'curvature.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Roughness',
    description: 'High-frequency variation',
    path: 'roughness.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Trend',
    description: 'Long-term directional movement',
    path: 'trend.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Noise',
    description: 'Random fluctuation analysis',
    path: 'noise.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Periodicity',
    description: 'Cyclic pattern detection',
    path: 'periodicity.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Mean',
    description: 'Central tendency',
    path: 'mean.pdf',
    category: 'Feature Details'
  },
  {
    title: 'Regression Fit',
    description: 'Linear trend approximation',
    path: 'regression_fit.pdf',
    category: 'Feature Details'
  },
  {
    title: 'FC Distribution (Normalized)',
    description: 'Distribution of normalized FC scores across all simplification levels',
    path: 'pdf24_converted (6)/level_l1_fc_distribution.pdf',
    category: 'FC Analysis'
  },
  {
    title: 'Raw L1 Error (Normalized)',
    description: 'Raw L1 error distribution without FC score transformation',
    path: 'pdf24_converted (6)/level_l1_raw.pdf',
    category: 'FC Analysis'
  },
  {
    title: 'Z-Score FC Distribution (Normalized)',
    description: 'Z-score normalized FC scores for statistical analysis',
    path: 'pdf24_converted (6)/level_l1_zscore_fc.pdf',
    category: 'FC Analysis'
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
                    Download PDF
                  </a>
                </div>
              </div>

              {/* Preview - Download Placeholder for PDF */}
              <div style={{
                padding: 24,
                backgroundColor: '#fafafa',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 400,
                gap: 16
              }}>
                <div style={{
                  fontSize: 64,
                  marginBottom: 16
                }}>📄</div>
                <div style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: '#333',
                  marginBottom: 8
                }}>PDF Document</div>
                <div style={{
                  fontSize: 14,
                  color: '#666',
                  textAlign: 'center',
                  maxWidth: 400
                }}>
                  Click "View Full Size" to open in a new window, or "Download PDF" to save locally
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Info Box */}
        <div style={{
          marginTop: 48,
          padding: 24,
          backgroundColor: '#FFF3E0',
          borderLeft: '4px solid #FF9800',
          borderRadius: 4
        }}>
          <h3 style={{
            fontSize: 16,
            fontWeight: 600,
            color: '#E65100',
            marginBottom: 8
          }}>
            📐 Figure Specifications
          </h3>
          <ul style={{
            fontSize: 14,
            color: '#666',
            lineHeight: 1.8,
            marginLeft: 20
          }}>
            <li><strong>Format:</strong> PDF (publication-ready, vector graphics)</li>
            <li><strong>Font Sizes:</strong> 22px base text, 26px bold titles</li>
            <li><strong>Spacing:</strong> Optimized for print publication (adequate margins between labels and axes)</li>
            <li><strong>Canvas Dimensions:</strong> 1400px × 900px (annotated), 1100px × 900px (standard)</li>
            <li><strong>ViewBox:</strong> 1200 × 900 coordinate system</li>
          </ul>
        </div>
      </div>

      {/* Fullscreen Modal - Removed since PDFs open in new tab */}
    </div>
  );
}
