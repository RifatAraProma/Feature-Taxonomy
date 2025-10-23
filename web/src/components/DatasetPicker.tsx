import React, {useEffect, useState} from 'react'
import { getDatasets } from '../api'

interface Dataset {
  id: string;
  n: number;
  category?: string;
}

export default function DatasetPicker({value, onChange}:{value:string, onChange:(v:string)=>void}){
  const [list, setList] = useState<Dataset[]>([])
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  
  useEffect(()=>{ 
    getDatasets().then((datasets) => {
      setList(datasets)
      // Set initial category based on current value
      const current = datasets.find(d => d.id === value);
      if (current && current.category) {
        setSelectedCategory(current.category);
      }
    }) 
  }, [])
  
  // Group datasets by category
  const groupedDatasets = list.reduce((acc, dataset) => {
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
  const filteredDatasets = selectedCategory === 'all' 
    ? list 
    : (groupedDatasets[selectedCategory] || []);
  
  // Handle category change
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    // Auto-select first dataset in new category
    if (category !== 'all' && groupedDatasets[category] && groupedDatasets[category].length > 0) {
      onChange(groupedDatasets[category][0].id);
    }
  };
  
  return (
    <div style={{display: 'flex', flexDirection: 'column', gap: 16}}>
      {/* Category Section */}
      <div style={{
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderRadius: 8,
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: 14,
          fontWeight: 600,
          color: '#333',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Dataset Category
        </h3>
        <select 
          value={selectedCategory} 
          onChange={e => handleCategoryChange(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            fontSize: 14,
            borderRadius: 6,
            border: '1px solid #ccc',
            backgroundColor: '#fff',
            cursor: 'pointer',
            fontWeight: 500
          }}
        >
          <option value="all">All Categories ({list.length})</option>
          {categories.map(cat => (
            <option key={cat} value={cat}>
              {cat.toUpperCase()} ({groupedDatasets[cat].length})
            </option>
          ))}
        </select>
      </div>
      
      {/* Dataset File Section */}
      <div style={{
        padding: 16,
        backgroundColor: '#f8f9fa',
        borderRadius: 8,
        border: '1px solid #e0e0e0'
      }}>
        <h3 style={{
          margin: '0 0 12px 0',
          fontSize: 14,
          fontWeight: 600,
          color: '#333',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Data File
        </h3>
        <select 
          value={value} 
          onChange={e => onChange(e.target.value)}
          style={{
            width: '100%',
            padding: '10px 12px',
            fontSize: 14,
            borderRadius: 6,
            border: '1px solid #ccc',
            backgroundColor: '#fff',
            cursor: 'pointer',
            maxHeight: 200
          }}
        >
          {filteredDatasets.map(d => (
            <option key={d.id} value={d.id}>
              {d.id} ({d.n.toLocaleString()} points)
            </option>
          ))}
        </select>
        
        {filteredDatasets.length === 0 && (
          <div style={{
            marginTop: 8,
            padding: 8,
            fontSize: 13,
            color: '#666',
            fontStyle: 'italic'
          }}>
            No datasets in this category
          </div>
        )}
        
        {/* Dataset Info */}
        {filteredDatasets.find(d => d.id === value) && (
          <div style={{
            marginTop: 12,
            padding: 12,
            backgroundColor: '#e3f2fd',
            borderRadius: 6,
            fontSize: 13
          }}>
            <div style={{fontWeight: 600, color: '#1976d2', marginBottom: 4}}>
              Selected: {value}
            </div>
            <div style={{color: '#555'}}>
              {filteredDatasets.find(d => d.id === value)?.n.toLocaleString()} data points
            </div>
            {selectedCategory !== 'all' && (
              <div style={{color: '#555', fontSize: 12, marginTop: 4}}>
                Category: {selectedCategory.toUpperCase()}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}