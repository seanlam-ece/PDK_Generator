#Sweep for PSR BiTaper Neff vs Waveguide Width 
#Runs a LA sweep for each LB that is listed

#General Purpose Libraries 
import numpy as np
import platform 

#Import functions for material setup + simulation recipes
from eme_transmission_taper_length_sweep_setup import bitaper_length_sweep
from neff_taper_width_sweep_setup import material_setup

#Import LUMAPI
from lumerical_lumapi import lumapi

#Range of LB Length to sweep
LB=np.linspace(13e-6,60e-6,6)
#LB = [60e-6]

#Class that runs length sweep
class length_sweep:
    
    @staticmethod
    def main(x, width_sweep):

        with lumapi.MODE(hide = False) as mode:
            
            #Material Setup
            material = material_setup.add_material(mode)
            
            #Component Setup and Sweep
            polygon = bitaper_length_sweep.setup_polygons(mode,x,width_sweep)
            setup = bitaper_length_sweep.eme_solver(mode)
            run = bitaper_length_sweep.run_eme(mode,x)
            
            #Switch Back to Layout Mode
            mode.switchtolayout()
            return run
        



    
    