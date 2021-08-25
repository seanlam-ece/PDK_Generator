#Sets Adiabatic Coupler EME Simulation Parameters 

#General Purpose Libraries
try:
    import matplotlib.pyplot as plt
except:
    import pip
    pip.main(['install', 'matplotlib'])
    import matplotlib.pyplot as plt

import numpy as np
import ac_geometry
acg = ac_geometry.ac_geo
L_IO = ac_geometry.L_io_wg
thick_Si = ac_geometry.thick_Si

#Setup and run EME sweep
def run_length_eme_sweep(mode, start_len, end_len):
    print("Running EME simulation...\n")
    num_points = 100
    mode.run()
    
    print("Running EME length sweep from {} to {}...".format(start_len, end_len))
    mode.setemeanalysis("propagation sweep",1);
    mode.setemeanalysis("parameter","group span 2");
    mode.setemeanalysis("start",start_len);
    mode.setemeanalysis("stop",end_len);
    mode.setemeanalysis("number of points", num_points);
    mode.emesweep()

#Optimizing and plotting results of EME Sweep 
def get_ac_eme_results(mode, start, end):
    
    length = np.linspace(start,end,100)
    S = mode.getemesweep("S")
    trans = abs(S['s42'])**2
    
    neff_plot = plt.plot(length, trans, label = "SWG-AC TE01")
    neff_plot = plt.title('Transmission vs Length')
    neff_plot = plt.xlabel('Length')
    neff_plot = plt.ylabel("Transmission")  
    neff_plot = plt.legend()
    neff_plot = plt.show()
    
    max_efficiency = 0
    best_length = 0
    difference = 1
    prev_val = 0
    for x, y in zip(length, trans):
        if y > max_efficiency:
            difference = y - prev_val
            max_efficiency = y
            if y - prev_val>0.0005:
                best_length = x
            prev_val = y
            
    return best_length
    
