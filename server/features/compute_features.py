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
import ruptures as rpt


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
    regime_penalty: Optional[float] = None  # None = auto (BIC), or specify manual penalty
    
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
        - minima: List of {index, value} for local minima
        - maxima: List of {index, value} for local maxima
    """
    # TODO: Implement based on extrema.svg
    return {
        "minima": [],
        "maxima": []
    }


# ============================================================================
# FEATURE 4: REGIME & CHANGE POINTS
# ============================================================================

def compute_regimes(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Detect regimes exactly as defined in the paper:
    - Regimes = intervals with constant mean baseline
    - Change-points = boundaries where the mean shifts
    Uses PELT optimal segmentation with L2 loss.
    
    Penalty selection:
    - If cfg.regime_penalty is None: Uses BIC (Bayesian Information Criterion)
      Formula: pen = log(n) * d^2, where n=length, d=dimension (1 for univariate)
    - Otherwise: Uses the specified manual penalty
    
    Reference: web/src/figures/Visual features/regime_change_points.svg
    
    Args:
        y: Time series data
        cfg: Configuration with regime_penalty parameter
        
    Returns:
        Dictionary containing:
        - regimes: List of {start, end, baseline_mean} for each regime
        - change_points: List of indices where regime changes occur
        - num_regimes: Total number of regimes detected
        - num_change_points: Total number of change points detected
        - penalty_used: The penalty value that was used (for debugging)
    """
    y = np.asarray(y)
    
    try:
        # BIC penalty: log(n) * d^2 * sigma^2
        # For L2 cost, standard formulation is: log(n) * d^2
        # We use a slightly more conservative version: log(n) * (1 + log(n))
        # This helps avoid over-segmentation in short series
        n = len(y)
        penalty = np.log(n) * np.var(y)  # Scaled by variance for better adaptivity

        # Fit PELT model (mean-shift model with L2 loss)
        algo = rpt.Pelt(model="l2").fit(y)
        cps = algo.predict(pen=penalty)  # change-points (end indices of segments)
        
        # Convert to regime intervals
        regimes = []
        start = 0
        for cp in cps:
            end = cp - 1
            baseline_mean = float(np.mean(y[start:cp]))
            regimes.append({
                "start": int(start),
                "end": int(end),
                "baseline_mean": baseline_mean
            })
            start = cp
        
        # Remove last change point (it's the length of the series)
        change_points = [int(cp) for cp in cps[:-1]]
        
        return {
            "regimes": regimes,
            "change_points": change_points,
            "num_regimes": len(regimes),
            "num_change_points": len(change_points),
            "penalty_used": float(penalty)
        }
    except Exception as e:
        # Fallback if ruptures fails
        print(f"Warning: PELT failed with error: {e}. Returning empty regimes.")
        return {
            "regimes": [],
            "change_points": [],
            "num_regimes": 0,
            "num_change_points": 0,
            "penalty_used": None
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
    Compute first derivative (rate of change).
    
    Reference: web/src/figures/Visual features/slope.svg
    
    Returns:
        Dictionary containing:
        - values: Array of slope values
        - mean_slope: Average slope
    """
    # TODO: Implement based on slope.svg
    return {
        "values": [],
        "mean_slope": 0.0
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
# FEATURE 8: TREND
# ============================================================================

def compute_trend(y: np.ndarray, cfg: FeatureConfig) -> Dict[str, Any]:
    """
    Extract low-frequency trend component via spectral filtering.
    
    Reference: web/src/figures/Visual features/trend.svg
    
    Returns:
        Dictionary containing:
        - values: Array of trend values
        - correlation: Correlation with original signal
    """
    # TODO: Implement based on trend.svg (low-pass filter)
    return {
        "values": [],
        "correlation": 0.0
    }


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
    
    Reference: web/src/figures/Visual features/periodicity.svg
    
    Returns:
        Dictionary containing:
        - dominant_frequency: Primary frequency
        - period: Corresponding period (1/frequency)
        - amplitude: Peak amplitude in frequency domain
    """
    # TODO: Implement based on periodicity.svg
    return {
        "dominant_frequency": 0.0,
        "period": 0.0,
        "amplitude": 0.0
    }


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
    Extract high-frequency noise component via spectral filtering.
    
    Reference: web/src/figures/Visual features/noise.svg
    
    Returns:
        Dictionary containing:
        - values: Array of noise values
        - std: Standard deviation of noise
    """
    # TODO: Implement based on noise.svg (high-pass filter)
    return {
        "values": [],
        "std": 0.0
    }


# ============================================================================
# Main Feature Computation
# ============================================================================

def compute_all_features(
    y: np.ndarray | List[float],
    cfg: Optional[FeatureConfig] = None
) -> Dict[str, Any]:
    """
    Compute all 12 visual features for a time series.
    
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
    
    # Compute all features
    features = {
        "level": compute_level(y, cfg),
        "mean": compute_mean(y),
        "extrema": compute_extrema(y),
        "regimes": compute_regimes(y, cfg),
        "spikes_dips": compute_spikes_dips(y, cfg),
        "slope": compute_slope(y),
        "curvature": compute_curvature(y),
        "trend": compute_trend(y, cfg),
        "regression": compute_regression(y),
        "periodicity": compute_periodicity(y),
        "roughness": compute_roughness(y),
        "noise": compute_noise(y, cfg)
    }
    
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
    
    metrics["extrema_retention"] = 0.0
    metrics["spike_retention"] = 0.0
    metrics["slope_correlation"] = 0.0
    metrics["curvature_correlation"] = 0.0
    metrics["trend_correlation"] = 0.0
    metrics["regression_error"] = 0.0
    metrics["periodicity_preservation"] = 0.0
    metrics["roughness_ratio"] = 0.0
    metrics["noise_ratio"] = 0.0
    
    return metrics
