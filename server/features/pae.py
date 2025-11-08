from pae import PAEMeasure
import pandas as pd
import numpy as np
from pae import Scaler

def get_pae(data, width=1000, height=375, r=None):
    if not isinstance(data, (list, tuple)) or len(data) == 0:
        # print("PAE Input Data:", data)
        raise ValueError("Invalid input: Expected non-empty list or tuple.")

    if len(data) == 0:
        return 0

    # Scale the data
    scale = Scaler(int(width), int(height))
    data_scaled = scale.scale(data)
    # # print("Rescaled Data:", data_scaled)  # Debugging: # print rescaled data

    # Set r based on input or default behavior
    if r is None:
        r = 0.2 * np.std(data_scaled)   # Adjusted default behavior # cite from paper titled Approximate entropy as a measure of system complexity. 
                                        #btn 0.1 to 0.2 sd is good choice. we chose 0.2 for a higher tolerance
    else:
        r = float(r)  # Ensure r is a float

    # Calculate PAE
    pae_meas = PAEMeasure(w=int(width), h=int(height), r=r)
    pae_value = pae_meas.pae(data)

    return round(pae_value, 3)