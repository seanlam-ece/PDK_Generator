# Suggested Packages to install/use
from template_geometry import TemplateGeometry
from math import log10, pi
from scipy.interpolate import make_interp_spline
from datetime import datetime
from shutil import copyfile
from lumgeo import generate_lum_geometry
from common.common_methods import prettify
import xml.etree.ElementTree as ET
import numpy as np
import yaml
import os
import matplotlib.pyplot as plt
import csv
import logging


class TemplateSimulation():
''' Component simulation class used to handle simulations/optimizations

Attributes
----------
design_file : str
    Absolute path to YAML design file.
process_file : str
    Absolute path to process file (.lbr).
mode : lumapi.MODE
    Lumerical simulation object for MODE
fdtd : lumapi.FDTD
    Lumerical simulation object for FDTD
interpolation_points : int
    Number of points for interpolation.
scale_factor : float
    Scale factor used to convert to SI units. (Ex. um to m)
compact_model_mapping : dict
    
design_data : dict
    Design data from design YAML file. Contains everything in YAML file.
sim_params : dict
    Simulation params from design YAML file. keys = simulation param name;
    values = simulation param value(s).
design_intent : dict
    Design intent params from design YAML file. Describes key figures of merit
    to hit. keys = design intent name; values = design intent value(s).
component_name : str
    Name/desription of component.   
techname : str
    Name of technology.
compact_model_data : dict
    Compact model params from design YAML file. keys = compact model param name;
    values = compact model param value(s).
compact_model_name : str
    Name of compact model. No spaces is preferred.
photonic_model : str
    Photonic model based on Lumerical's CML Compiler photonic models.
    https://support.lumerical.com/hc/en-us/sections/360005195993-CML-Compiler-Photonic-Models
TEM : str
    Polarization. Either "TE" or "TM".
mode_num : int
    Mode number for propagated wave. Convention is start from 0.
    Ex. Fundamental mode is 0.
wavelength : float
    Wavelength for simulation (m).
results_dir : str
    Absolute path to simulation results.
sim_dir : str
    Absolute path to simulation files.
plots_dir
    Absolute path to plots.
compact_mod_dir
    Absolute path to compact model files.
'''
    
    def __init__(self, design_file, process_file, mode = None, fdtd = None):
        ''' Initialize component simulation class
        
        Save design file, process file, and Lumerical simulation objects.
        Generate data storage dirs and prep instance variables.
        
        Parameters
        ----------
        design_file : str
            Absolute path to YAML design file
        process_file : str
            Absolute path to process file (.lbr).
        mode : lumapi.MODE, optional
            Lumerical MODE simulation object.
        fdtd : lumapi.FDTD, optional
            Lumerical FDTD simulation object.
        
        Returns
        -------
        None.
        '''
        self.design_file = design_file
        self.process_file = process_file
        self.mode = mode
        self.fdtd = fdtd
        self.interpolation_points = 10000
        
        # Set scaling to ensure SI units. Assume all distance units are in um.
        self.scale_factor = 1e-6
        
        self.get_design_params()
        self.get_process_params()
        self.create_data_dirs()
        
        # Compact model mapping
        self.compact_model_mapping = {}
        
        
    def get_design_params(self):
        ''' Get design params from YAML file
        
        Design YAML file is generated within each component directory.
        Convention is <component-name>_design.yml. Ex. if component name
        is "Waveguide", the design file is "Waveguide_design.yml"

        Returns
        -------
        None.

        '''
        try:
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain design file... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain design file... Passing...")
            return
        except TypeError:
            if type(self.design_file) == tuple:
                self.design_file = self.design_file[0]
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        
        self.design_data = data
        self.sim_params = data['simulation-params']
        self.design_intent = data['design-intent']
        self.component_name = data['name']
        
        self.techname = data.get('techname','EBeam')
        
        # Save compact model params
        self.compact_model_data = data['compact-model']
        self.compact_model_name = data['compact-model']['name']
        self.photonic_model = data['compact-model']['photonic-model']
        
        # Save design intent
        self.TEM = data['design-intent']['polarization']
        self.mode_num = data['design-intent']['mode-num'] + 1 # Define mode to start at 0
        
        # Save simulation params
        self.wavelength = data['simulation-params']['wavelength']*self.scale_factor
              
    def get_process_params(self):
        ''' Get process params
        
        Save what is necessary for simulation purposes from process file.
        Process file is .lbr format.
        
        Returns
        -------
        None.
        
        '''
        pass
     
    def create_data_dirs(self):
        '''Create data storage directories
        
        Store simulations, results, plots, and compact model files in these generated
        directories.
        
        Returns
        -------
        None.
        
        '''
        # define directories
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        self.sim_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulations")
        self.plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
        self.compact_mod_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compact_models")
        
        # create dirs if not available
        if not os.path.isdir(self.results_dir):
            os.mkdir(self.results_dir)
        if not os.path.isdir(self.sim_dir):
            os.mkdir(self.sim_dir)
        if not os.path.isdir(self.plots_dir):
            os.mkdir(self.plots_dir)
        if not os.path.isdir(self.compact_mod_dir):
            os.mkdir(self.compact_mod_dir)
     
    def setup_sim_geometry(self):
        pass
    
    def optimize_component(self):
        pass
    
    def generate_compact_model_file(self):
        pass