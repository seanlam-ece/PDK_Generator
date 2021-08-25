#Interconnect and FDTD Functions For Y Branch Generation

# General Purpose Imports
import pandas as pd
import numpy as np
import scipy as sp

#Import Parser
from parsers import parse

#Library for Lumerical
from lumerical_lumapi import lumapi

#Library for data ploting
try:
    import matplotlib.pyplot as plt
except:
    import pip
    pip.main(['install', 'matplotlib'])
    import matplotlib.pyplot as plt

#CLASS FOR FDTD S PARAMETER SWEEP
class FDTD_draw_splitter_sparam_sweep:

    def __init__(self, fdtd, results):
        """
        Exracting results from optimizations and
        initializes FDTD session

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        results : int array
            results from the optimizations 
        Returns
        -------
        None.

        """
        self.fdtd = fdtd
        self.results = results[0]
        self.initial_points_x = results[1]
        self.initial_points_y = results[2]
        
    # Drawing the Y-splitter on FDTD
    def draw_polygon(self,results):
        """
        Draws the Y-Splitter on FDTD

        Parameters
        ----------
        results : int array
            results from the optimizations 

        Returns
        -------
        None.

        """
        self.fdtd.addpoly(vertices = results)
        self.fdtd.set('x', 0.0)
        self.fdtd.set('y', 0.0)
        self.fdtd.set('z', 0.0)
        self.fdtd.set('z span', 220.0e-9)
        self.fdtd.set('material','Si: non-dispersive')
    
    def add_s_param_sweep(self):
        """
        Add S-Parameter Sweep and generates datafile for Interconnect Simulations

        Returns
        -------
        None.

        """
        self.fdtd.addsweep(3)
        self.fdtd.setsweep("s-parameter sweep", "name", "s-parameter sweep")
        self.fdtd.setsweep("s-parameter sweep", "Excite all ports", 1)
        self.fdtd.runsweep("s-parameter sweep")
        self.fdtd.exportsweep("s-parameter sweep", "s_parameters_y_branch_data.dat")
        
    # Draw Y Splitter
    def draw_y_splitter(self,initial_points_x, initial_points_y):
        """
        Function for constructing the Y-Splitter using optimization results 

        Parameters
        ----------
        initial_points_x : int array
            Range of coordinates along the x axis in which the Y-branch is generated 
        initial_points_y : int array
            Range of coordinates along the y axis in which the Y-branch is generated

        Returns
        -------
        polygon_points : int array
            Coordinates that outline the shape of a Y branch

        """
        points_x = np.concatenate(([initial_points_x.min() - 0.01e-6], initial_points_x, [initial_points_x.max() + 0.01e-6]))
        points_y = np.concatenate(([initial_points_y.min()], self.results, [initial_points_y.max()]))
        n_interpolation_points = 100
        polygon_points_x = np.linspace(min(points_x), max(points_x), n_interpolation_points)
        interpolator = sp.interpolate.interp1d(points_x, points_y, kind = 'cubic')
        polygon_points_y = interpolator(polygon_points_x)
        polygon_points_up = [(x, y) for x, y in zip(polygon_points_x, polygon_points_y)]
        polygon_points_down = [(x, -y) for x, y in zip(polygon_points_x, polygon_points_y)]
        polygon_points = np.array(polygon_points_up[::-1] + polygon_points_down)
        return polygon_points
    
    def main(self):
        """
        Main function that generates s parameter datafile

        Returns
        -------
        None
        
        """
        self.polygon_points = self.draw_y_splitter(self.initial_points_x,self.initial_points_y)
        self.draw_polygon = self.draw_polygon(self.polygon_points)
        self.add_s_param_sweep()
        return self.polygon_points
 
#CLASS FOR INTERCONNECT FUNCTIONS
class INTC_functions():
    
    def __init__(self, intc,req):
        """
        Exracting design requirements from YAML and
        initializes INTERCONNECT session

        Parameters
        ----------
        intc : method
            calls the contructor for the Lumerical INTERCONNECT product
        req : int
            design requirement threshold 

        Returns
        -------
        None.

        """
        self.intc = intc
        self.req = req
    
    def setup(self):
        """
        Loading s-parameter datafile in interconnect, adding ONA and connections

        Returns
        -------
        None.

        """
        #Load file into DAT
        self.intc.addelement("Optical N Port S-Parameter")
        self.intc.set('load from file',True)
        self.intc.set('s parameters filename','s_parameters_y_branch_data.dat')
        
        #Add optical network analyzer
        self.intc.addelement('Optical Network Analyzer')
        self.intc.set('number of input ports',2)
        self.intc.set('plot kind','wavelength')
        self.intc.set('number of points', 5000)
        self.intc.set('input parameter', 'start and stop')
        self.intc.set('start frequency',187.5e12)
        self.intc.set('stop frequency', 200e12)
        
        #Connect Ports to check for insertion loss
        self.intc.connect('ONA_1','output','SPAR_1', 'port 1' )
        self.intc.connect('ONA_1','input 1','SPAR_1', 'port 2' )
        self.intc.connect('ONA_1','input 2','SPAR_1', 'port 3' )
          
    def listToString(self,s):
        """
        Function that converts List to String 

        Parameters
        ----------
        s : list
            List to be converted.

        Returns
        -------
        string
            String converted from a list.

        """
        string = ""
        return (string.join(s))
        
    def run_simulation_results(self):
        """
        Runs simulations of Y branch to check if insertion losses through one port meet requirements
        Also prints a graph of the results

        Returns
        -------
        bool
            Returns 'True' if passses requirements
            Returns 'False' if fails requirements 

        """
        #Run Simulations, print graphs 
        results = self.intc.run()
        available_simulations = self.intc.getresultdata('ONA_1')
        available_sim = available_simulations.split('\n')
        self.intc.save("test_interconnect")
        
       
        data1 = self.intc.getresult('ONA_1',"input 1/mode 1/gain")
        data = self.intc.getresult('ONA_1',"input 1/mode 1/transmission")
        attr = data['Lumerical_dataset']['attributes']
        self.attr_str = self.listToString(attr)
        #Plot graphs
        self.help = plt.plot(data['wavelength']*10e8,
                 abs(data[self.attr_str])**2)
        self.help = plt.title('Transmission vs Wavelength (Through One Port)')
        self.help = plt.xlabel('Wavelength (nm)')
        self.help = plt.ylabel(self.attr_str)        
        self.help = plt.show()
        req = self.req[0]
        for i in data1['mode 1 gain (dB)']:
            if i < req:
                print ("Insertion Loss exceeds design requirements, please revise YAML and resimulate/reoptimize")
                return False
        #Checking 
        return True
      
        
    def save_intc_file(self):
        """
        Saves INTERCONNECT file

        Returns
        -------
        None.

        """
        self.intc.save("interconnect_testing_y_branch")
        return
    
    def save_to_CML(intc):
        """
        CML Compiler Function 

        Parameters
        ----------
        intc : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        out = intc.customlibrary()
        #path = intc.getpath()
        #intc.addpath("C://Users//victo//AppData//Roaming//Custom")
        path = intc.getpath()
        intc.save("Y_Branch_Test")
        intc.packagedesignkit("dk", "dk.cml", 'none')
        intc.importschematic("Y-Branch",'Y_Branch_Test.ice')
        
    #Main function
    def main(self):
        """
        Main function

        Returns
        -------
        None.

        """
        self.setup()
        self.graphs = self.run_simulation_results()
        self.save_intc_file()
        return self.graphs