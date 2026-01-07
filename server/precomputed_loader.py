"""
Module for loading and accessing precomputed algorithm outputs from individual level files.

New Structure (individual files per level):
    precomputed/
        dataset_name/
            algorithm_level_0.json
            algorithm_level_1.json
            ...
            algorithm_level_100.json

Each JSON contains: {level, parameter_name, parameter_value, output_length, output, pae}
"""

import json
import os
from pathlib import Path

class PrecomputedLoader:
    def __init__(self, precomputed_dir='precomputed'):
        # Check for production environment variable first
        if os.getenv('PRECOMPUTED_DATA_PATH'):
            self.precomputed_dir = Path(os.getenv('PRECOMPUTED_DATA_PATH'))
        # Handle relative path from server directory
        elif not Path(precomputed_dir).is_absolute():
            # Assume running from server directory, so go up one level
            self.precomputed_dir = Path(__file__).parent.parent / precomputed_dir
        else:
            self.precomputed_dir = Path(precomputed_dir)
        self.cache = {}  # Cache loaded files: (dataset, algorithm, level) -> data
        self.metadata_cache = {}  # Cache metadata: (dataset, algorithm) -> {num_levels, param_name}
        
    def _normalize_dataset_name(self, dataset_id):
        """Normalize dataset name by replacing / with _"""
        return dataset_id.replace('/', '_')
    
    def _get_dataset_dir(self, dataset_id):
        """Find the actual dataset directory, trying normalized name and fuzzy matching."""
        normalized_dataset = self._normalize_dataset_name(dataset_id)
        dir_path = self.precomputed_dir / normalized_dataset
        
        if dir_path.exists() and dir_path.is_dir():
            return dir_path
        
        # Try fuzzy matching - find a directory that ends with the dataset_id
        for candidate in self.precomputed_dir.iterdir():
            if candidate.is_dir() and candidate.name.endswith(normalized_dataset):
                return candidate
        
        return None
    
    def _scan_algorithm_levels(self, dataset_id, algorithm):
        """Scan directory to find all level files for an algorithm and build metadata.
        
        Supports both new format (shared level_0.json) and old format (algorithm_level_0.json).
        """
        cache_key = (dataset_id, algorithm)
        if cache_key in self.metadata_cache:
            return self.metadata_cache[cache_key]
        
        dataset_dir = self._get_dataset_dir(dataset_id)
        if not dataset_dir:
            self.metadata_cache[cache_key] = None
            return None
        
        # Find all level files: algorithm_level_N.json
        level_files = sorted(dataset_dir.glob(f"{algorithm}_level_*.json"))
        
        if not level_files:
            self.metadata_cache[cache_key] = None
            return None
        
        # Load first level file to get parameter name
        first_level_data = None
        try:
            with open(level_files[0], 'r') as f:
                first_level_data = json.load(f)
        except Exception as e:
            print(f"Error loading first level for {algorithm}: {e}")
            self.metadata_cache[cache_key] = None
            return None
        
        param_name = first_level_data.get('parameter_name', 'param') if first_level_data else 'param'
        
        # Count total levels based on actual files that exist
        num_levels = len(level_files)
        
        metadata = {
            'num_levels': num_levels,
            'param_name': param_name,
            'dataset_dir': dataset_dir
        }
        self.metadata_cache[cache_key] = metadata
        return metadata
    
    def _load_level_file(self, dataset_id, algorithm, level):
        """Load a specific level file for a dataset and algorithm."""
        cache_key = (dataset_id, algorithm, level)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        dataset_dir = self._get_dataset_dir(dataset_id)
        if not dataset_dir:
            self.cache[cache_key] = None
            return None
        
        # Load algorithm-specific file (algorithm_level_X.json)
        file_path = dataset_dir / f"{algorithm}_level_{level}.json"
        
        if not file_path.exists():
            self.cache[cache_key] = None
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            self.cache[cache_key] = None
            return None
    
    def has_precomputed(self, dataset_id, algorithm):
        """
        Check if precomputed output exists for dataset and algorithm.
        
        Args:
            dataset_id: Dataset identifier (e.g., 'stock_aapl_price' or 'stock_price/stock_aapl_price')
            algorithm: Algorithm name (e.g., 'gaussian_filter')
        
        Returns:
            bool: True if precomputed data exists
        """
        metadata = self._scan_algorithm_levels(dataset_id, algorithm)
        return metadata is not None
    
    def get_precomputed_output(self, dataset_id, algorithm, level):
        """
        Get precomputed output for a specific level.
        
        Args:
            dataset_id: Dataset identifier
            algorithm: Algorithm name
            level: Level index (0 to num_levels-1)
        
        Returns:
            dict with keys: output, param_name, param_value, pae, num_levels, features, feature_preservation
            Returns None if not found or level out of range
        """
        metadata = self._scan_algorithm_levels(dataset_id, algorithm)
        if not metadata:
            return None
        
        # Validate 0-based level range
        if level < 0 or level >= metadata['num_levels']:
            return None
        
        level_data = self._load_level_file(dataset_id, algorithm, level)
        if not level_data:
            return None
        
        return {
            'output': level_data.get('output'),
            'param_name': metadata['param_name'],
            'param_value': level_data.get('parameter_value'),
            'pae': level_data.get('pae'),
            'output_length': level_data.get('output_length'),
            'num_levels': metadata['num_levels'],
            'features': level_data.get('features', {}),
            'feature_preservation': level_data.get('feature_preservation', {})
        }
    
    def get_algorithm_info(self, dataset_id, algorithm):
        """
        Get metadata about precomputed algorithm outputs.
        
        Args:
            dataset_id: Dataset identifier
            algorithm: Algorithm name
        
        Returns:
            dict with keys: param_name, num_levels, param_values (list of all values), pae_values (list of all PAE)
            Returns None if not found
        """
        metadata = self._scan_algorithm_levels(dataset_id, algorithm)
        if not metadata:
            return None
        
        # Collect parameter values and PAE values from all levels (0-based)
        param_values = []
        pae_values = []
        for level in range(metadata['num_levels']):
            level_data = self._load_level_file(dataset_id, algorithm, level)
            if level_data:
                param_values.append(level_data.get('parameter_value'))
                pae_values.append(level_data.get('pae'))
        
        return {
            'param_name': metadata['param_name'],
            'num_levels': metadata['num_levels'],
            'param_values': param_values,
            'pae_values': pae_values
        }

# Singleton instance
_loader = None

def _get_loader():
    global _loader
    if _loader is None:
        _loader = PrecomputedLoader()
    return _loader

# Module-level convenience functions
def has_precomputed(dataset_id, algorithm):
    """Check if precomputed output exists."""
    return _get_loader().has_precomputed(dataset_id, algorithm)

def get_precomputed_output(dataset_id, algorithm, level):
    """Get precomputed output for a specific level."""
    return _get_loader().get_precomputed_output(dataset_id, algorithm, level)

def get_algorithm_info(dataset_id, algorithm):
    """Get metadata about precomputed algorithm outputs."""
    return _get_loader().get_algorithm_info(dataset_id, algorithm)
