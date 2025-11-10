def to_xy(y):
    """
    Convert y-values to {t, y} format for the UI.
    Handles both simple y-value arrays and (x,y) tuple arrays from reducers.
    """
    if not y:
        return []
    
    # Check if this is a list of (x, y) tuples (from reducers)
    if isinstance(y[0], (list, tuple)) and len(y[0]) == 2:
        # Use the original x index from the tuple
        return [{"t": int(pair[0]) + 1, "y": float(pair[1])} for pair in y]
    
    # Simple y-values array (from transformers)
    return [{"t": i + 1, "y": float(val)} for i, val in enumerate(y)]
