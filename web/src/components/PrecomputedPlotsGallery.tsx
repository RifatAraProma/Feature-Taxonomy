import React, { useState, useEffect } from 'react'
import { getAlgorithmColor } from '../constants/algorithmColors'
import { getAlgorithmName } from '../constants/algorithmNames'
import { CDN_URLS } from '../config/cdn'

interface Dataset {
  id: string
  category: string
}

// List of all algorithms
const ALGORITHMS = [
  'gaussian_filter',
  'mean_filter',
  'median_filter',
  'min_filter',
  'max_filter',
  'savitzky_golay_filter',
  'butterworth_filter',
  'chebyshev_filter',
  'elliptical_filter',
  'fft_cutoff_filter',
  'lttb_downsample',
  'm4_downsample',
  'minmaxlttb_downsample',
  'uniform_subsample',
  'rdp_downsample',
  'fpcs_downsample',
  'tda_downsample',
  'asap_aggregator',
  'bin_average_aggregator'
]

export default function PrecomputedPlotsGallery() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('')
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [availableDatasets, setAvailableDatasets] = useState<Dataset[]>([])

  useEffect(() => {
    // Load all datasets
    fetch('/datasets')
      .then(res => res.json())
      .then(data => {
        const allCategories = new Set<string>()
        
        data.forEach((item: any) => {
          allCategories.add(item.category)
        })
        
        const datasets: Dataset[] = data.map((item: any) => ({
          id: item.id,
          category: item.category
        }))
        
        setDatasets(datasets)
        setCategories(Array.from(allCategories).sort())
        
        // Set initial category and dataset
        if (datasets.length > 0) {
          const firstCategory = datasets[0].category
          setSelectedCategory(firstCategory)
          setSelectedDataset(datasets[0].id)
        }
      })
      .catch(err => console.error('Error loading datasets:', err))
  }, [])

  useEffect(() => {
    // Filter datasets by category
    if (selectedCategory) {
      const filtered = datasets.filter(d => d.category === selectedCategory)
      setAvailableDatasets(filtered)
      
      // If current dataset is not in the new category, select the first one
      if (!filtered.find(d => d.id === selectedDataset) && filtered.length > 0) {
        setSelectedDataset(filtered[0].id)
      }
    }
  }, [selectedCategory, datasets])

  return (
    <div style={{
      padding: 24,
      height: '100%',
      overflow: 'auto',
      backgroundColor: '#f5f5f5'
    }}>
      <div style={{
        maxWidth: 1800,
        margin: '0 auto'
      }}>
        {/* Header with Controls */}
        <div style={{
          marginBottom: 24,
          padding: 20,
          backgroundColor: '#fff',
          borderRadius: 8,
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{
            margin: '0 0 16px 0',
            fontSize: 20,
            fontWeight: 600,
            color: '#333'
          }}>
            Algorithm PAE Plots
          </h2>
          <p style={{
            margin: '0 0 20px 0',
            fontSize: 14,
            color: '#666'
          }}>
            Level vs PAE plots for each algorithm
          </p>

          {/* Category and Dataset Selectors */}
          <div style={{ display: 'flex', gap: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ flex: '0 0 auto' }}>
              <label style={{
                display: 'block',
                fontSize: 12,
                fontWeight: 600,
                color: '#666',
                marginBottom: 6,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Category
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{
                  padding: '8px 32px 8px 12px',
                  border: '2px solid #e0e0e0',
                  borderRadius: 6,
                  fontSize: 14,
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                  minWidth: 200,
                  fontWeight: 500,
                  color: '#333',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#1E88E5'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>
                    {cat.replace(/_/g, ' ')}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ flex: '1 1 auto', minWidth: 250 }}>
              <label style={{
                display: 'block',
                fontSize: 12,
                fontWeight: 600,
                color: '#666',
                marginBottom: 6,
                textTransform: 'uppercase',
                letterSpacing: '0.5px'
              }}>
                Dataset
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                style={{
                  padding: '8px 32px 8px 12px',
                  border: '2px solid #e0e0e0',
                  borderRadius: 6,
                  fontSize: 14,
                  backgroundColor: '#fff',
                  cursor: 'pointer',
                  width: '100%',
                  fontWeight: 500,
                  color: '#333',
                  fontFamily: 'monospace',
                  outline: 'none',
                  transition: 'border-color 0.2s'
                }}
                onFocus={(e) => e.target.style.borderColor = '#1E88E5'}
                onBlur={(e) => e.target.style.borderColor = '#e0e0e0'}
              >
                {availableDatasets.map(dataset => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.id}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Gallery Grid */}
        {selectedDataset && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))',
            gap: 20,
            alignItems: 'start'
          }}>
            {ALGORITHMS.map(algorithm => {
              const algorithmColor = getAlgorithmColor(algorithm)
              const algorithmName = getAlgorithmName(algorithm)
              
              return (
                <div
                  key={algorithm}
                  style={{
                    backgroundColor: '#fff',
                    borderRadius: 8,
                    padding: 16,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    transition: 'all 0.2s',
                    cursor: 'default',
                    border: '1px solid #e0e0e0'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'
                    e.currentTarget.style.transform = 'translateY(-2px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'
                    e.currentTarget.style.transform = 'translateY(0)'
                  }}
                >
                  {/* Algorithm Name */}
                  <div style={{
                    marginBottom: 12,
                    paddingBottom: 10,
                    borderBottom: `3px solid ${algorithmColor}`
                  }}>
                    <h3 style={{
                      margin: 0,
                      fontSize: 14,
                      fontWeight: 600,
                      color: algorithmColor,
                      fontFamily: 'monospace',
                      letterSpacing: '-0.3px'
                    }}>
                      {algorithmName}
                    </h3>
                  </div>

                  {/* PNG Image */}
                  <div style={{
                    width: '100%',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    backgroundColor: '#fafafa',
                    borderRadius: 4,
                    overflow: 'hidden',
                    minHeight: 200
                  }}>
                    <img
                      src={`${CDN_URLS.precomputed}/${selectedDataset}/plots/${algorithm}_level_vs_pae.png`}
                      alt={`${algorithmName} level vs PAE`}
                      style={{
                        width: '100%',
                        height: 'auto',
                        display: 'block'
                      }}
                      onError={(e) => {
                        const img = e.target as HTMLImageElement
                        img.style.display = 'none'
                        const parent = img.parentElement
                        if (parent) {
                          parent.innerHTML = `
                            <div style="padding: 40px; text-align: center; color: #999; font-size: 13px;">
                              <div style="margin-bottom: 8px;">⚠️</div>
                              <div>Plot not available</div>
                            </div>
                          `
                        }
                      }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {!selectedDataset && (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: '#999',
            fontSize: 16
          }}>
            Select a dataset to view plots
          </div>
        )}
      </div>
    </div>
  )
}
