#CODE FUNCTION: Produces 3 Dimensional Y-Branch, optimized with parameters extracted from a YAML file
#OPTIMIZER: Optimizes Insertion Loss/Transmission 

#General Purpose Libraries
import numpy as np
import os
import sys

#Import classes from other files 
from parsers import parse, exports
from interconnect_functions import FDTD_draw_splitter_sparam_sweep, INTC_functions
from fdtd_optimizer_functions import y_branch_optimization, __call__,recipe, retrieve_reqs
from drc_checks import DRCCheck, export_gds

#Import LUMOPT    
from lumerical_lumapi import lumapi

#GDS Filepath to save
gds_filepath = r'C:\Users\victo\Documents\SiEPIC_Work\Inverse Design Y Branch\y_branch_3D.gds'

#Tech Name
techname = "SiEPICfab-Grouse-Base"

#Component Name
component_name = "y-branch"

with lumapi.FDTD(hide = True) as fdtd1:
    
    print("\n")
    
    #Draw waveguides for DRC checks
    print("Drawing waveguides to GDS file for initial DRC check....\n")
    waveguides = recipe.main(fdtd1)
    
    #Export as GDS for DRC check
    gds_export_script_1 = export_gds(fdtd1, "y_branch_3D", 'model', [1, {0}, {1}])
    #fdtd1.eval(gds_export_script)
    print("GDS with Waveguides ONLY Printed.\n")
    
#Running DRC Check
print("Running First DRC Check....\n")
y_branch_DRC = DRCCheck()
DRC = y_branch_DRC.run_drc(techname, gds_filepath, component_name)

#Proceed to optimizations if DRC checks pass 
if DRC == True:
    with lumapi.FDTD(hide = True) as fdtd:
        
        #Run optimizations
        print("Running optimizations...\n")
        results = y_branch_optimization(fdtd).main()
        '''
        results = np.array([[ 2.76126801e-07,  3.29060956e-07,  2.88481994e-07,
         2.69174294e-07,  3.56542244e-07,  5.77472437e-07,
         6.10329076e-07,  6.11647896e-07,  6.20592465e-07,
         5.93398925e-07],
       [-1.00000000e-06, -7.77777778e-07, -5.55555556e-07,
        -3.33333333e-07, -1.11111111e-07,  1.11111111e-07,
         3.33333333e-07,  5.55555556e-07,  7.77777778e-07,
         1.00000000e-06],
       [ 2.50000000e-07,  2.88888889e-07,  3.27777778e-07,
         3.66666667e-07,  4.05555556e-07,  4.44444444e-07,
         4.83333333e-07,  5.22222222e-07,  5.61111111e-07,
         6.00000000e-07]])
        '''
        print("Optimizations complete.\n")

        #Redrawing waveguides, splitter on FDTD to setup s-parameter sweep
        revised = recipe.main(fdtd)
    
        #Adding ports for s parameter sweep 
        ports = recipe.insert_ports(fdtd)

        #Running s-parameter sweep
        print("Running S-parameter sweeps.....")
        polygon_points = FDTD_draw_splitter_sparam_sweep(fdtd, results).main()
    

        with lumapi.INTERCONNECT(hide = True) as intc:
    
            print("Running Design Requirement Checks...\n")
            #Retrieving Requirement Checks
            req = retrieve_reqs().parse_reqs()
            #Run Interconnect Simulations and Display Results
            INTC = INTC_functions(intc, req).main()
    
        #Export to K Layout if meets requirements 
        
        fdtd.save("y_branch_3D")
        gds_export_script_2 = export_gds(fdtd, "y_branch_3D", 'model', [1, {0}, {1}])
        print("Full GDS (Y-branch and waveguides) Printed.\n")
else:
    raise Exception("Initial DRC Check Failed, please revise YAML document/GDS file/Simulation Parameters")
    

print("Requirement checks passed\n")    
#Run final DRC check
print("Final DRC check commencing....\n")
DRC2 = y_branch_DRC.run_drc(techname, gds_filepath, component_name)

if (DRC2 == True and INTC == True):
    print ("Final DRC Check passed and design requirements passed")
    print ("Y - branch successfully optimized.\n")
    print ("Lumerical (FSP) with simulated/optimized design available in directory.\n")
    print ("K Layout GDS file of simulated/optimized design available in directory.\n")

else:
    raise Exception("DRC Check Failed, please revise YAML document/GDS file/Simulation Parameters")

