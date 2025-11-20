# server/features/compute_features.py
"""
Visual Feature Extraction for Time Series Line Charts

This module computes visual features based on the definitions in the SVG reference files
located in web/src/figures/Visual features/.

Features (12 total):
1. Level - Point values and interval averages
2. Mean - Overall average value
3. Extrema - Local minima and maxima
4. Regime & Change Points - Plateaus and transitions
5. Spikes & Dips - Local outliers
6. Slope - First derivative (rate of change)
7. Curvature - Second derivative (bend)
8. Trend - Low-frequency component
9. Regression Fit - Linear trend line
10. Periodicity - Dominant frequency
11. Roughness - High-frequency variation
12. Noise - High-frequency residual

Author: Feature Taxonomy Team
Date: November 2025
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy import signal, fft
import scipy.fftpack as scifft
import persim




# ============================================================================
# Configuration
# ============================================================================

@dataclass
class FeatureConfig:
    """Configuration parameters for feature extraction."""
    
    # Spikes & Dips
    spike_window: int = 21          # Window size for local outlier detection
    spike_threshold: float = 3.0     # Standard deviation multiplier
    
    # Regime & Change Points
    regime_n_bkps: Optional[int] = None     # Number of breakpoints (manual override)
    regime_min_len: int = 20                # Minimum points per regime (for meaningful segments)
    
    # Trend & Noise (spectral)
    cutoff_ratio: float = 0.15       # Fraction of Nyquist frequency
    
    # Interval averaging (optional)
    intervals: Optional[List[Tuple[int, int]]] = None  # 1-based inclusive


# ============================================================================
# Helper Functions
# ============================================================================

def _interpolate_to_match_length(y_short: np.ndarray, target_length: int) -> np.ndarray:
    """
    Interpolate a shorter series to match a target length.
    
    Used for comparing series of different lengths (e.g., after reduction/aggregation).
    Uses linear interpolation to estimate values at intermediate points.
    
    Args:
        y_short: The shorter series to interpolate
        target_length: Desired output length
        
    Returns:
        Interpolated series of length target_length
    """
    if len(y_short) == target_length:
        return y_short
    
    if len(y_short) == 0:
        return np.zeros(target_length)
    
    # Create x-coordinates for original and target series
    x_original = np.linspace(0, 1, len(y_short))
    x_target = np.linspace(0, 1, target_length)
    
    # Linear interpolation
    y_interpolated = np.interp(x_target, x_original, y_short)
    
    return y_interpolated


# ============================================================================
# FEATURE 1: LEVEL
# ============================================================================

def compute_level(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Extract level features: point values and interval averages.
    
    Reference: web/src/figures/Visual features/level.svg
    
    Level represents the y-values of the time series at each point.
    For comparison purposes, we store all point values.
    
    Returns:
        Dictionary containing:
        - point_values: Array of all y-values (float list)
    """
    return {
        "point_values": y.tolist()
    }


# ============================================================================
# FEATURE 2: MEAN
# ============================================================================

def compute_mean(y: np.ndarray) -> Dict[str, Any]:
    """
    Compute the overall mean value of the time series.
    
    Reference: web/src/figures/Visual features/mean.svg
    
    Returns:
        Dictionary containing:
        - value: The mean value
    """
    # TODO: Implement based on mean.svg
    return {
        "value": float(np.mean(y))
    }


# ============================================================================
# FEATURE 3: EXTREMA
# ============================================================================

def compute_extrema(y: np.ndarray) -> Dict[str, Any]:
    """
    Detect local minima and maxima.
    
    Reference: web/src/figures/Visual features/extrema.svg
    
    Returns:
        Dictionary containing:
        - minima: List of {t, y, type} for local minima
        - maxima: List of {t, y, type} for local maxima
        - all_extrema: Combined list of all extrema
        - persistence_diagram: 2D array for topological analysis (birth, death pairs)
    """
    from .extrema import find_extrema
    
    # Optimized: find_extrema now returns separate lists, avoiding redundant filtering
    minima, maxima, all_extrema = find_extrema(y)
    
    # Create persistence diagram for topological analysis
    # Format: array of [birth, death] pairs
    # For extrema: birth = min value, death = max value (or vice versa)
    persistence_diagram = _create_persistence_diagram_from_extrema(all_extrema, y)
    
    # Convert NumPy array to list for JSON serialization
    if isinstance(persistence_diagram, np.ndarray):
        persistence_diagram = persistence_diagram.tolist()
    
    return {
        "minima": minima,
        "maxima": maxima,
        "all_extrema": all_extrema,
        "persistence_diagram": persistence_diagram
    }


def _create_persistence_diagram_from_extrema(extrema: List[Dict], y: np.ndarray) -> np.ndarray:
    """
    Convert extrema to persistence diagram format for topological distance computation.
    
    Persistence diagrams represent topological features as (birth, death) pairs.
    For extrema in time series:
    - Each local maximum corresponds to a topological feature
    - Birth = value at the saddle point (between min neighbors)
    - Death = value at the maximum
    
    Args:
        extrema: List of extrema points with 't', 'y', 'type' (already time-ordered)
        y: Original time series
        
    Returns:
        np.ndarray of shape (n_features, 2) with [birth, death] pairs
    """
    if not extrema:
        return np.array([[0.0, 0.0]], dtype=np.float32)  # Return trivial diagram
    
    # Optimized: Extrema are already time-ordered from find_extrema(), no need to sort
    # Build persistence pairs from extrema
    pairs = []
    
    for i in range(len(extrema) - 1):
        curr = extrema[i]
        next_pt = extrema[i + 1]
        
        # Create birth-death pair
        if curr["type"] == "min" and next_pt["type"] == "max":
            # Birth at minimum, death at maximum
            pairs.append([curr["y"], next_pt["y"]])
        elif curr["type"] == "max" and next_pt["type"] == "min":
            # Birth at minimum, death at maximum (flipped)
            pairs.append([next_pt["y"], curr["y"]])
    
    if not pairs:
        # If no pairs, use extrema values directly
        extrema_values = [e["y"] for e in extrema]
        if len(extrema_values) >= 2:
            min_val = min(extrema_values)
            max_val = max(extrema_values)
            pairs.append([min_val, max_val])
        else:
            pairs.append([0.0, 0.0])
    
    return np.array(pairs, dtype=np.float32)


# ============================================================================
# FEATURE 4: REGIME & CHANGE POINTS
# ============================================================================

def compute_regimes(y: np.ndarray, cfg: "FeatureConfig") -> Dict[str, Any]:
    """
    Detect regimes using ruptures library with fixed breakpoint strategy.
    
    - Regimes = intervals with constant mean baseline
    - Change-points = boundaries where the mean shifts
    
    Uses a simple, fast approach:
    - Fixed 5 breakpoints for interpretability and speed
    - Pelt algorithm with minimum segment length of 50 points
    - L2 cost (mean shift detection)
    
    This gives 3-6 major regimes which is visually meaningful.
    
    Reference: web/src/figures/Visual features/regime_change_points.svg
    
    Args:
        y: Time series data
        cfg: Configuration (n_bkps and min_len can override defaults)
        
    Returns:
        Dictionary containing:
        - regimes: List of {start, end, baseline_mean} for each regime
        - change_points: List of indices where regime changes occur
        - num_regimes: Total number of regimes detected
        - num_change_points: Total number of change points detected
        - n_bkps_used: The number of breakpoints that was used
    """
    y = np.asarray(y)
    n = len(y)
    
    try:
        # Simple fixed strategy: 5 breakpoints for interpretability
        # This gives 3-6 major regimes which is visually meaningful
        n_bkps = cfg.regime_n_bkps if cfg.regime_n_bkps is not None else 5
        min_size = cfg.regime_min_len  # Default 20
        
        # Handle edge cases
        if n < min_size * 2 or n_bkps <= 0:
            # Too short for meaningful segmentation
            return {
                "regimes": [{
                    "start": 0,
                    "end": n - 1,
                    "baseline_mean": float(np.mean(y))
                }],
                "change_points": [],
                "num_regimes": 1,
                "num_change_points": 0,
                "n_bkps_used": 0
            }
        
        # Use Pelt algorithm with L2 cost (fast and effective for mean shifts)
        # Pelt is O(n) on average, much faster than DP which is O(n²)
        algo = rpt.Pelt(model="l2", min_size=min_size).fit(y)
        
        # Predict with penalty parameter
        # Higher penalty = fewer breakpoints
        # We use n_bkps parameter but ruptures uses penalty
        # Heuristic: penalty ≈ 3 * variance works well
        penalty_value = 3 * np.var(y) if np.var(y) > 0 else 1.0
        
        try:
            bkps = algo.predict(pen=penalty_value)
        except Exception:
            # Fallback: use simpler Dynp with fixed n_bkps
            algo = rpt.Dynp(model="l2", min_size=min_size).fit(y)
            bkps = algo.predict(n_bkps=min(n_bkps, (n // min_size) - 1))
        
        # bkps includes the last index (n), remove it
        if bkps and bkps[-1] == n:
            bkps = bkps[:-1]
        
        change_points = sorted(bkps)
        
        # Build regimes from breakpoints
        regimes = []
        regime_starts = [0] + change_points
        regime_ends = change_points + [n]
        
        for start, end in zip(regime_starts, regime_ends):
            regime_data = y[start:end]
            regimes.append({
                "start": int(start),
                "end": int(end - 1),  # Inclusive end
                "baseline_mean": float(np.mean(regime_data))
            })
        
        return {
            "regimes": regimes,
            "change_points": [int(cp) for cp in change_points],
            "num_regimes": len(regimes),
            "num_change_points": len(change_points),
            "n_bkps_used": len(change_points)
        }
        
    except ImportError:
        # Fallback if ruptures not installed: single regime
        return {
            "regimes": [{
                "start": 0,
                "end": n - 1,
                "baseline_mean": float(np.mean(y))
            }],
            "change_points": [],
            "num_regimes": 1,
            "num_change_points": 0,
            "n_bkps_used": 0
        }
    except Exception as e:
        # Any other error: single regime
        return {
            "regimes": [{
                "start": 0,
                "end": n - 1,
                "baseline_mean": float(np.mean(y))
            }],
            "change_points": [],
            "num_regimes": 1,
            "num_change_points": 0,
            "n_bkps_used": 0
        }


# ============================================================================
# FEATURE 5: SPIKES & DIPS
# ============================================================================

def compute_spikes_dips(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Detect local outliers (spikes and dips).
    
    Reference: web/src/figures/Visual features/spikes_dips.svg
    
    Returns:
        Dictionary containing:
        - spikes: List of {index, value} for upward outliers
        - dips: List of {index, value} for downward outliers
    """
    # TODO: Implement based on spikes_dips.svg
    return {
        "spikes": [],
        "dips": []
    }


# ============================================================================
# FEATURE 6: SLOPE
# ============================================================================

def compute_slope(y: np.ndarray) -> Dict[str, Any]:
    """
    Compute first derivative (rate of change) as absolute differences between consecutive points.
    
    Slope[i] = |y[i+1] - y[i]| for i in [0, n-2]
    
    Reference: web/src/figures/Visual features/slope.svg
    
    Returns:
        Dictionary containing:
        - values: Array of absolute slope values (length n-1)
        - mean_slope: Average absolute slope
    """
    y = np.asarray(y, dtype=float)
    
    if len(y) < 2:
        return {
            "values": [],
            "mean_slope": 0.0
        }
    
    # Compute absolute differences between consecutive points
    slope_values = np.abs(np.diff(y))
    
    return {
        "values": slope_values.tolist(),
        "mean_slope": float(np.mean(slope_values))
    }


# ============================================================================
# FEATURE 7: CURVATURE
# ============================================================================

def compute_curvature(y: np.ndarray) -> Dict[str, Any]:
    """
    Compute second derivative (curvature/bend).
    
    Reference: web/src/figures/Visual features/curvature.svg
    
    Returns:
        Dictionary containing:
        - values: Array of curvature values
        - mean_curvature: Average curvature
    """
    # TODO: Implement based on curvature.svg
    return {
        "values": [],
        "mean_curvature": 0.0
    }


# ============================================================================
# FFT-BASED SPECTRAL FEATURES (COMBINED COMPUTATION)
# ============================================================================

def compute_spectral_features(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Compute all spectral features (trend, periodicity, noise) in a single pass.
    
    This function performs FFT once and extracts all three spectral features,
    which is much more efficient than computing them separately.
    
    Process:
    1. Perform FFT once on the offset time series
    2. Extract trend from low frequencies
    3. Extract periodicity from dominant frequency
    4. Extract noise from high-frequency components
    
    Args:
        y: Time series data
        cfg: Feature configuration
        
    Returns:
        Dictionary containing:
        - trend: Trend component (dict with 'trend' array and 'cutoff_freq')
        - periodicity: Periodicity analysis (dict with frequency info)
        - noise: Noise component (dict with 'noise' array and 'energy')
    """
    try:
        n = len(y)
        
        # Handle edge cases
        if n < 2:
            return {
                "trend": {"trend": y.tolist(), "cutoff_freq": 0},
                "periodicity": {"dominant_frequency_index": 0, "amplitude": 0.0, "num_periods": 0.0},
                "noise": {"values": y.tolist(), "energy": 0.0}
            }
        
        # ===== STEP 1: Perform FFT once =====
        avg_y = np.mean(y)
        offset = abs(avg_y)
        y_offset = y + offset
        fft_y = fft.rfft(y_offset)
        
        # ===== STEP 2: Extract TREND (low frequencies) =====
        max_x = float(n - 1)
        if max_x > 0:
            log_max_x = np.log10(max_x)
            cutoff_fraction = 1.0 / 3.0  # Use 1/3 for low-frequency trend
            cutoff_freq = int(10 ** (cutoff_fraction * log_max_x))
        else:
            cutoff_freq = 1
        
        cutoff_freq = max(1, min(cutoff_freq, len(fft_y) - 1))
        
        # Filter and inverse FFT for trend
        fft_y_filtered = fft_y.copy()
        fft_y_filtered[cutoff_freq:] = 0
        trend_values = fft.irfft(fft_y_filtered, n=n)
        trend_values = trend_values - offset
        
        trend_result = {
            "trend": trend_values.tolist(),
            "cutoff_freq": int(cutoff_freq)
        }
        
        # ===== STEP 3: Extract PERIODICITY (dominant frequency) =====
        if n < 4:
            periodicity_result = {
                "dominant_frequency_index": 0,
                "amplitude": 0.0,
                "num_periods": 0.0
            }
        else:
            # Exclude DC component (first element)
            fft_y_no_dc = fft_y[1:]
            
            # Find dominant frequency in range [2:100]
            search_end = min(100, len(fft_y_no_dc))
            if search_end <= 2:
                max_freq_index = 0
            else:
                max_freq_index = np.argmax(np.abs(fft_y_no_dc[2:search_end])) + 2
            
            # Calculate amplitude and periods
            if max_freq_index < len(fft_y_no_dc):
                max_freq_amplitude = float(np.abs(fft_y_no_dc[max_freq_index]) / n)
            else:
                max_freq_amplitude = 0.0
            
            num_periods = float(max_freq_index) if max_freq_index > 0 else 0.0
            
            periodicity_result = {
                "dominant_frequency_index": int(max_freq_index),
                "amplitude": max_freq_amplitude,
                "num_periods": num_periods
            }
        
        # ===== STEP 4: Extract NOISE (high frequencies) =====
        # Use scipy's rfft for consistency with original implementation
        fft_y_scipy = scifft.rfft(y_offset)
        
        # Calculate noise cutoff (2/3 of log scale, opposite of trend)
        if max_x > 0:
            noise_cutoff_fraction = 2.0 / 3.0
            noise_cutoff_freq = int(10 ** (noise_cutoff_fraction * log_max_x))
        else:
            noise_cutoff_freq = 1
        
        noise_cutoff_freq = max(1, min(noise_cutoff_freq, len(fft_y_scipy) - 1))
        
        # Keep only high frequencies (zero out low frequencies)
        fft_y_noise = fft_y_scipy.copy()
        fft_y_noise[:noise_cutoff_freq] = 0
        
        # Inverse FFT to get noise
        noise_values = scifft.irfft(fft_y_noise, n=n)
        noise_values = noise_values - offset
        
        # Calculate noise energy
        noise_energy = float(np.sum(noise_values ** 2))
        
        noise_result = {
            "values": noise_values.tolist(),
            "energy": noise_energy
        }
        
        return {
            "trend": trend_result,
            "periodicity": periodicity_result,
            "noise": noise_result
        }
    
    except Exception as e:
        print(f"Error computing spectral features: {e}")
        return {
            "trend": {"trend": np.zeros(len(y)).tolist(), "cutoff_freq": 0},
            "periodicity": {"dominant_frequency_index": 0, "amplitude": 0.0, "num_periods": 0.0},
            "noise": {"values": np.zeros(len(y)).tolist(), "energy": 0.0}
        }


# ============================================================================
# FEATURE 8: TREND
# ============================================================================

def compute_trend(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Extract low-frequency trend component via FFT-based spectral filtering.
    
    NOTE: This now delegates to compute_spectral_features() for efficiency.
    All spectral features (trend, periodicity, noise) are computed together.
    
    Reference: web/src/figures/Visual features/trend.svg
    
    Returns:
        Dictionary containing:
        - trend: Array of trend values (same length as input)
        - cutoff_freq: The cutoff frequency index used
    """
    # Delegate to combined spectral features computation
    spectral = compute_spectral_features(y, cfg)
    return spectral["trend"]


# ============================================================================
# FEATURE 9: REGRESSION FIT
# ============================================================================

def compute_regression(y: np.ndarray) -> Dict[str, Any]:
    """
    Fit linear regression line (OLS).
    
    Reference: web/src/figures/Visual features/regression_fit.svg
    
    Returns:
        Dictionary containing:
        - slope: Regression slope (beta)
        - intercept: Regression intercept (alpha)
        - r_squared: Coefficient of determination
    """
    # TODO: Implement based on regression_fit.svg
    return {
        "slope": 0.0,
        "intercept": 0.0,
        "r_squared": 0.0
    }


# ============================================================================
# FEATURE 10: PERIODICITY
# ============================================================================

def compute_periodicity(y: np.ndarray) -> Dict[str, Any]:
    """
    Detect dominant frequency via FFT.
    
    NOTE: This now delegates to compute_spectral_features() for efficiency.
    All spectral features (trend, periodicity, noise) are computed together.
    
    Reference: web/src/figures/Visual features/periodicity.svg
    
    Returns:
        Dictionary containing:
        - dominant_frequency_index: Index of dominant frequency component
        - amplitude: Amplitude of dominant frequency (normalized by length)
        - num_periods: Number of complete periods in the series
    """
    # Delegate to combined spectral features computation
    spectral = compute_spectral_features(y, FeatureConfig())
    return spectral["periodicity"]


# ============================================================================
# FEATURE 11: ROUGHNESS
# ============================================================================

def compute_roughness(y: np.ndarray) -> Dict[str, Any]:
    """
    Measure high-frequency variation (standard deviation of differences).
    
    Reference: web/src/figures/Visual features/roughness.svg
    
    Returns:
        Dictionary containing:
        - value: Roughness metric
    """
    # TODO: Implement based on roughness.svg
    return {
        "value": 0.0
    }


# ============================================================================
# FEATURE 12: NOISE
# ============================================================================

def compute_noise(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Extract high-frequency noise component via FFT-based spectral filtering.
    
    NOTE: This now delegates to compute_spectral_features() for efficiency.
    All spectral features (trend, periodicity, noise) are computed together.
    
    Reference: web/src/figures/Visual features/noise.svg
    
    Returns:
        Dictionary containing:
        - noise: Array of noise values (same length as input)
        - energy: Energy of noise component
    """
    # Delegate to combined spectral features computation
    spectral = compute_spectral_features(y, cfg)
    return spectral["noise"]


# ============================================================================
# Main Feature Computation
# ============================================================================

def compute_all_features(
    y: np.ndarray | List[float],
    cfg: Optional[FeatureConfig] = None
) -> Dict[str, Any]:
    """
    Compute all 12 visual features for a time series.
    
    Optimized to compute FFT once for all spectral features (trend, periodicity, noise).
    
    Args:
        y: Time series data (numpy array or list)
        cfg: Optional configuration parameters
        
    Returns:
        Dictionary with all computed features
    """
    if cfg is None:
        cfg = FeatureConfig()
    
    # Ensure numpy array
    if not isinstance(y, np.ndarray):
        y = np.array(y, dtype=float)
    
    # Optimization: Compute all spectral features (trend, periodicity, noise) in one pass
    # This performs FFT only once instead of three times
    spectral = compute_spectral_features(y, cfg)
    
    # Compute all features
    features = {
        "level": compute_level(y, cfg),
        "mean": compute_mean(y),
        "extrema": compute_extrema(y),
        "regimes": compute_regimes(y, cfg),
        "spikes_dips": compute_spikes_dips(y, cfg),
        "slope": compute_slope(y),
        "curvature": compute_curvature(y),
        "trend": spectral['trend'],         # ← From combined spectral computation
        "regression": compute_regression(y),
        "periodicity": spectral['periodicity'],  # ← From combined spectral computation
        "roughness": compute_roughness(y),
        "noise": spectral['noise']          # ← From combined spectral computation
    }
    
    return features


def compute_selective_features(
    y: np.ndarray,
    feature_names: List[str],
    cfg: Optional[FeatureConfig] = None
) -> Dict[str, Any]:
    """
    Compute only specific features instead of all features.
    
    Optimized to compute FFT once when multiple spectral features 
    (trend, periodicity, noise) are requested together.
    
    Args:
        y: Time series data
        feature_names: List of feature names to compute
        cfg: Feature configuration
    
    Returns:
        Dictionary with only the requested features
    """
    if cfg is None:
        cfg = FeatureConfig()
    
    # Ensure numpy array
    if not isinstance(y, np.ndarray):
        y = np.array(y, dtype=float)
    
    features = {}
    
    # Identify which spectral features are needed
    spectral_features_set = {'trend', 'periodicity', 'noise'}
    requested_spectral = spectral_features_set.intersection(set(feature_names))
    
    # Optimization: Compute all spectral features together if ANY are requested
    if len(requested_spectral) > 0 and len(y) >= 2:
        # Use combined spectral features computation (FFT done once)
        spectral = compute_spectral_features(y, cfg)
        
        # Extract only the requested spectral features
        if 'trend' in requested_spectral:
            features['trend'] = spectral['trend']
        
        if 'periodicity' in requested_spectral:
            features['periodicity'] = spectral['periodicity']
        
        if 'noise' in requested_spectral:
            features['noise'] = spectral['noise']
    
    # Map feature names to computation functions
    feature_map = {
        "level": lambda: compute_level(y, cfg),
        "mean": lambda: compute_mean(y),
        "extrema": lambda: compute_extrema(y),
        "regimes": lambda: compute_regimes(y, cfg),
        "change_points": lambda: compute_regimes(y, cfg),  # Same as regimes
        "spikes_dips": lambda: compute_spikes_dips(y, cfg),
        "slope": lambda: compute_slope(y),
        "curvature": lambda: compute_curvature(y),
        "trend": lambda: compute_trend(y, cfg),
        "regression": lambda: compute_regression(y),
        "periodicity": lambda: compute_periodicity(y),
        "roughness": lambda: compute_roughness(y),
        "noise": lambda: compute_noise(y, cfg)
    }
    
    # Metric-to-feature dependency mapping
    # Some preservation metrics require specific features to be computed
    metric_dependencies = {
        "extrema": "extrema",  # extrema metric needs extrema feature
        "spike_retention": "spikes_dips"
    }
    
    # Compute remaining features (skip already computed spectral features)
    for feature_name in feature_names:
        if feature_name in features:
            # Already computed via optimized path
            continue
        elif feature_name in feature_map:
            features[feature_name] = feature_map[feature_name]()
        elif feature_name == "change_points":
            # change_points is part of regimes
            if "regimes" not in features:
                features["regimes"] = compute_regimes(y, cfg)
        elif feature_name in metric_dependencies:
            # This is a metric name, compute the underlying feature it needs
            required_feature = metric_dependencies[feature_name]
            if required_feature not in features and required_feature in feature_map:
                features[required_feature] = feature_map[required_feature]()
    
    return features


# ============================================================================
# Feature Preservation Metrics (Placeholder)
# ============================================================================
def l1_norm(d0, d1):
    diff = np.subtract(d0, d1)
    return np.linalg.norm(diff, ord=1)


def l2_norm(d0, d1):
    diff = np.subtract(d0, d1)
    return np.linalg.norm(diff, ord=2)


def linf_norm(d0, d1):
    diff = np.subtract(d0, d1)
    return np.linalg.norm(diff, ord=np.inf)

def delta(d0, d1):
    diff = np.subtract(d0, d1)
    return abs(diff)

def _compute_level_metrics(
    original_values: List[float],
    simplified_values: List[float]
) -> Dict[str, float]:
    """
    Compute L1 and L∞ distance metrics for level preservation.
    
    Handles different-length series by interpolating the shorter one.
    
    Args:
        original_values: Point values from original series
        simplified_values: Point values from simplified series
        
    Returns:
        Dictionary with:
        - l1: Average absolute error (mean distance)
        - linf: Maximum absolute error (worst-case distance)
    """
    y_orig = np.array(original_values, dtype=float)
    y_simp = np.array(simplified_values, dtype=float)
    
    # Handle empty arrays
    if len(y_orig) == 0 or len(y_simp) == 0:
        return {"l1": 0.0, "linf": 0.0}
    
    # Interpolate if lengths differ
    if len(y_simp) != len(y_orig):
        y_simp = _interpolate_to_match_length(y_simp, len(y_orig))
    
    l1 = l1_norm(y_orig, y_simp)      # Average error
    linf = linf_norm(y_orig, y_simp)     # Worst-case error
    
    return {
        "l1": l1,
        "linf": linf
    }


def _compute_slope_metrics(
    original_slope_values: List[float],
    simplified_slope_values: List[float]
) -> Dict[str, float]:
    """
    Compute L1 and L∞ distance metrics for slope preservation.
    
    Compares the absolute consecutive differences (|y[i+1] - y[i]|) between
    original and simplified series.
    
    Handles different-length series by interpolating the shorter one.
    
    Args:
        original_slope_values: Slope values from original series
        simplified_slope_values: Slope values from simplified series
        
    Returns:
        Dictionary with:
        - l1: Average absolute error in slope
        - linf: Maximum absolute error in slope
    """
    slope_orig = np.array(original_slope_values, dtype=float)
    slope_simp = np.array(simplified_slope_values, dtype=float)
    
    # Handle empty arrays
    if len(slope_orig) == 0 or len(slope_simp) == 0:
        return {"l1": 0.0, "linf": 0.0}
    
    # Interpolate if lengths differ
    if len(slope_simp) != len(slope_orig):
        slope_simp = _interpolate_to_match_length(slope_simp, len(slope_orig))
    
    # Use existing helper functions for L1 and L∞ norms
    l1 = l1_norm(slope_orig, slope_simp)
    linf = linf_norm(slope_orig, slope_simp)
    
    return {
        "l1": l1,
        "linf": linf
    }


def _compute_trend_metrics(
    original_trend: List[float],
    simplified_trend: List[float]
) -> Dict[str, float]:
    """
    Compute L1 and L∞ distance metrics for trend preservation.
    
    Compares the trend values (low-frequency FFT components) between
    original and simplified series.
    
    Handles different-length series by interpolating the shorter one.
    
    Args:
        original_trend: Trend values from original series
        simplified_trend: Trend values from simplified series
        
    Returns:
        Dictionary with:
        - l1: Average absolute error in trend
        - linf: Maximum absolute error in trend
    """
    trend_orig = np.array(original_trend, dtype=float)
    trend_simp = np.array(simplified_trend, dtype=float)
    
    # Handle empty arrays
    if len(trend_orig) == 0 or len(trend_simp) == 0:
        return {"l1": 0.0, "linf": 0.0}
    
    # Interpolate if lengths differ
    if len(trend_simp) != len(trend_orig):
        trend_simp = _interpolate_to_match_length(trend_simp, len(trend_orig))
    
    # Use existing helper functions for L1 and L∞ norms
    l1 = l1_norm(trend_orig, trend_simp)
    linf = linf_norm(trend_orig, trend_simp)
    
    return {
        "l1": l1,
        "linf": linf
    }


def _compute_periodicity_metrics(
    original_periodicity: Dict[str, Any],
    simplified_periodicity: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute preservation metrics for periodicity.
    
    Compares:
    - Amplitude difference (absolute delta)
    - Number of periods difference (absolute delta)
    
    Args:
        original_periodicity: Periodicity from original series
        simplified_periodicity: Periodicity from simplified series
        
    Returns:
        Dictionary with:
        - amplitude_delta: Absolute difference in amplitude
        - num_periods_delta: Absolute difference in number of periods
    """
    orig_amplitude = original_periodicity.get("amplitude", 0.0)
    simp_amplitude = simplified_periodicity.get("amplitude", 0.0)
    
    orig_num_periods = original_periodicity.get("num_periods", 0.0)
    simp_num_periods = simplified_periodicity.get("num_periods", 0.0)
    
    amplitude_delta = abs(orig_amplitude - simp_amplitude)
    num_periods_delta = abs(orig_num_periods - simp_num_periods)
    
    return {
        "amplitude_delta": amplitude_delta,
        "num_periods_delta": num_periods_delta
    }


def _compute_noise_metrics(
    original_noise: List[float],
    simplified_noise: List[float]
) -> Dict[str, float]:
    """
    Compute L1 and L∞ distance metrics for noise preservation.
    
    Compares the noise values (high-frequency FFT components) between
    original and simplified series.
    
    Handles different-length series by interpolating the shorter one.
    
    Args:
        original_noise: Noise values from original series
        simplified_noise: Noise values from simplified series
        
    Returns:
        Dictionary with:
        - l1: Average absolute error in noise
        - linf: Maximum absolute error in noise
    """
    noise_orig = np.array(original_noise, dtype=float)
    noise_simp = np.array(simplified_noise, dtype=float)
    
    # Handle empty arrays
    if len(noise_orig) == 0 or len(noise_simp) == 0:
        return {"l1": 0.0, "linf": 0.0}
    
    # Interpolate if lengths differ
    if len(noise_simp) != len(noise_orig):
        noise_simp = _interpolate_to_match_length(noise_simp, len(noise_orig))
    
    # Use existing helper functions for L1 and L∞ norms
    l1 = l1_norm(noise_orig, noise_simp)
    linf = linf_norm(noise_orig, noise_simp)
    
    return {
        "l1": l1,
        "linf": linf
    }


def _compute_extrema_metrics(
    original_extrema: Dict[str, Any],
    simplified_extrema: Dict[str, Any]
) -> Dict[str, float]:
    """
    Compute topological distance metrics for extrema preservation using persistence diagrams.
    
    Uses bottleneck and wasserstein distances between persistence diagrams
    to measure how well extrema (local minima/maxima) are preserved.
    
    Bottleneck distance: L∞ metric (worst-case matching distance)
    Wasserstein distance: L1 metric (average-case matching distance)
    
    Args:
        original_extrema: Extrema from original series with 'persistence_diagram'
        simplified_extrema: Extrema from simplified series with 'persistence_diagram'
        
    Returns:
        Dictionary with:
        - bottleneck: L∞ distance between diagrams (worst-case)
        - wasserstein: L1 distance between diagrams (average-case)
    """
    metrics = {}
    

    orig_pd = original_extrema.get("persistence_diagram")
    simp_pd = simplified_extrema.get("persistence_diagram")
    
    if orig_pd is not None and simp_pd is not None and len(orig_pd) > 0 and len(simp_pd) > 0:
        try:
            # Optimized: Only convert if not already correct dtype
            if not isinstance(orig_pd, np.ndarray) or orig_pd.dtype != np.float32:
                orig_pd = np.array(orig_pd, dtype=np.float32)
            if not isinstance(simp_pd, np.ndarray) or simp_pd.dtype != np.float32:
                simp_pd = np.array(simp_pd, dtype=np.float32)
            
            # Bottleneck distance (L∞ metric - worst-case matching)
            distance_bottleneck = persim.bottleneck(orig_pd, simp_pd)
            metrics["bottleneck"] = float(distance_bottleneck)
            
            # Wasserstein distance (L1 metric - average-case matching)
            # Note: Default order is 1 (L1 distance)
            distance_wasserstein = persim.wasserstein(orig_pd, simp_pd)
            metrics["wasserstein"] = float(distance_wasserstein)
            
        except Exception as e:
            print(f"Warning: Error computing persistence distances: {e}")
            # Return None on error to indicate computation failed
            metrics["bottleneck"] = None
            metrics["wasserstein"] = None
    else:
        # Return None when diagrams are empty/missing
        print(f"Warning: Empty or missing persistence diagrams (orig: {len(orig_pd) if orig_pd is not None else 'None'}, simp: {len(simp_pd) if simp_pd is not None else 'None'})")
        metrics["bottleneck"] = None
        metrics["wasserstein"] = None
            
    return metrics


def compute_feature_preservation_metrics(
    original_features: Dict[str, Any],
    simplified_features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Compare features between original and simplified series.
    
    Args:
        original_features: Features from original series
        simplified_features: Features from simplified series
        
    Returns:
        Dictionary of preservation metrics for each feature
    """
    metrics = {}
    
    # IMPORTANT: Handle length mismatch ONCE at the beginning
    # If simplified series has different length, interpolate it to match original length
    # and recompute position-dependent features (slope, curvature, etc.)
    # This ensures all metrics compare features at the same x-positions.
    if "level" in original_features and "level" in simplified_features:
        orig_y = np.array(original_features["level"]["point_values"], dtype=float)
        simp_y = np.array(simplified_features["level"]["point_values"], dtype=float)
        
        if len(simp_y) != len(orig_y):
            # Interpolate simplified y-values to match original length
            simp_y_interpolated = _interpolate_to_match_length(simp_y, len(orig_y))
            
            # Recompute position-dependent features from interpolated y-values
            # Slope: derivative assumes uniform x-spacing
            if "slope" in simplified_features:
                slope_result = compute_slope(simp_y_interpolated)
                simplified_features["slope"] = slope_result
            
            # Update level feature with interpolated values
            simplified_features["level"]["point_values"] = simp_y_interpolated.tolist()
    
    # Level metrics (L1 and L∞)
    if "level" in original_features and "level" in simplified_features:
        level_metrics = _compute_level_metrics(
            original_features["level"]["point_values"],
            simplified_features["level"]["point_values"]
        )
        metrics["level"] = level_metrics
    
    # Mean preservation: absolute delta between means
    if "mean" in original_features and "mean" in simplified_features:
        orig_mean = original_features["mean"]["value"]
        simp_mean = simplified_features["mean"]["value"]
        mean_delta = delta(orig_mean, simp_mean)
        # Store as nested dict like level, so frontend grouping works
        metrics["mean"] = {
            "delta": mean_delta
        }
    
    # Regime & Change Points preservation: count-based deltas
    if "regimes" in original_features and "regimes" in simplified_features:
        orig_num_regimes = original_features["regimes"]["num_regimes"]
        simp_num_regimes = simplified_features["regimes"]["num_regimes"]
        orig_num_cps = original_features["regimes"]["num_change_points"]
        simp_num_cps = simplified_features["regimes"]["num_change_points"]
        
        metrics["regimes"] = {
            "delta": abs(orig_num_regimes - simp_num_regimes)
        }
        metrics["change_points"] = {
            "delta": abs(orig_num_cps - simp_num_cps)
        }
    
    # Slope preservation: L1 and L∞ of slope series
    # NOTE: Slope is now recomputed from interpolated y-values if lengths differ (see above)
    if "slope" in original_features and "slope" in simplified_features:
        orig_slope_values = original_features["slope"]["values"]
        simp_slope_values = simplified_features["slope"]["values"]
        
        if orig_slope_values and simp_slope_values:
            slope_metrics = _compute_slope_metrics(orig_slope_values, simp_slope_values)
            metrics["slope"] = slope_metrics
    
    # Trend preservation: L1 and L∞ of trend series
    if "trend" in original_features and "trend" in simplified_features:
        orig_trend = original_features["trend"]["trend"]
        simp_trend = simplified_features["trend"]["trend"]
        
        if orig_trend and simp_trend:
            trend_metrics = _compute_trend_metrics(orig_trend, simp_trend)
            metrics["trend"] = trend_metrics
    
    # Periodicity preservation: amplitude and period deltas
    if "periodicity" in original_features and "periodicity" in simplified_features:
        periodicity_metrics = _compute_periodicity_metrics(
            original_features["periodicity"],
            simplified_features["periodicity"]
        )
        metrics["periodicity"] = periodicity_metrics
    
    # Noise preservation: L1 and L∞ of noise series
    if "noise" in original_features and "noise" in simplified_features:
        orig_noise = original_features["noise"]["values"]
        simp_noise = simplified_features["noise"]["values"]
        
        if orig_noise and simp_noise:
            noise_metrics = _compute_noise_metrics(orig_noise, simp_noise)
            metrics["noise"] = noise_metrics
    
    # Extrema preservation: Bottleneck and Wasserstein distances using persistence diagrams
    if "extrema" in original_features and "extrema" in simplified_features:
        extrema_metrics = _compute_extrema_metrics(
            original_features["extrema"],
            simplified_features["extrema"]
        )
        metrics["extrema"] = extrema_metrics
    else:
        # If extrema not computed, return None for both metrics
        metrics["extrema"] = {"bottleneck": None, "wasserstein": None}
    
    metrics["spike_retention"] = 0.0
    metrics["curvature_correlation"] = 0.0
    metrics["regression_error"] = 0.0
    metrics["roughness_ratio"] = 0.0
    
    return metrics
