#Main function for PSR Bitaper Length and Width Sweeps 

#General Purpose Libraries
import numpy as np

#Imported functions for width and length sweeps
from neff_taper_width_sweep import width_sweep
from eme_transmission_taper_length_sweep import length_sweep 

#Range of LB Length to sweep
LB=np.linspace(12e-6,60e-6,6)

ideal_LA = 0
ideal_LB = 0
best_eff = 0

#Run Bitaper Width Sweep
print("Sweeping PSR Bitaper Widths.....")
width_sweep = width_sweep.main()

print("Widths for PSR Bitaper [start width, middle width, end width: "+ str(width_sweep))
print("Sweeping PSR Bitaper Lengths.....")

#Run Bitaper Length Sweep and Optimize for Best Transmission 
for x in LB:
    run = length_sweep.main(x, width_sweep)
    
    if run[1] > best_eff:
        ideal_LB = x
        ideal_LA = run[0][0]*10-6
        best_eff = run[1]
    
#Optimized LA, LB values 
lengths = [ideal_LA, ideal_LB, best_eff]
