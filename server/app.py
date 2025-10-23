from flask import Flask, request, jsonify
from .util import list_datasets, load_series
from .banking import median_slope_aspect
from .features.pae import pixel_approx_entropy as pae
from .features.extrema import find_extrema
from .features.regimes import simple_regimes
from .features.spectral import periodogram
from .features.derivatives import slope, curvature, roughness
from .features.roughness_noise import highpass_energy
from .algorithms import transformers, reducers, aggregators
from .adapters import to_xy
import numpy as np

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

def run_method(method, params, y):
    # try transformer first, then reducer, then aggregator
    try:
        return transformers.apply(method, y, **params)
    except Exception:
        pass
    try:
        return reducers.apply(method, y, **params)
    except Exception:
        pass
    try:
        return aggregators.apply(method, y, **params)
    except Exception as e:
        # final fallback to moving average if requested
        if method == "moving_average":
            return transformers.apply(method, y, **params)
        raise e

def compute_features(y, return_features):
    feats = {}
    if not return_features:
        return feats
    if "extrema" in return_features:
        feats["extrema"] = find_extrema(y)
    if "regimes" in return_features or "change-points" in return_features:
        regs, cpts = simple_regimes(y)
        feats["regimes"] = regs
        feats["changePoints"] = cpts
    if "periodicity" in return_features:
        feats["periodicity"] = periodogram(y)
    return feats

def compute_metrics(orig, yhat):
    # lightweight set to demo the UI; expand as needed
    orig = np.asarray(orig, dtype=float)
    yhat = np.asarray(yhat, dtype=float)
    L1 = float(np.mean(np.abs(orig - yhat)))
    Linf = float(np.max(np.abs(orig - yhat))) if len(orig) else 0.0
    rho = float(np.corrcoef(orig, yhat)[0,1]) if len(orig) > 1 else 1.0
    rough_orig, rough_hat = roughness(orig), roughness(yhat)
    rough_ratio = float(rough_hat / rough_orig) if rough_orig != 0 else 1.0
    hp_orig, hp_hat = highpass_energy(orig), highpass_energy(yhat)
    hp_loss = float((hp_orig - hp_hat) / hp_orig) if hp_orig != 0 else 0.0
    return {"L1": L1, "Linf": Linf, "rho": rho,
            "roughnessRatio": rough_ratio, "hpEnergyLoss": hp_loss}

@app.route("/smooth", methods=["POST"])
def smooth():
    body = request.get_json(force=True)
    sid = body["seriesId"]
    method = body["method"]
    params = body.get("params", {})
    return_features = body.get("returnFeatures", [])
    banking_flag = bool(body.get("banking", True))

    s = load_series(sid)
    y = s.get("y", [])
    yhat = run_method(method, params, y)

    aspect = median_slope_aspect(yhat if banking_flag else y)
    pae_val = pae(yhat)
    feats = compute_features(yhat, return_features)
    metrics = compute_metrics(y, yhat)

    return jsonify({
        "seriesId": s.get("id", sid),
        "method": method,
        "params": params,
        "yhat": to_xy(yhat),
        "pae": pae_val,
        "banking": {"aspect": aspect, "heightPx": 0},
        "features": feats,
        "metrics": metrics
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
