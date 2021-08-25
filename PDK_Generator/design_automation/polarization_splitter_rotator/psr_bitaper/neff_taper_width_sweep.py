#Function that performs PSR Bitaper Neff - Waveguide Width Sweep

#General Purpose Libaries
try:
    import matplotlib.pyplot as plt
except:
    import pip
    pip.main(['install', 'matplotlib'])
    import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import platform 

#Import LUMAPI
from lumerical_lumapi import lumapi

#Import libraries for sweep and material setup
from neff_taper_width_sweep_setup import width_sweep_setup, material_setup

#Output Modes
modes=3

#Sweep range of widths (ridge waveguide)
width_ridge_list=np.linspace(0.4,0.9,100)*1e-6 

#Sweep range of widths (slab waveguide)
width_slab_list=np.linspace(0.4,1.9,100)*1e-6

#Class that performs width sweep 
class width_sweep:
    
    @staticmethod
    def main():

        with lumapi.MODE(hide = False) as mode:
            
            #Adding materials, drawing photonic components and simulation recipe setup
            material = material_setup.add_material(mode)
            draw_wg = width_sweep_setup.wg_2D_draw(mode)
            sweep = width_sweep_setup.wg_2D_func(mode)
    
            mode.set("number of trial modes",modes+1);
            neff = []
            TE00 = []
            TM00 = []
            TE01 = []

            #Finding the modes for each specified waveguide width
            for i in range (0,len(width_ridge_list)):
                mode.switchtolayout()
                mode.setnamed("waveguide","y span", width_ridge_list[i])
                mode.setnamed("mesh1","y span", width_ridge_list[i])
                mode.setnamed("slab","y span", width_slab_list[i])
                mode.setnamed("mesh2","y span", width_slab_list[i])
                n = mode.findmodes()
                mode.save("bitaper_mode_calculations")
                
                #For each mode, simulate/extract the effective index for corresponding width
                for m in range(1,4):
                    if m == 1:
                        data = abs(mode.getdata("FDE::data::mode"+str(m),"neff"))
                        data = data[0][0]
                        TE00.append(data)
                        mode.selectmode("mode1")
                        #mode.setanalysis("track selected mode",1);
                        #mode.setanalysis("detailed dispersion calculation",1);
                        #mode.frequencysweep()
                        #loss_data = mode.getdata("frequencysweep","loss")
                        
                    elif m == 2:
                        data = abs(mode.getdata("FDE::data::mode"+str(m),"neff"))
                        data = data[0][0]
                        TM00.append(data)
                    elif m == 3:
                        data = abs(mode.getdata("FDE::data::mode"+str(m),"neff"))
                        data = data[0][0]
                        TE01.append(data)

            #Append to arrays for data visualization
            neff.append(TE00)
            neff.append(TM00)
            neff.append(TE01)
            
            neff_plot = plt.plot(width_ridge_list, TE00, label = "TE00")
            neff_plot = plt.plot(width_ridge_list, TM00, label = "TM00")
            neff_plot = plt.plot(width_ridge_list, TE01, label = "TE01")
            neff_plot = plt.title('Neff vs Waveguide Width')
            neff_plot = plt.xlabel('Width (10e-7 m)')
            neff_plot = plt.ylabel("Neff")  
            neff_plot = plt.legend()
            neff_plot = plt.show()
           
            #Find starting width: Find the width that is closest to the neff cutoff of the fundamental mode (1.465)
            width_begin = 0
            for x, y in zip(width_ridge_list, TE01):
                if x < 5e-07 and x > 4e-07:
                    if y<1.467 and y >1.463:
                        width_begin = x
                        
            #Find hybrid point to determine hybrid region           
            hybrid_point = 0
            max_differ = sys.maxsize
            for x, y, z in zip(width_ridge_list, TE01, TM00):
                if z - y < max_differ:
                    max_differ = z - y
                    hybrid_point = x
                    
            #Find middle width: Scans a range between (+-50nm) of the hybrid region to find the point that has the most gentle slope
            maxslope = 1
            difference = 1
            width_middle = 0
            for x, y in zip(width_ridge_list, TE01):
                if x < hybrid_point + 50e-9 and x> hybrid_point - 50e-9:
                    if y - difference <maxslope:
                        maxslope = y - difference
                        width_middle = x
                    difference = y 
            
            #Find end width: find largest discrepancy between TM00, TE01 
            #Ensures most efficient mode conversion
            width_end = 0
            max_diff = 0
            for x, y, z in zip(width_ridge_list, TE01, TM00):
                if x < 9e-07 and x> 6.5e-07:
                    if z - y > max_diff:
                        max_diff = z - y
                        width_end = x
            
            #Returns widths as an array
            widths = [width_begin, width_middle, width_end]
            mode.save("bitaper_mode_calculations")
            return widths
  
#plot = width_sweep.main()


