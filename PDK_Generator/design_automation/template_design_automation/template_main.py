# Suggested Packages to install/use
from common.lumerical_lumapi import lumapi
from template_geometry import TemplateGeometry
from template_simulation import TemplateSimulation
from drc_checks import DRCCheck
from lumgeo import generate_gds_from_pcell

import os
import logging

design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"template_design.yml")

def create_compact_model(process_file, hide = False):
''' Create compact model files for component.

Generates compact model files ready for Lumerical's CML Compiler or 
ready for custom script that compiles compact models into a library.

Params
------
process_file : str
    Absolute path to process file (.lbr)
hide : bool, default : False
    Hide or show simulations.
    
Returns
-------
compact_model_mapping : dict
    Mapping of location of compact model files to photonic model.
    This is based on Lumerical's CML Compiler format.
    keys = absolute path to compact model dir/files;
    values = photonic model name (str)
    
    NOTE: This can change if a custom script is used to generate a compact model.
    A reference to the generated compact model is needed for PDK-Generator to 
    copy and compile a compact model library.
    
'''

    mode = lumapi.MODE(hide = hide)
    fdtd = lumapi.FDTD(hide = hide)
    
    # Change the following to your generated code
    TS = TemplateSimulation(design_file, process_file, mode = mode, fdtd = fdtd)
    TG = TemplateGeometry(design_file, process_file, lum_app = mode)
    
    # Add code to generate compact model files
    # ....
    
    print("Done creating compact model...")
    
    mode.close()
    fdtd.close()
    
    return TS.compact_model_mapping
    
def run_design_process(process_file, hide = False):
''' Run design recipe/process for component

Run design process to simulate, optimize, and/or create compact
models for component.

Params
------
process_file : str
    Absolute path to process file (.lbr)
hide : bool, default : False
    Hide or show simulations.
    
Returns
-------
compact_model_mapping : dict
    Mapping of location of compact model files to photonic model.
    This is based on Lumerical's CML Compiler format.
    keys = absolute path to compact model dir/files;
    values = photonic model name (str)
    
    NOTE: This can change if a custom script is used to generate a compact model.
    A reference to the generated compact model is needed for PDK-Generator to 
    copy and compile a compact model library.

'''
    mode = lumapi.MODE(hide = hide)
    fdtd = lumapi.FDTD(hide = hide)
    
    # Change the following to your generated code
    TS = TemplateSimulation(design_file, process_file, mode = mode, fdtd = fdtd)
    TG = TemplateGeometry(design_file, process_file, lum_app = mode)
    
    # Add code to design component
    # ....
    
    print("Done designing component...")
    
    mode.close()
    fdtd.close()
    
    return TS.compact_model_mapping
