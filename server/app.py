from flask import Flask, request, jsonify
from .util import list_datasets, load_series
from .banking import median_slope_aspect
from .features.pae import get_pae as pae
from .features.compute_features import compute_all_features, FeatureConfig
from .features.spectral import periodogram
from .features.derivatives import slope, curvature, roughness
from .features.roughness_noise import highpass_energy
from .algorithms import transformers, reducers, aggregators
from .adapters import to_xy
from .precomputed_loader import get_precomputed_output, has_precomputed, get_algorithm_info
import numpy as np
from pathlib import Path

app = Flask(__name__)

@app.route("/datasets", methods=["GET"])
def datasets():
    return jsonify(list_datasets())

@app.route("/series/<sid>", methods=["GET"])
def series(sid):
    s = load_series(sid)
    y = s.get("y", [])
    x = list(range(1, len(y)+1))
    return jsonify({"id": s.get("id", sid), "x": x, "y": y})

@app.route('/precomputed/<dataset_id>/<algorithm>.json')
def serve_precomputed_file(dataset_id, algorithm):
    """
    Serve precomputed JSON files directly (LineSmooth strategy).
    Simple deterministic path: precomputed/{dataset_id}/{algorithm}.json
    """
    from flask import send_file
    precomputed_dir = Path(__file__).parent.parent / 'precomputed'
    file_path = precomputed_dir / dataset_id / f"{algorithm}.json"
    
    print(f"[PRECOMPUTED] Looking for: {file_path}")
    print(f"[PRECOMPUTED] Exists: {file_path.exists()}")
    
    if file_path.exists():
        print(f"[PRECOMPUTED] ✓ Serving file")
        return send_file(file_path)
    
    print(f"[PRECOMPUTED] ✗ File not found")
    return jsonify({
        "error": "Precomputed file not found", 
        "path": str(file_path)
    }), 404

@app.route("/precomputed/<sid>/<algorithm>", methods=["GET"])
def precomputed_info(sid, algorithm):
    """Get precomputed algorithm metadata and ALL level data for a dataset."""
    try:
        print(f"\n[PRECOMPUTED] GET request: sid={sid}, algorithm={algorithm}")
        has_data = has_precomputed(sid, algorithm)
        print(f"[PRECOMPUTED] has_precomputed returned: {has_data}")
        
        if has_data:
            info = get_algorithm_info(sid, algorithm)
            print(f"[PRECOMPUTED] get_algorithm_info returned: {info}")
            
            # Load ALL level outputs at once for smooth slider interaction (0-based levels)
            all_outputs = []
            for level in range(info['num_levels']):
                level_data = get_precomputed_output(sid, algorithm, level)
                if level_data:
                    all_outputs.append({
                        'level': level,
                        'output': level_data['output'],
                        'paramName': level_data['param_name'],  # Add param name to each level
                        'paramValue': level_data['param_value'],
                        'pae': level_data['pae']
                    })
            
            print(f"[PRECOMPUTED] Loaded {len(all_outputs)} levels")
            return jsonify({
                "available": True,
                "paramName": info['param_name'],
                "paramValues": info['param_values'],
                "paeValues": info['pae_values'],
                "numLevels": info['num_levels'],
                "allOutputs": all_outputs  # Include all level outputs for instant slider response
            })
        else:
            print(f"[PRECOMPUTED] No precomputed data found")
            return jsonify({"available": False})
    except Exception as e:
        print(f"Error in precomputed_info for {sid}/{algorithm}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"available": False, "error": str(e)})

def compute_default_params(method, y):
    """Compute sensible default parameters for a method when none are provided."""
    data_length = len(y)
    
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev', 'elliptical']):
        if method == 'gaussian_filter':
            return {'sigma': max(1.0, data_length / 100)}
        elif method == 'savitzky_golay_filter':
            return {'window_size': 5, 'polyorder': 2}
        else:
            return {'window_size': 5}
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        return {'cutoff_freq_normalized': 0.25}
    elif method == 'elliptical_filter':
        return {
            'cutoff_freq_normalized': 0.25,
            'order': 2,
            'ripple_db': 0.001,
            'max_atten_db': 40
        }
    elif 'downsample' in method:
        return {'output_length': max(50, data_length // 2)}
    elif method == 'asap_aggregator':
        return {'max_window': 10}
    elif method == 'bin_average_aggregator':
        return {'bins': max(10, data_length // 10)}
    else:
        return {'w': 5}

def compute_params_from_slider(method, slider_level, y):
    """
    Map slider level (0-32) to algorithm-specific parameters.
    This matches the precomputation ranges in precompute_all.py.
    """
    data_length = len(y)
    # Normalize slider to 0-1 range
    normalized = slider_level / 32.0
    
    if 'filter' in method and not any(x in method for x in ['fft', 'butterworth', 'chebyshev', 'elliptical']):
        if method == 'gaussian_filter':
            # Match precompute_all.py: min=0.001, max=dataLength/10, exponential scale
            min_sigma = 0.001
            max_sigma = max(10, data_length / 10)
            # Exponential interpolation
            sigma = min_sigma * ((max_sigma / min_sigma) ** normalized)
            return {'sigma': sigma}
        else:
            # Other filters: window_size 1 to 51
            window_size = int(1 + normalized * 50)
            if window_size % 2 == 0:
                window_size += 1  # Make odd
            return {'window_size': window_size}
    elif any(x in method for x in ['butterworth', 'fft', 'chebyshev']):
        # Match precompute_all.py: min=0.99, max=0.01, exponential scale
        cutoff = 0.99 * ((0.01 / 0.99) ** normalized)
        return {'cutoff_freq_normalized': cutoff}
    elif method == 'elliptical_filter':
        # Elliptical filter needs cutoff + order, ripple_db, max_atten_db
        cutoff = 0.99 * ((0.01 / 0.99) ** normalized)
        return {
            'cutoff_freq_normalized': cutoff,
            'order': 2,
            'ripple_db': 0.001,
            'max_atten_db': 40
        }
    elif 'downsample' in method:
        # Match precompute_all.py: linear scale, min_ratio=1.0, max_ratio=0.05
        min_length = max(10, int(data_length * 0.05))
        output_length = int(data_length - normalized * (data_length - min_length))
        return {'output_length': max(10, output_length)}
    elif method == 'asap_aggregator':
        # max_window 1 to 100
        max_window = int(1 + normalized * 99)
        return {'max_window': max_window}
    elif method == 'bin_average_aggregator':
        # bins: dataLength down to 10
        min_bins = 10
        bins = int(data_length - normalized * (data_length - min_bins))
        return {'bins': max(10, bins)}
    else:
        # Fallback
        return {'w': int(1 + normalized * 50)}

def run_method(method, params, y):
    # try transformer first, then reducer, then aggregator
    try:
        return transformers.apply(method, y, **params)
    except Exception as e:
        print(f"Transformer failed for {method}: {e}")
        pass
    try:
        return reducers.apply(method, y, **params)
    except Exception as e:
        print(f"Reducer failed for {method}: {e}")
        pass
    try:
        return aggregators.apply(method, y, **params)
    except Exception as e:
        raise e

def compute_feature_preservation_metrics(orig_features, simp_features):
    """
    Compare features between original and simplified series.
    Returns metrics showing how well features are preserved.
    Organized by feature type with consistent naming.
    """
    metrics = {}
    
    # 1. LEVEL - Point and interval level values
    orig_level = orig_features.get("level", {})
    simp_level = simp_features.get("level", {})
    if orig_level:
        # Compare interval levels if available
        orig_intervals = orig_level.get("interval", [])
        simp_intervals = simp_level.get("interval", [])
        if orig_intervals and simp_intervals:
            orig_values = [iv.get("value", 0) for iv in orig_intervals]
            simp_values = [iv.get("value", 0) for iv in simp_intervals]
            min_len = min(len(orig_values), len(simp_values))
            if min_len > 1:
                corr = np.corrcoef(orig_values[:min_len], simp_values[:min_len])[0, 1]
                metrics["level_interval_correlation"] = float(corr)
                mae = np.mean(np.abs(np.array(orig_values[:min_len]) - np.array(simp_values[:min_len])))
                metrics["level_interval_mae"] = float(mae)
        # Compare point levels if available
        orig_points = orig_level.get("point", [])
        simp_points = simp_level.get("point", [])
        if orig_points and simp_points:
            orig_values = [pv.get("value", 0) for pv in orig_points]
            simp_values = [pv.get("value", 0) for pv in simp_points]
            min_len = min(len(orig_values), len(simp_values))
            if min_len > 0:
                mae = np.mean(np.abs(np.array(orig_values[:min_len]) - np.array(simp_values[:min_len])))
                metrics["level_point_mae"] = float(mae)
    
    # 2. MEAN - Average value
    orig_mean = orig_features.get("mean", {}).get("mu", 0)
    simp_mean = simp_features.get("mean", {}).get("mu", 0)
    metrics["mean_absolute_error"] = abs(orig_mean - simp_mean)
    if abs(orig_mean) > 1e-10:
        metrics["mean_relative_error"] = abs(orig_mean - simp_mean) / abs(orig_mean)
    
    # 3. REGIMES - Mean-based segments
    orig_regimes = orig_features.get("regimes", [])
    simp_regimes = simp_features.get("regimes", [])
    if orig_regimes:
        metrics["regimes_count_orig"] = len(orig_regimes)
        metrics["regimes_count_simp"] = len(simp_regimes)
        metrics["regimes_retention"] = len(simp_regimes) / len(orig_regimes)
        # Baseline correlation if both have regimes
        if simp_regimes:
            orig_baselines = [r.get("baseline", 0) for r in orig_regimes]
            simp_baselines = [r.get("baseline", 0) for r in simp_regimes]
            min_len = min(len(orig_baselines), len(simp_baselines))
            if min_len > 1:
                corr = np.corrcoef(orig_baselines[:min_len], simp_baselines[:min_len])[0, 1]
                metrics["regimes_baseline_correlation"] = float(corr)
    
    # 4. CHANGE POINTS - Regime boundaries
    orig_cpts = orig_features.get("changePoints", [])
    simp_cpts = simp_features.get("changePoints", [])
    if orig_cpts:
        metrics["changepoints_count_orig"] = len(orig_cpts)
        metrics["changepoints_count_simp"] = len(simp_cpts)
        metrics["changepoints_retention"] = len(simp_cpts) / len(orig_cpts)
        # Positional error if both have change points
        if simp_cpts and len(orig_cpts) > 0:
            orig_t = [cp.get("t", 0) for cp in orig_cpts]
            simp_t = [cp.get("t", 0) for cp in simp_cpts]
            min_len = min(len(orig_t), len(simp_t))
            if min_len > 0:
                avg_error = sum(abs(orig_t[i] - simp_t[i]) for i in range(min_len)) / min_len
                metrics["changepoints_position_error"] = avg_error
    
    # 5. EXTREMA - Local maxima and minima
    orig_extrema = orig_features.get("extrema", [])
    simp_extrema = simp_features.get("extrema", [])
    if orig_extrema:
        metrics["extrema_count_orig"] = len(orig_extrema)
        metrics["extrema_count_simp"] = len(simp_extrema)
        metrics["extrema_retention"] = len(simp_extrema) / len(orig_extrema)
        # Value correlation if both have extrema
        if simp_extrema and len(simp_extrema) > 1:
            orig_y = [e.get("y", 0) for e in orig_extrema]
            simp_y = [e.get("y", 0) for e in simp_extrema]
            min_len = min(len(orig_y), len(simp_y))
            if min_len > 1:
                corr = np.corrcoef(orig_y[:min_len], simp_y[:min_len])[0, 1]
                metrics["extrema_value_correlation"] = float(corr)
    
    # 6. SPIKES/DIPS - Outliers
    orig_spikes = orig_features.get("spikesDips", [])
    simp_spikes = simp_features.get("spikesDips", [])
    if orig_spikes:
        metrics["spikes_count_orig"] = len(orig_spikes)
        metrics["spikes_count_simp"] = len(simp_spikes)
        metrics["spikes_retention"] = len(simp_spikes) / len(orig_spikes)
    
    # 7. SLOPE - First derivative (rate of change)
    orig_slope = np.array(orig_features.get("slope", {}).get("values", []))
    simp_slope = np.array(simp_features.get("slope", {}).get("values", []))
    if len(orig_slope) > 1 and len(simp_slope) > 1:
        # Interpolate to match lengths
        if len(simp_slope) != len(orig_slope):
            x_simp = np.linspace(0, 1, len(simp_slope))
            x_orig = np.linspace(0, 1, len(orig_slope))
            simp_slope = np.interp(x_orig, x_simp, simp_slope)
        corr = np.corrcoef(orig_slope, simp_slope)[0, 1] if len(orig_slope) == len(simp_slope) else 0.0
        metrics["slope_correlation"] = float(corr)
        # MAE for slope
        mae = np.mean(np.abs(orig_slope - simp_slope))
        metrics["slope_mae"] = float(mae)
    
    # 8. CURVATURE - Second derivative (shape bending)
    orig_curv = np.array(orig_features.get("curvature", {}).get("values", []))
    simp_curv = np.array(simp_features.get("curvature", {}).get("values", []))
    if len(orig_curv) > 1 and len(simp_curv) > 1:
        # Interpolate to match lengths
        if len(simp_curv) != len(orig_curv):
            x_simp = np.linspace(0, 1, len(simp_curv))
            x_orig = np.linspace(0, 1, len(orig_curv))
            simp_curv = np.interp(x_orig, x_simp, simp_curv)
        corr = np.corrcoef(orig_curv, simp_curv)[0, 1] if len(orig_curv) == len(simp_curv) else 0.0
        metrics["curvature_correlation"] = float(corr)
        # MAE for curvature
        mae = np.mean(np.abs(orig_curv - simp_curv))
        metrics["curvature_mae"] = float(mae)
    
    # 9. TREND - Low-frequency component
    orig_trend = np.array(orig_features.get("trend", {}).get("values", []))
    simp_trend = np.array(simp_features.get("trend", {}).get("values", []))
    if len(orig_trend) > 1 and len(simp_trend) > 1:
        # Interpolate to match lengths
        if len(simp_trend) != len(orig_trend):
            x_simp = np.linspace(0, 1, len(simp_trend))
            x_orig = np.linspace(0, 1, len(orig_trend))
            simp_trend = np.interp(x_orig, x_simp, simp_trend)
        corr = np.corrcoef(orig_trend, simp_trend)[0, 1] if len(orig_trend) == len(simp_trend) else 0.0
        metrics["trend_correlation"] = float(corr)
        # MAE for trend
        mae = np.mean(np.abs(orig_trend - simp_trend))
        metrics["trend_mae"] = float(mae)
    
    # 10. NOISE - High-frequency residual
    orig_noise = np.array(orig_features.get("noise", {}).get("values", []))
    simp_noise = np.array(simp_features.get("noise", {}).get("values", []))
    if len(orig_noise) > 1 and len(simp_noise) > 1:
        # Interpolate to match lengths
        if len(simp_noise) != len(orig_noise):
            x_simp = np.linspace(0, 1, len(simp_noise))
            x_orig = np.linspace(0, 1, len(orig_noise))
            simp_noise = np.interp(x_orig, x_simp, simp_noise)
        # Energy ratio (how much noise energy is preserved)
        orig_energy = np.sum(orig_noise ** 2)
        simp_energy = np.sum(simp_noise ** 2)
        if orig_energy > 1e-10:
            metrics["noise_energy_ratio"] = float(simp_energy / orig_energy)
    
    # 11. REGRESSION - Linear fit (alpha + beta*t)
    orig_reg = orig_features.get("regression", {})
    simp_reg = simp_features.get("regression", {})
    orig_alpha = orig_reg.get("alpha", 0)
    orig_beta = orig_reg.get("beta", 0)
    simp_alpha = simp_reg.get("alpha", 0)
    simp_beta = simp_reg.get("beta", 0)
    metrics["regression_slope_error"] = abs(orig_beta - simp_beta)
    metrics["regression_intercept_error"] = abs(orig_alpha - simp_alpha)
    if abs(orig_beta) > 1e-10:
        metrics["regression_slope_relative_error"] = abs(orig_beta - simp_beta) / abs(orig_beta)
    
    # 12. PERIODICITY - Frequency analysis
    orig_period = orig_features.get("periodicity", {})
    simp_period = simp_features.get("periodicity", {})
    orig_fstar = orig_period.get("fStar", 0)
    simp_fstar = simp_period.get("fStar", 0)
    if orig_fstar > 0:
        metrics["periodicity_frequency_error"] = abs(orig_fstar - simp_fstar)
        metrics["periodicity_frequency_relative_error"] = abs(orig_fstar - simp_fstar) / orig_fstar
    orig_period_val = orig_period.get("period", 0)
    simp_period_val = simp_period.get("period", 0)
    if orig_period_val > 0:
        metrics["periodicity_period_error"] = abs(orig_period_val - simp_period_val)
    
    # 13. ROUGHNESS - Variability measure
    orig_rough = orig_features.get("roughness", {}).get("value", 0)
    simp_rough = simp_features.get("roughness", {}).get("value", 0)
    if orig_rough > 0:
        metrics["roughness_ratio"] = simp_rough / orig_rough
        metrics["roughness_absolute_change"] = abs(orig_rough - simp_rough)
    
    return metrics

def compute_metrics(orig, yhat, orig_features=None, simp_features=None):
    # lightweight set to demo the UI; expand as needed
    # Convert to arrays first
    orig = np.asarray(orig, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    
    # Ensure they are 1D arrays
    orig = orig.flatten()
    yhat = yhat.flatten()
    
    # Handle different length series (e.g., downsampling)
    if orig.shape[0] != yhat.shape[0]:
        # For downsampled series, we can only compute roughness-based metrics
        rough_orig, rough_hat = roughness(orig), roughness(yhat)
        rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
        hp_orig, hp_hat = highpass_energy(orig), highpass_energy(yhat)
        hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
        
        result = {
            "L1": None,  # Cannot compute point-wise metrics
            "Linf": None,
            "rho": None,
            "roughnessRatio": rough_ratio,
            "hpEnergyLoss": hp_loss,
            "note": f"Different lengths: orig={orig.shape[0]}, yhat={yhat.shape[0]}"
        }
    else:
        # Point-wise metrics (same length)
        L1 = float(np.mean(np.abs(orig - yhat)))
        Linf = float(np.max(np.abs(orig - yhat))) if len(orig) else 0.0
        rho = float(np.corrcoef(orig, yhat)[0,1]) if len(orig) > 1 else 1.0
        rough_orig, rough_hat = roughness(orig), roughness(yhat)
        rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
        hp_orig, hp_hat = highpass_energy(orig), highpass_energy(yhat)
        hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
        
        result = {
            "L1": L1, 
            "Linf": Linf, 
            "rho": rho,
            "roughnessRatio": rough_ratio, 
            "hpEnergyLoss": hp_loss
        }
    
    # Feature preservation metrics
    if orig_features and simp_features:
        feature_preservation = compute_feature_preservation_metrics(orig_features, simp_features)
        result["featurePreservation"] = feature_preservation
    
    return result

@app.route("/smooth", methods=["POST"])
def smooth():
    body = request.get_json(force=True)
    sid = body["seriesId"]
    method = body["method"]
    params = body.get("params", {})
    return_features = body.get("returnFeatures", [])
    banking_flag = bool(body.get("banking", True))
    use_precomputed = body.get("usePrecomputed", True)  # Default to using precomputed
    slider_level = body.get("sliderLevel", None)  # 0-99 value from slider (index into precomputed levels)

    s = load_series(sid)
    y = s.get("y", [])
    
    # Special case: fetch ALL precomputed levels (LineSmooth strategy)
    if use_precomputed and slider_level is None and has_precomputed(sid, method):
        algo_info = get_algorithm_info(sid, method)
        if algo_info and algo_info['num_levels'] > 0:
            all_levels = {}
            for level_idx in range(algo_info['num_levels']):
                precomputed = get_precomputed_output(sid, method, level_idx)
                if precomputed and precomputed['output'] is not None:
                    yhat = precomputed['output']
                    
                    # Just return the output, skip heavy computation for now
                    all_levels[level_idx] = {
                        "yhat": to_xy(yhat),
                        "pae": None,  # Skip PAE computation for bulk load
                        "banking": {"aspect": 1.0, "heightPx": 0},  # Skip banking for bulk load
                        "features": {'original': {}, 'simplified': {}},  # Skip features for bulk load
                        "metrics": {},  # Skip metrics for bulk load
                        "params": {precomputed['param_name']: precomputed['param_value']}
                    }
            
            return jsonify({
                "seriesId": s.get("id", sid),
                "method": method,
                "allLevels": all_levels,
                "precomputedInfo": algo_info
            })
    
    # Try to use precomputed output first if slider level is provided
    yhat = None
    actual_params = params.copy()
    precomputed_pae = None  # Store PAE from precomputed file
    
    if use_precomputed and slider_level is not None:
        # Check if we have precomputed output for this dataset and algorithm
        if has_precomputed(sid, method):
            precomputed = get_precomputed_output(sid, method, slider_level)
            if precomputed and precomputed['output'] is not None:
                yhat = precomputed['output']
                precomputed_pae = precomputed.get('pae')  # Get PAE from precomputed file
                # Update params to reflect the actual parameter value used
                actual_params = {precomputed['param_name']: precomputed['param_value']}
                print(f"Using precomputed output: {method} level {slider_level}, {precomputed['param_name']}={precomputed['param_value']}, PAE={precomputed_pae}")
            else:
                print(f"Precomputed output not found for {sid} × {method} level {slider_level}, falling back to runtime computation")
        else:
            print(f"No precomputed data for {sid} × {method}, falling back to runtime computation")
    
    # Fall back to runtime computation if precomputed not available
    if yhat is None:
        # If no params provided, compute from slider_level or use defaults
        if not actual_params:
            if slider_level is not None:
                actual_params = compute_params_from_slider(method, slider_level, y)
            else:
                actual_params = compute_default_params(method, y)
        yhat = run_method(method, actual_params, y)

    aspect = median_slope_aspect(yhat if banking_flag else y)
    # Use precomputed PAE if available, otherwise compute it
    pae_val = precomputed_pae if precomputed_pae is not None else pae(yhat)
    
    # Skip heavy computation for precomputed data (focus on speed)
    if use_precomputed and has_precomputed(sid, method):
        # Return minimal response for precomputed data
        precomputed_info = get_algorithm_info(sid, method)
        return jsonify({
            "seriesId": s.get("id", sid),
            "method": method,
            "params": actual_params,
            "yhat": to_xy(yhat),
            "pae": None,  # Skip PAE
            "banking": {"aspect": 1.0, "heightPx": 0},  # Skip banking
            "features": {'original': {}, 'simplified': {}},  # Skip features
            "allFeaturesOrig": {},
            "allFeaturesSimp": {},
            "metrics": {},  # Skip metrics
            "precomputedInfo": precomputed_info
        })
    
    # ALWAYS compute all features for both original and simplified (needed for metrics)
    cfg = FeatureConfig()
    orig_features = compute_all_features(y, cfg)
    simp_features = compute_all_features(yhat, cfg)
    
    # Extract requested features for overlay visualization
    # Return features for BOTH original and simplified series
    feats = {
        'original': {},
        'simplified': {}
    }
    if return_features:
        # Map frontend feature names to backend feature keys
        feature_map = {
            'level': 'level',
            'mean': 'mean',
            'extrema': 'extrema',
            'regimes': 'regimes',
            'changePoints': 'changePoints',
            'spikes': 'spikesDips',
            'spikesDips': 'spikesDips',
            'trend': 'trend',
            'noise': 'noise',
            'slope': 'slope',
            'curvature': 'curvature',
            'regression': 'regression',
            'periodicity': 'periodicity',
            'roughness': 'roughness'
        }
        
        for req_feature in return_features:
            mapping = feature_map.get(req_feature)
            if mapping:
                # Single feature mapping
                if mapping in orig_features:
                    feats['original'][mapping] = orig_features[mapping]
                if mapping in simp_features:
                    feats['simplified'][mapping] = simp_features[mapping]
    
    # Compute metrics including feature preservation
    metrics = compute_metrics(y, yhat, orig_features, simp_features)
    
    # Get precomputed metadata if available
    precomputed_info = None
    if has_precomputed(sid, method):
        precomputed_info = get_algorithm_info(sid, method)

    return jsonify({
        "seriesId": s.get("id", sid),
        "method": method,
        "params": actual_params,
        "yhat": to_xy(yhat),
        "pae": pae_val,
        "banking": {"aspect": aspect, "heightPx": 0},
        "features": feats,  # For visualization overlays
        "allFeaturesOrig": orig_features,  # Complete features of original
        "allFeaturesSimp": simp_features,  # Complete features of simplified
        "metrics": metrics,
        "precomputedInfo": precomputed_info  # Metadata about precomputed levels
    })

@app.route("/match_pae", methods=["POST"])
def match_pae():
    # naive: we just return the one run at provided params; you can expand to sweep+nearest
    body = request.get_json(force=True)
    sid = body["seriesId"]
    pae_target = float(body["paeTarget"])
    methods = body["methods"]
    s = load_series(sid)
    y = s.get("y", [])
    out = []
    for m in methods:
        name = m["name"]
        params = m.get("params", {})
        yhat = run_method(name, params, y)
        out.append({
            "name": name,
            "params": params,
            "yhat": to_xy(yhat),
            "pae": pae(yhat),
            "metrics": compute_metrics(y, yhat)
        })
    return jsonify({"seriesId": s.get("id", sid), "paeTarget": pae_target, "results": out})

@app.route("/spectral/<sid>", methods=["GET"])
def spectral(sid):
    s = load_series(sid)
    return jsonify(periodogram(s.get("y", [])))

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})
