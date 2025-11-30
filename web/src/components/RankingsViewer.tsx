import React, { useState } from 'react'

export default function RankingsViewer() {
  const [rankingType, setRankingType] = useState<'dataset_type' | 'feature' | 'category' | 'density' | 'periodic' | 'global'>('dataset_type')
  const [selectedView, setSelectedView] = useState<string>('')

  // Define available views for each ranking type
  const viewOptions: Record<string, { value: string; label: string }[]> = {
    dataset_type: [
      { value: 'astro', label: 'Astronomy' },
      { value: 'climate_awnd', label: 'Climate - Wind Speed' },
      { value: 'climate_prcp', label: 'Climate - Precipitation' },
      { value: 'climate_tmax', label: 'Climate - Max Temperature' },
      { value: 'crime', label: 'Crime Statistics' },
      { value: 'eeg_500', label: 'EEG (500 points)' },
      { value: 'eeg_2500', label: 'EEG (2,500 points)' },
      { value: 'eeg_10000', label: 'EEG (10,000 points)' },
      { value: 'flights', label: 'Flight Data' },
      { value: 'nz_tourism', label: 'NZ Tourism' },
      { value: 'stock_price', label: 'Stock Price' },
      { value: 'stock_volume', label: 'Stock Volume' },
      { value: 'unemployment', label: 'Unemployment' },
    ],
    feature: [
      { value: 'change_points_delta', label: 'Change Points' },
      { value: 'curvature_l1', label: 'Curvature (L1)' },
      { value: 'curvature_linf', label: 'Curvature (L∞)' },
      { value: 'extrema_bottleneck', label: 'Extrema (Bottleneck)' },
      { value: 'extrema_wasserstein', label: 'Extrema (Wasserstein)' },
      { value: 'level_l1', label: 'Level (L1)' },
      { value: 'level_linf', label: 'Level (L∞)' },
      { value: 'mean_delta', label: 'Mean Delta' },
      { value: 'noise_auc_delta', label: 'Noise AUC Delta' },
      { value: 'noise_l1', label: 'Noise (L1)' },
      { value: 'noise_linf', label: 'Noise (L∞)' },
      { value: 'periodicity_amplitude_delta', label: 'Periodicity Amplitude' },
      { value: 'periodicity_num_periods_delta', label: 'Periodicity Periods' },
      { value: 'regimes_delta', label: 'Regimes' },
      { value: 'regression_l1', label: 'Regression (L1)' },
      { value: 'regression_linf', label: 'Regression (L∞)' },
      { value: 'roughness_delta', label: 'Roughness' },
      { value: 'slope_l1', label: 'Slope (L1)' },
      { value: 'slope_linf', label: 'Slope (L∞)' },
      { value: 'spikes_dips_bottleneck', label: 'Spikes/Dips (Bottleneck)' },
      { value: 'spikes_dips_wasserstein', label: 'Spikes/Dips (Wasserstein)' },
      { value: 'trend_l1', label: 'Trend (L1)' },
      { value: 'trend_linf', label: 'Trend (L∞)' },
    ],
    category: [
      { value: 'overall', label: 'Overall (All Algorithms)' },
      { value: 'transformer', label: 'Transformers' },
      { value: 'reducer', label: 'Reducers' },
      { value: 'aggregator', label: 'Aggregators' },
    ],
    density: [
      { value: 'overall', label: 'Overall (All Densities)' },
      { value: 'low', label: 'Low Density (< 1,257 points)' },
      { value: 'medium', label: 'Medium Density (1,257 - 2,499 points)' },
      { value: 'high', label: 'High Density (≥ 2,500 points)' },
    ],
    periodic: [
      { value: 'num_periods', label: 'Number of Periods Preservation' },
      { value: 'amplitude', label: 'Amplitude Preservation' },
    ],
    global: [
      { value: 'global', label: 'Global Ranking' },
    ],
  }

  // Initialize selected view when ranking type changes
  React.useEffect(() => {
    const options = viewOptions[rankingType]
    if (options && options.length > 0) {
      setSelectedView(options[0].value)
    }
  }, [rankingType])

  // Build the SVG path
  const getSvgPath = () => {
    if (!selectedView) return null

    if (rankingType === 'global') {
      return '/plots/global_ranking/global_bump_chart.svg'
    } else if (rankingType === 'category') {
      return `/plots/category_rankings/${selectedView}_bump_chart.svg`
    } else if (rankingType === 'dataset_type') {
      return `/plots/dataset_type_rankings/${selectedView}_bump_chart.svg`
    } else if (rankingType === 'feature') {
      return `/plots/feature_rankings/${selectedView}_bump_chart.svg`
    } else if (rankingType === 'density') {
      return `/plots/density_rankings/${selectedView}_bump_chart.svg`
    } else if (rankingType === 'periodic') {
      return `/plots/periodic_rankings/${selectedView}_bump_chart.svg`
    }
    return null
  }

  const svgPath = getSvgPath()

  return (
    <div style={{
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      backgroundColor: '#f5f5f5'
    }}>
      {/* Controls Panel */}
      <div style={{
        backgroundColor: '#fff',
        borderBottom: '1px solid #e0e0e0',
        padding: '20px 24px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
      }}>
        <div style={{
          display: 'flex',
          gap: 24,
          alignItems: 'center',
          flexWrap: 'wrap'
        }}>
          {/* Ranking Type Selector */}
          <div style={{ minWidth: 200 }}>
            <label style={{
              display: 'block',
              fontSize: 13,
              fontWeight: 600,
              color: '#555',
              marginBottom: 8,
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Ranking Type
            </label>
            <select
              value={rankingType}
              onChange={(e) => setRankingType(e.target.value as any)}
              style={{
                width: '100%',
                padding: '10px 12px',
                fontSize: 14,
                border: '1px solid #ccc',
                borderRadius: 6,
                backgroundColor: '#fff',
                cursor: 'pointer',
                transition: 'border-color 0.2s',
                outline: 'none'
              }}
              onFocus={(e) => e.target.style.borderColor = '#1E88E5'}
              onBlur={(e) => e.target.style.borderColor = '#ccc'}
            >
              <option value="dataset_type">By Dataset Type</option>
              <option value="feature">By Feature</option>
              <option value="category">By Algorithm Category</option>
              <option value="density">By Data Point Density</option>
              <option value="periodic">Periodic Datasets (Periodicity)</option>
              <option value="global">Global Ranking</option>
            </select>
          </div>

          {/* View Selector */}
          {rankingType !== 'global' && (
            <div style={{ flex: 1, minWidth: 250 }}>
              <label style={{
                display: 'block',
                fontSize: 13,
                fontWeight: 600,
                color: '#555',
                marginBottom: 8,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                {rankingType === 'dataset_type' ? 'Dataset Type' :
                 rankingType === 'feature' ? 'Feature' :
                 rankingType === 'density' ? 'Density Bucket' :
                 rankingType === 'periodic' ? 'Periodicity Metric' :
                 'Category'}
              </label>
              <select
                value={selectedView}
                onChange={(e) => setSelectedView(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 12px',
                  fontSize: 14,
                  border: '1px solid #ccc',
                  borderRadius: 6,
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s',
                  outline: 'none'
                }}
                onFocus={(e) => e.target.style.borderColor = '#1E88E5'}
                onBlur={(e) => e.target.style.borderColor = '#ccc'}
              >
                {viewOptions[rankingType]?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Info Badge */}
          <div style={{
            marginLeft: 'auto',
            padding: '8px 16px',
            backgroundColor: '#E3F2FD',
            borderRadius: 6,
            fontSize: 13,
            color: '#1E88E5',
            fontWeight: 500
          }}>
            📊 Bump Chart View
          </div>
        </div>

        {/* Description */}
        <div style={{
          marginTop: 16,
          padding: 12,
          backgroundColor: '#f8f9fa',
          borderRadius: 6,
          fontSize: 13,
          color: '#666',
          lineHeight: 1.6
        }}>
          {rankingType === 'dataset_type' && (
            <p style={{ margin: 0 }}>
              <strong>Dataset Type Rankings:</strong> Shows how algorithms rank across different datasets within a specific category (e.g., stock prices, climate data).
              Lower ranks (closer to 1) indicate better feature preservation.
            </p>
          )}
          {rankingType === 'feature' && (
            <p style={{ margin: 0 }}>
              <strong>Feature Rankings:</strong> Shows how algorithms preserve a specific visual feature across different dataset types.
              Compare algorithm performance for preserving extrema, trends, noise, etc.
            </p>
          )}
          {rankingType === 'category' && (
            <p style={{ margin: 0 }}>
              <strong>Category Rankings:</strong> Shows how algorithms rank within their category (Transformers, Reducers, Aggregators).
              "Overall" shows all algorithms with category distinctions.
            </p>
          )}
          {rankingType === 'density' && (
            <p style={{ margin: 0 }}>
              <strong>Density Rankings:</strong> Shows how algorithms perform on datasets with different data point densities.
              Low (&lt;1,257 pts), Medium (1,257-2,499 pts), High (≥2,500 pts). Helps identify which algorithms work best for sparse vs. dense data.
            </p>
          )}
          {rankingType === 'periodic' && (
            <p style={{ margin: 0 }}>
              <strong>Periodic Dataset Rankings:</strong> Focuses on truly periodic datasets (climate seasonality, unemployment cycles, crime patterns).
              Evaluates algorithm performance specifically on preserving periodicity characteristics: number of periods and amplitude strength.
            </p>
          )}
          {rankingType === 'global' && (
            <p style={{ margin: 0 }}>
              <strong>Global Ranking:</strong> Overall algorithm performance averaged across all features and dataset types.
              This provides a comprehensive view of which algorithms perform best overall.
            </p>
          )}
        </div>
      </div>

      {/* Chart Display */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: 24,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'flex-start'
      }}>
        {svgPath ? (
          <div style={{
            backgroundColor: '#fff',
            borderRadius: 8,
            padding: 24,
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            maxWidth: '100%',
            overflow: 'auto'
          }}>
            <img
              src={svgPath}
              alt={`${rankingType} - ${selectedView} bump chart`}
              style={{
                maxWidth: '100%',
                height: 'auto',
                display: 'block'
              }}
              onError={(e) => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
                const parent = target.parentElement
                if (parent) {
                  const errorDiv = document.createElement('div')
                  errorDiv.style.cssText = 'padding: 40px; text-align: center; color: #999;'
                  errorDiv.innerHTML = `
                    <div style="font-size: 48px; margin-bottom: 16px;">📊</div>
                    <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">Chart not found</div>
                    <div style="font-size: 14px;">This ranking chart hasn't been generated yet.</div>
                    <div style="font-size: 13px; margin-top: 8px; color: #bbb;">Run the ranking script to generate charts.</div>
                  `
                  parent.appendChild(errorDiv)
                }
              }}
            />
          </div>
        ) : (
          <div style={{
            padding: 60,
            textAlign: 'center',
            color: '#999'
          }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>📊</div>
            <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
              Select a view to display rankings
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
