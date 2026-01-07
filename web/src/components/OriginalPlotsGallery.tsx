import React, { useState, useEffect } from 'react'
import { getPlotUrl } from '../config/cdn';
import { getDatasets } from '../api';

interface Dataset {
  name: string
  category: string
}

export default function OriginalPlotsGallery() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [filter, setFilter] = useState<string>('all')
  const [categories, setCategories] = useState<string[]>([])

  useEffect(() => {
    // Load all datasets using API helper (handles local vs CDN)
    getDatasets()
      .then(data => {
        // data is an array of {id, n, category}
        const allCategories = new Set<string>()
        
        data.forEach((item: any) => {
          allCategories.add(item.category)
        })
        
        const datasets: Dataset[] = data.map((item: any) => ({
          name: item.id,
          category: item.category
        }))
        
        setDatasets(datasets.sort((a, b) => a.name.localeCompare(b.name)))
        setCategories(['all', ...Array.from(allCategories).sort()])
      })
      .catch(err => console.error('Error loading datasets:', err))
  }, [])

  const filteredDatasets = filter === 'all' 
    ? datasets 
    : datasets.filter(d => d.category === filter)

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
        {/* Header */}
        <div style={{
          marginBottom: 24,
          padding: 20,
          backgroundColor: '#fff',
          borderRadius: 8,
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h2 style={{
            margin: '0 0 12px 0',
            fontSize: 20,
            fontWeight: 600,
            color: '#333'
          }}>
            Original Datasets Gallery
          </h2>
          <p style={{
            margin: '0 0 16px 0',
            fontSize: 14,
            color: '#666'
          }}>
            Showing {filteredDatasets.length} dataset{filteredDatasets.length !== 1 ? 's' : ''}
          </p>

          {/* Category Filter */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                style={{
                  padding: '6px 14px',
                  border: 'none',
                  borderRadius: 16,
                  backgroundColor: filter === cat ? '#1E88E5' : '#e0e0e0',
                  color: filter === cat ? '#fff' : '#666',
                  fontSize: 13,
                  fontWeight: filter === cat ? 600 : 400,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {cat === 'all' ? 'All Categories' : cat.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Gallery Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(520px, 1fr))',
          gap: 20,
          alignItems: 'start'
        }}>
          {filteredDatasets.map(dataset => (
            <div
              key={dataset.name}
              style={{
                backgroundColor: '#fff',
                borderRadius: 8,
                padding: 20,
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
              {/* Dataset Name */}
              <div style={{
                marginBottom: 12,
                paddingBottom: 12,
                borderBottom: '2px solid #f0f0f0'
              }}>
                <h3 style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 600,
                  color: '#1E88E5',
                  fontFamily: 'monospace',
                  letterSpacing: '-0.5px'
                }}>
                  {dataset.name}
                </h3>
                <p style={{
                  margin: '4px 0 0 0',
                  fontSize: 11,
                  color: '#999',
                  textTransform: 'uppercase',
                  fontWeight: 600,
                  letterSpacing: '0.5px'
                }}>
                  {dataset.category.replace(/_/g, ' ')}
                </p>
              </div>

              {/* SVG Image */}
              <div style={{
                width: '100%',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                backgroundColor: '#fafafa',
                borderRadius: 4,
                overflow: 'hidden'
              }}>
                <img
                  src={getPlotUrl(`original/${dataset.name}.svg`)}
                  alt={dataset.name}
                  style={{
                    width: '100%',
                    height: 'auto',
                    display: 'block'
                  }}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                    const parent = (e.target as HTMLElement).parentElement;
                    if (parent) {
                      parent.innerHTML = '<div style="padding: 40px; text-align: center; color: #999;">Image not found</div>';
                    }
                  }}
                />
              </div>
            </div>
          ))}
        </div>

        {filteredDatasets.length === 0 && (
          <div style={{
            textAlign: 'center',
            padding: 60,
            color: '#999',
            fontSize: 16
          }}>
            No datasets found
          </div>
        )}
      </div>
    </div>
  )
}
