#Main function for Adiabatic Coupler,
#Performs sweeps for W6 (Output width of SWG Coupling Taper)
#Performs sweeps for L4 (Length of the SWG Coupling Taper)

#Importing General Purpose Libraries
import numpy as np
import os
import sys
import platform 
import importlib.util

#Importing functions for material/geometry setup + Running/setup of EME Sweeps 
from ac_geometry import set_ac_materials, set_ac_geometry, set_sweep
from ac_eme import run_length_eme_sweep, get_ac_eme_results

#Importing LUMAPI 
from lumerical_lumapi import lumapi

#Width Sweeping Range of W6
#widths = [0.55e-6]
widths = np.linspace(0.5e-6,0.6e-6,3)

#Length Sweeping Range of L4
lengths = [10e-6, 120e-6]

w6 = 0
s42 = 0
s31 = 0

print('Beginning W6 Sweep....')
print('Commencing W6 Sweep....')

#Change width for every sweep
for i in range(0,len(widths)):
    
    with lumapi.MODE(hide = False) as mode:
    
        #Add materials 
        add_materials = set_ac_materials(mode)
    
        #Create Geometry of Adiabatic Taper
        ac_geometry = set_ac_geometry(mode, widths[i])
             
        #Run sweep and obtain results 
        sweep_and_results = set_sweep(mode)
        
        #Switch to layout 
        mode.switchtolayout()
      
        #Replace w6 if transmission values are higher that existing 
        if sweep_and_results[0]>s31 and sweep_and_results[1]>s42:
            s31 = sweep_and_results[0]
            s42 = sweep_and_results[1]
            w6 = widths[i]
        
print ('Optimal W6 width: '+ str(w6))
print ("Width Sweep Finished, Running Length Sweep....")  

with lumapi.MODE(hide = False) as mode:
    
    #Add materials 
    add_materials = set_ac_materials(mode)
    
    #Create Geometry of Adiabatic Taper
    set_geometry = set_ac_geometry(mode, w6)
    
    #Run length sweep and obtain results 
    run_length_sweep = run_length_eme_sweep(mode, lengths[0], lengths[1])
    l4 = get_ac_eme_results(mode, lengths[0], lengths[1])
    
    #Save Adiabatic Length Sweep 
    mode.save("adiabatic_length_sweep")
    
    #Optimized W6 and L4
    final_vals = [w6, l4]
    
print ('Optimal L4 width: '+ str(l4))
print ("Length Sweep Completed, Overall Optimization of Adiabatic Coupler Completed Successfuly.") 


        
        
        
        
        
        
    
        



