# Suggested Packages to install/use
from common.lumerical_lumapi import lumapi
from klayout import db
from common.common_methods import get_klayout_app_path
try:
    from lumgen.lumgeo import generate_lum_geometry, generate_gds_from_pcell
except:
    from lumgeo import generate_lum_geometry, generate_gds_from_pcell
import yaml
import os
import logging

class TemplateGeometry():
'''Component geometry class used to handle simulation geometries


Attributes
----------
lum_app : lumapi
    Lumerical simulation object (ex. MODE or FDTD)
process_file : str
    Absolute path to process file (.lbr).
design_file : str
    Absolute path to YAML design file.
techname : str
    Name of technology.
libname : str
    Name of library for which this component can found within.
gds_dir : str
    Absolute path of GDS directory for this component. Sweeping geometry
    and generating multiple GDS goes in this directory.
    
Examples
--------
The following shows how to generate a GDS. NOTE: Fill in the method for generate_gds()
to create a GDS.

>>> CompGeo = TemplateGeometry()
>>> CompGeo.generate_gds()

'''
    
    def __init__(self, design_file, process_file, lum_app = None):
        '''Initialize geometry class
        
        Saves design file, process file, and Lumerical simulation object as
        instance vars.
        
        Parameters
        ----------
        design_file : str
            Absolute path to YAML design file
        process_file : str
            Absolute path to process file (.lbr).
        lum_app : lumapi, optional
            Lumerical simulation object (ex. MODE or FDTD)
            
        Returns
        -------
        None.
        '''
    
        self.lum_app = lum_app
        self.process_file = process_file
        self.design_file = design_file
        
        self.get_geometry_params()
        self.create_geometry_dirs()

    
    def get_geometry_params(self):
        ''' Get geometry params from YAML file
        
        GDS layers are defined by a layer number and datatype (i.e. 1/0, 1 is 
        the layer number and 0 is the datatype)

        Returns
        -------
        None.

        '''
        try:
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain layer info... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain layer info... Passing...")
            return
        except TypeError:
            if type(self.design_file) == tuple:
                self.design_file = self.design_file[0]
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        
        # Save tech,lib, pcell names
        self.techname = data.get('techname','EBeam')
        self.libname = data.get('libname','EBeam')
        
        # Save base geometry params
        
        # Save layer source info (i.e. 1:0)
    
    def get_process_params(self):
        ''' Get process params from YAML or LBR file
        
        Process file is .lbr format.
        
        Returns
        -------
        None.
        
        '''
        pass
    
    def create_geometry_dirs(self):
        '''Create GDS directory to store generated GDS
        
        Returns
        -------
        None.
        
        '''
        # define paths
        self.gds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gds")
        
        # create dirs if not available
        if not os.path.isdir(self.gds_dir):
            os.mkdir(self.gds_dir)
            
    def generate_gds(self):
        pass

if __name__ == "__main__":
    pass

