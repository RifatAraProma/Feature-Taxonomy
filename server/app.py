from flask import Flask, request, jsonify
from flask_cors import CORS
from .util import list_datasets, load_series
from .banking import median_slope_aspect
from .features.pae import get_pae as pae
from .features.compute_features import compute_all_features, compute_feature_preservation_metrics, FeatureConfig
from .features.spectral import periodogram
from .features.derivatives import slope, curvature, roughness
from .features.roughness_noise import highpass_energy
from .algorithms import transformers, reducers, aggregators
from .adapters import to_xy
from .precomputed_loader import get_precomputed_output, has_precomputed, get_algorithm_info
import numpy as np
import json
from pathlib import Path

def extract_y_values(data):
    """
    Extract y-values from data that might be tuples (from reducers) or simple values (from transformers).
    
    Args:
        data: Either a list of y-values or a list of (x, y) tuples
        
    Returns:
        List of y-values
    """
    if not data or len(data) == 0:
        return data
    
    # Check if this is a list of (x, y) tuples (from reducers)
    if isinstance(data[0], (list, tuple)) and len(data[0]) == 2:
        return [float(pair[1]) for pair in data]
    
    # Already simple y-values (from transformers)
    return data

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow CDN access

@app.route("/datasets", methods=["GET"])
def datasets():
    return jsonify(list_datasets())

@app.route("/datasets.json", methods=["GET"])
def datasets_json():
    """Serve datasets.json file for frontend"""
    import json
    datasets_file = Path(__file__).parent.parent / "datasets.json"
    if datasets_file.exists():
        with open(datasets_file, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    return jsonify([]), 404

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
        # Special case: feature-scales endpoint
        if algorithm == "feature-scales":
            print(f"\n[FEATURE_SCALES] GET request: sid={sid}")
            precomputed_dir = Path(__file__).parent.parent / 'precomputed' / sid
            scales_file = precomputed_dir / '_feature_scales.json'
            
            if scales_file.exists():
                with open(scales_file, 'r') as f:
                    scales_data = json.load(f)
                print(f"[FEATURE_SCALES] ✓ Loaded scales: {len(scales_data.get('scales', {}))} metrics")
                return jsonify(scales_data)
            else:
                print(f"[FEATURE_SCALES] ✗ Scales file not found: {scales_file}")
                return jsonify({
                    "error": "Feature scales not found",
                    "message": "Run precomputation script to generate feature scales"
                }), 404
        
        # Normal precomputed algorithm data
        print(f"\n[PRECOMPUTED] GET request: sid={sid}, algorithm={algorithm}")
        has_data = has_precomputed(sid, algorithm)
        print(f"[PRECOMPUTED] has_precomputed returned: {has_data}")
        
        if has_data:
            info = get_algorithm_info(sid, algorithm)
            print(f"[PRECOMPUTED] get_algorithm_info returned: {info}")
            print(f"[PRECOMPUTED] info['param_name'] = {info.get('param_name')}")
            
            # Load ALL level outputs at once for smooth slider interaction (0-based levels)
            all_outputs = []
            for level in range(info['num_levels']):
                level_data = get_precomputed_output(sid, algorithm, level)
                if level_data:
                    print(f"[DEBUG] Level {level} param_name: {level_data.get('param_name')}, param_value: {level_data.get('param_value')}")
                    all_outputs.append({
                        'level': level,
                        'output': level_data['output'],
                        'paramName': level_data['param_name'],  # Add param name to each level
                        'paramValue': level_data['param_value'],
                        'pae': level_data['pae'],
                        'features': level_data.get('features', {}),
                        'featurePreservation': level_data.get('feature_preservation', {})
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

@app.route("/smooth", methods=["POST"])
def smooth():
    body = request.get_json(force=True)
    sid = body["seriesId"]
    method = body["method"]
    params = body.get("params", {})
    banking_flag = bool(body.get("banking", True))
    use_precomputed = body.get("usePrecomputed", True)
    slider_level = body.get("sliderLevel", None)  # 0-based index into precomputed levels

    s = load_series(sid)
    y = s.get("y", [])
    
    # Try to use precomputed output if slider level is provided
    yhat = None
    actual_params = params.copy()
    precomputed_pae = None
    precomputed_simp_features = None
    precomputed_feature_preservation = None
    
    if use_precomputed and slider_level is not None and has_precomputed(sid, method):
        precomputed = get_precomputed_output(sid, method, slider_level)
        if precomputed and precomputed['output'] is not None:
            yhat = precomputed['output']
            precomputed_pae = precomputed.get('pae')
            precomputed_simp_features = precomputed.get('features', {})
            precomputed_feature_preservation = precomputed.get('feature_preservation', {})
            actual_params = {precomputed['param_name']: precomputed['param_value']}
            print(f"Using precomputed: {method} level {slider_level}, PAE={precomputed_pae}")
    
    # Fall back to runtime computation if precomputed not available
    if yhat is None:
        if not actual_params:
            actual_params = compute_params_from_slider(method, slider_level, y) if slider_level is not None else compute_default_params(method, y)
        yhat = run_method(method, actual_params, y)

    # Extract y-values from tuples if needed (for reducers)
    yhat_values = extract_y_values(yhat)
    
    # Compute or use precomputed values
    aspect = median_slope_aspect(yhat_values if banking_flag else y)
    pae_val = precomputed_pae if precomputed_pae is not None else pae(yhat_values)
    
    # ALWAYS compute features for original data (needed for overlay comparison)
    cfg = FeatureConfig()
    orig_features = compute_all_features(y, cfg)
    
    # Use precomputed simplified features if available, otherwise compute
    if precomputed_simp_features and precomputed_feature_preservation:
        print(f"Using precomputed features and metrics for {method} level {slider_level}")
        simp_features = precomputed_simp_features
        feature_preservation_metrics = precomputed_feature_preservation
    else:
        print(f"Computing features at runtime for {method}")
        simp_features = compute_all_features(yhat_values, cfg)
        feature_preservation_metrics = compute_feature_preservation_metrics(orig_features, simp_features)
    
    # Compute basic metrics
    orig_arr = np.asarray(y, dtype=float).flatten()
    yhat_arr = np.asarray(yhat_values, dtype=float).flatten()
    
    # Handle different length series (e.g., downsampling)
    if orig_arr.shape[0] != yhat_arr.shape[0]:
        rough_orig, rough_hat = roughness(orig_arr), roughness(yhat_arr)
        rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
        hp_orig, hp_hat = highpass_energy(orig_arr), highpass_energy(yhat_arr)
        hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
        
        basic_metrics = {
            "L1": None,
            "Linf": None,
            "rho": None,
            "roughnessRatio": rough_ratio,
            "hpEnergyLoss": hp_loss,
            "note": f"Different lengths: orig={orig_arr.shape[0]}, yhat={yhat_arr.shape[0]}"
        }
    else:
        L1 = float(np.mean(np.abs(orig_arr - yhat_arr)))
        Linf = float(np.max(np.abs(orig_arr - yhat_arr))) if len(orig_arr) else 0.0
        rho = float(np.corrcoef(orig_arr, yhat_arr)[0,1]) if len(orig_arr) > 1 else 1.0
        rough_orig, rough_hat = roughness(orig_arr), roughness(yhat_arr)
        rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
        hp_orig, hp_hat = highpass_energy(orig_arr), highpass_energy(yhat_arr)
        hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
        
        basic_metrics = {
            "L1": L1,
            "Linf": Linf,
            "rho": rho,
            "roughnessRatio": rough_ratio,
            "hpEnergyLoss": hp_loss
        }
    
    # Combine basic metrics with feature preservation
    metrics = {
        **basic_metrics,
        "featurePreservation": feature_preservation_metrics
    }
    
    precomputed_info = get_algorithm_info(sid, method) if has_precomputed(sid, method) else None
    
    return jsonify({
        "seriesId": s.get("id", sid),
        "method": method,
        "params": actual_params,
        "yhat": to_xy(yhat),
        "pae": pae_val,
        "banking": {"aspect": aspect, "heightPx": 0},
        "features": {'original': {}, 'simplified': {}},  # Deprecated - use allFeatures* instead
        "allFeaturesOrig": orig_features,
        "allFeaturesSimp": simp_features,
        "metrics": metrics,
        "precomputedInfo": precomputed_info
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
        
        # Extract y-values
        yhat_values = extract_y_values(yhat)
        
        # Compute basic metrics inline
        orig_arr = np.asarray(y, dtype=float).flatten()
        yhat_arr = np.asarray(yhat_values, dtype=float).flatten()
        
        if orig_arr.shape[0] != yhat_arr.shape[0]:
            rough_orig, rough_hat = roughness(orig_arr), roughness(yhat_arr)
            rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
            hp_orig, hp_hat = highpass_energy(orig_arr), highpass_energy(yhat_arr)
            hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
            
            metrics = {
                "L1": None,
                "Linf": None,
                "rho": None,
                "roughnessRatio": rough_ratio,
                "hpEnergyLoss": hp_loss
            }
        else:
            L1 = float(np.mean(np.abs(orig_arr - yhat_arr)))
            Linf = float(np.max(np.abs(orig_arr - yhat_arr))) if len(orig_arr) else 0.0
            rho = float(np.corrcoef(orig_arr, yhat_arr)[0,1]) if len(orig_arr) > 1 else 1.0
            rough_orig, rough_hat = roughness(orig_arr), roughness(yhat_arr)
            rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
            hp_orig, hp_hat = highpass_energy(orig_arr), highpass_energy(yhat_arr)
            hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
            
            metrics = {
                "L1": L1,
                "Linf": Linf,
                "rho": rho,
                "roughnessRatio": rough_ratio,
                "hpEnergyLoss": hp_loss
            }
        
        out.append({
            "name": name,
            "params": params,
            "yhat": to_xy(yhat),
            "pae": pae(yhat_values),
            "metrics": metrics
        })
    return jsonify({"seriesId": s.get("id", sid), "paeTarget": pae_target, "results": out})

@app.route("/spectral/<sid>", methods=["GET"])
def spectral(sid):
    s = load_series(sid)
    return jsonify(periodogram(s.get("y", [])))

@app.route("/plots/<dataset_name>/<path:filepath>")
def serve_plot(dataset_name, filepath):
    """
    Serve generated plot files (SVG or PDF).
    
    Args:
        dataset_name: Name of the dataset (e.g., 'stock_aapl_price' or 'paper  figures')
        filepath: Path to file (e.g., 'ranking/level_l1_ranking.svg' or 'Fig 5 a.pdf')
    
    Returns:
        SVG or PDF file content
    """
    from flask import send_file, abort
    import os
    
    # Get the project root directory (one level up from server/)
    project_root = Path(__file__).parent.parent
    plot_path = project_root / 'plots' / dataset_name / filepath
    
    print(f"[PLOTS] Requested: {dataset_name}/{filepath}")
    print(f"[PLOTS] Looking for: {plot_path}")
    print(f"[PLOTS] Exists: {plot_path.exists()}")
    
    if not plot_path.exists():
        print(f"[PLOTS] ERROR: File not found at {plot_path}")
        abort(404, description=f"Plot not found: {dataset_name}/{filepath}")
    
    # Determine MIME type based on file extension
    if filepath.endswith('.pdf'):
        mimetype = 'application/pdf'
    elif filepath.endswith('.svg'):
        mimetype = 'image/svg+xml'
    elif filepath.endswith('.png'):
        mimetype = 'image/png'
    else:
        mimetype = 'application/octet-stream'
    
    print(f"[PLOTS] Serving: {plot_path} as {mimetype}")
    return send_file(str(plot_path), mimetype=mimetype)

@app.route("/precomputed/<dataset_name>/plots/<filename>")
def serve_precomputed_plot(dataset_name, filename):
    """
    Serve precomputed PNG plot files.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'stock_aapl_price')
        filename: PNG filename (e.g., 'gaussian_filter_level_vs_pae.png')
    
    Returns:
        PNG file content
    """
    from flask import send_file, abort
    import os
    
    # Get the project root directory (one level up from server/)
    project_root = Path(__file__).parent.parent
    plot_path = project_root / 'precomputed' / dataset_name / 'plots' / filename
    
    print(f"[PRECOMPUTED_PLOTS] Requested: {dataset_name}/plots/{filename}")
    print(f"[PRECOMPUTED_PLOTS] Looking for: {plot_path}")
    print(f"[PRECOMPUTED_PLOTS] Exists: {plot_path.exists()}")
    
    if not plot_path.exists():
        print(f"[PRECOMPUTED_PLOTS] ERROR: File not found at {plot_path}")
        abort(404, description=f"Precomputed plot not found: {dataset_name}/plots/{filename}")
    
    print(f"[PRECOMPUTED_PLOTS] Serving: {plot_path}")
    return send_file(str(plot_path), mimetype='image/png')

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})
