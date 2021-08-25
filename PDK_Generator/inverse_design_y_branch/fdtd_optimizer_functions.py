#Optimizer Function Library 

#General Purpose Imports
import os, sys
import numpy as np
import scipy as sp

try:
    import pandas as pd
except:
    import pip
    pip.main(['install', 'pandas'])
    import pandas as pd
    
#Import Parser
from parsers import parse

from lumerical_lumapi import lumapi

#Lumopt Imports for Optimization
from lumopt.utilities.wavelengths import Wavelengths
from lumopt.geometries.polygon import FunctionDefinedPolygon
from lumopt.utilities.materials import Material
from lumopt.figures_of_merit.modematch import ModeMatch
from lumopt.optimizers.generic_optimizers import ScipyOptimizers
from lumopt.optimization import Optimization

#Insert Full Path for Datafile 
datafile = os.path.join(os.path.dirname(os.path.realpath(__file__)), "y_branch_specifications.yaml")

# Default Simulation Variables
mesh_x=20e-9;
mesh_y=20e-9;
mesh_z=20e-9;
c = 3.0e8;


# CLASS FOR Y BRANCH OPTIMIZATION
class y_branch_optimization:
    
    #Initialize 
    def __init__(self,fdtd):
        """
        Initializes FDTD session, exracts component physical parameters
        and optimization settings from YAML design intent file 

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        None.

        """
        #Design intent parameters from datafile
        self._fdtd = fdtd
        self._parseparse = parse()
        self._df = self._parseparse.extract_YAML(datafile)
        #Component Parsing
        self._sub_df = self._df.iloc[0]['component']
        self._sub_df = pd.DataFrame(self._sub_df)
        #Simulation parameters from datafile
        self._sim_df = self._df.iloc[0]['optimization_variables']
        self._sim_df = pd.DataFrame(self._sim_df)
    
    def extract_x_points(self):
        """
        Extract available space in between the input and output waveguides
        for Y Branch Creation (X axis)

        Returns
        -------
        coordinates : int array
            Range of coordinates for available space in the x axis

        """
        coordinates =  []
        for i in range(len(self._sub_df)):
            if self._sub_df.loc[i,'name'] == "input_wg" or self._sub_df.loc[i,'name'] == "output_wg_top":
                coordinates.append(self._sub_df.loc[i,'x_span'])
                coordinates.append(self._sub_df.loc[i,'x'])
        return coordinates

    #Extract available space for Y Branch Creation (Y axis)
    def extract_y_points(self):
        """
       Extract available space in between the input and output waveguides
        for Y Branch Creation (Y axis)

        Returns
        -------
        coordinates : int array
            Range of coordinates for available space in the y axis
            
        """
        coordinates =  []
        for i in range(len(self._sub_df)):
            if self._sub_df.loc[i,'name'] == "input_wg" or self._sub_df.loc[i,'name'] == "output_wg_top":
                coordinates.append(self._sub_df.loc[i,'y_span'])
                coordinates.append(self._sub_df.loc[i,'y'])
        return coordinates


    def calculate_x_points(self, x_coordinates):
        """
        Uses the range of coordinates for available space in the x axis and 
        returns evenly spaced sequence in a specified interval

        Parameters
        ----------
        x_coordinates : int array
            Range of coordinates for available space in the x axis

        Returns
        -------
        initial_points_x: int array
            Array of evenly spaced range of values (x-axis)

        """
        self.starting_point_left = x_coordinates[1] + x_coordinates[0]/2
        self.starting_point_right = x_coordinates[3] - x_coordinates[2]/2
        self.initial_points_x = np.linspace(self.starting_point_left, self.starting_point_right, 10)
        return self.initial_points_x
    
    def calculate_y_points(self, y_coordinates):
        """
        Uses the range of coordinates for available space in the y axis and 
        returns evenly spaced sequence in a specified interval

        Parameters
        ----------
        y_coordinates : int array
            Range of coordinates for available space in the x axis

        Returns
        -------
        initial_points_y: int array
            Array of evenly spaced range of values (y-axis)

        """
        self.starting_point_up = y_coordinates[1] + y_coordinates[0]/2
        self.starting_point_down = y_coordinates[3] + y_coordinates[2]/2
        self.initial_points_y = np.linspace(self.starting_point_up, self.starting_point_down, 10)
        return self.initial_points_y
    
    def opt_parameter_setup_polygon(self,initial_points_y, initial_points_x):
        """
        Defines the polygon of the Y-Splitter, also takes in the draw_y_splitter

        Parameters
        ----------
        initial_points_y : int array
            Array of evenly spaced range of values (y-axis).
        initial_points_x : int array
            Array of evenly spaced range of values (x-axis)

        Returns
        -------
        
        polygon: int array
            Coordinates that outline the shape of a Y branch
        """
        initial_points_x = initial_points_x
        initial_points_y = initial_points_y
        
        def draw_y_splitter(params):
            points_x = np.concatenate(([initial_points_x.min() - 0.01e-6], initial_points_x, [initial_points_x.max() + 0.01e-6]))
            points_y = np.concatenate(([initial_points_y.min()], params, [initial_points_y.max()]))
            n_interpolation_points = 100
            polygon_points_x = np.linspace(min(points_x), max(points_x), n_interpolation_points)
            interpolator = sp.interpolate.interp1d(points_x, points_y, kind = 'cubic')
            polygon_points_y = interpolator(polygon_points_x)
            polygon_points_up = [(x, y) for x, y in zip(polygon_points_x, polygon_points_y)]
            polygon_points_down = [(x, -y) for x, y in zip(polygon_points_x, polygon_points_y)]
            polygon_points = np.array(polygon_points_up[::-1] + polygon_points_down)
            return polygon_points
        try:
            prev_results = np.loadtxt('2D_parameters.txt')
        except:
            print("Couldn't find the file containing 2D optimization parameters. Starting with default parameters")
            prev_results = initial_points_y
            
        bounds = [(0, 1.2e-6)] * initial_points_y.size
        #Changing mesh orders to simulate Si
        eps_in = Material(name = 'Si: non-dispersive', mesh_order = 2)
        eps_out = Material(name = 'SiO2: non-dispersive', mesh_order = 3)
        #Defining the polygon
        polygon = FunctionDefinedPolygon(func = draw_y_splitter, 
                                 initial_params = prev_results,
                                 bounds = bounds,
                                 z = 0.0,
                                 depth = 220.0e-9,
                                 eps_out = eps_out, eps_in = eps_in,
                                 edge_precision = 5,
                                 dx = 1.0e-9)
        return polygon

    def def_param_and_run(self, polygon):
        """
        Defines optimizer parameters and runs optimizer, saving optimized results in file 

        Parameters
        ----------
        polygon: int array
            Coordinates that outline the shape of the intial Y branch shape

        Returns
        -------
        results int array
            Array that outlines the shape the optimized Y branch 

        """
        
        wavelengths = Wavelengths(start = self._sim_df.loc[0,'start'], 
                                  stop = self._sim_df.loc[0,'stop'],
                                  points = self._sim_df.loc[0,'points'])
        
        
        fom = ModeMatch(monitor_name = 'fom', 
                mode_number = self._sim_df.loc[0,'mode_selection'],
                direction = self._sim_df.loc[0,'direction'],
                target_T_fwd = lambda wl: np.ones(wl.size),
                norm_p = 1)

        #scaling_factor = self._sim_df.loc[0,'scaling_factor']
        optimizer = ScipyOptimizers(max_iter = self._sim_df.loc[0,'max_iter'],
                            method = self._sim_df.loc[0,'method'],
                            scaling_factor = 1.0e6,
                            pgtol = self._sim_df.loc[0,'pgtol'],
                            ftol = self._sim_df.loc[0,'ftol'],
                            scale_initial_gradient_to = 0.0)
        
        opt = Optimization(base_script = __call__,
                   wavelengths = wavelengths,
                   fom = fom,
                   geometry = polygon,
                   optimizer = optimizer,
                   use_var_fdtd = False,
                   hide_fdtd_cad = False,
                   use_deps = True,
                   plot_history = True,
                   store_all_simulations = False)
        
        results = opt.run()
        
        np.savetxt('../3D_parameters.txt', results[1])
                   
        return results[1]
       
    def main(self):
        """
        Main function 

        Returns
        -------
        everything : int list
            Returns list of arrays with the following information:
                - Array that outlines the shape the optimized Y branch 
                - Array of evenly spaced range of values in which the Y branch is placed in (y-axis)
                - Array of evenly spaced range of values in which the Y branch is placed in (x-axis)
                
        """

        self.x_coordinates = self.extract_x_points()
        self.y_coordinates = self.extract_y_points()
        self.initial_points_x = self.calculate_x_points(self.x_coordinates)
        self.initial_points_y = self.calculate_y_points(self.y_coordinates)
        #self.polygon = opt_parameter_setup_polygon(self.initial_points_y)
        self.polygon = self.opt_parameter_setup_polygon(self.initial_points_y,
                                                        self.initial_points_x)
        
        self.results = self.def_param_and_run(self.polygon)
        #append initial_points_x, initial_points_y to results
        everything = np.vstack((self.results,self.initial_points_x, self.initial_points_y))

        #return self.initial_points_y
        return everything 
        

#CLASS FOR ESTABLISHING SIMULATION RECIPE IN FDTD
class recipe:

    @staticmethod
    def y_branch_init_(fdtd):
        """
        Setup FDTD session, clears any existing data 
        
        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        None.

        """
        fdtd.selectall()
        fdtd.delete()
    
    #Extract component variables 
    @staticmethod       
    def create_df_component():
        """
        Extract physical component variables (waveguide info) 
        from design intent YAML file 

        Returns
        -------
        sub_df : panda dataframe
            Dataframe with component physical parameters
        """
            parseparse = parse()
            df = parseparse.extract_YAML(datafile)
            sub_df = df.iloc[0]['component']
            sub_df = pd.DataFrame(sub_df)
            return sub_df
        
    @staticmethod 
    def define_material(fdtd):
        """
        Simulates/builds material that Y Branch is drawn with/built on

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        Nothing signifcant to the code (sub_df is just the layering information)

        """
        
        parseparse = parse()
        df = parseparse.extract_YAML(datafile)
        sub_df = df.iloc[0]['layers_used']
        sub_df = pd.DataFrame(sub_df)
        _sim_df = df.iloc[0]['optimization_variables']
        _sim_df = pd.DataFrame(_sim_df)
        
        for i in range(len(sub_df)):
            
            opt_material= fdtd.addmaterial(sub_df.loc[i,'material_type'])
            opt_material = str(opt_material)
            fdtd.setmaterial(opt_material,'name',sub_df.loc[i,'name'])
            n_opt = fdtd.getindex(sub_df.loc[i,'material_name'],c/_sim_df.loc[0,'center_wavelength'])
            fdtd.setmaterial(sub_df.loc[i,'name'],'Refractive Index',n_opt)
        return sub_df
    
    @staticmethod 
    def draw_waveguide(df,fdtd):
        """
        Draws waveguides specified in dataframe with component physical parameters 

        Parameters
        ----------
        df : panda dataframe
            Dataframe with component physical parameters
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        None.

        """
        
        for i in range(len(df)):
            
            fdtd.addrect();
            fdtd.set('name',df.loc[i,'name'])
            fdtd.set('x span',df.loc[i,'x_span'])
            fdtd.set('y span',df.loc[i,'y_span'])
            fdtd.set('z span',df.loc[i,'z_span'])
            fdtd.set('y',df.loc[i,'y'])
            fdtd.set('x',df.loc[i,'x'])
            fdtd.set('z',df.loc[i,'z'])
            fdtd.set('material',df.loc[i,'material'])
            
            if df.loc[i,'material'] == "SiO2: non-dispersive":
                fdtd.set('override mesh order from material database',1)
                fdtd.set('mesh order',df.loc[i,'mesh_order'])
                fdtd.set('alpha',df.loc[i,'alpha'])
        
    #Extract simulation variables
    @staticmethod
    def extract_sim_param():
        """
        Extract simulation variables from Design Intent YAML 

        Returns
        -------
        _sim_df : panda dataframe
            Dataframe with simulation parameters from Design Intent YAML

        """
        _parseparse = parse()
        _df = _parseparse.extract_YAML(datafile)
        _sim_df = _df.iloc[0]['optimization_variables']
        _sim_df = pd.DataFrame(_sim_df)
        return _sim_df
    
    @staticmethod 
    def configure_fdtd(fdtd,component_df,sim_df):
        """
        Configures FDTD Eigensolver Dimensions and settings

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        component_df : panda dataframe
            Dataframe with component physical parameters
        sim_df : panda dataframe
            Dataframe with simulation parameters from Design Intent YAML

        Returns
        -------
        None.

        """
        fdtd.addfdtd();
        fdtd.set('mesh accuracy',2)
        fdtd.set('dimension',"3D")
        fdtd.set('x', 0)
        fdtd.set('x span',(component_df.loc[1,'x']+component_df.loc[1,'x_span']/2))
        fdtd.set('y',0)
        fdtd.set('y span',component_df.loc[1,'y']*10)
        fdtd.set('z',0)
        fdtd.set('z span',component_df.loc[1,'z_span']*7)
        fdtd.set('force symmetric y mesh',1)
    
    # Add mode source 
    @staticmethod 
    def add_mode_source(fdtd,component_df,sim_df):
        """
       Configures FDTD Mode Source Dimensions and Settings

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        component_df : panda dataframe
            Dataframe with component physical parameters
        sim_df : panda dataframe
            Dataframe with simulation parameters from Design Intent YAML

        Returns
        -------
        None.

        """
        fdtd.addmode();
        fdtd.set('direction',sim_df.loc[0,'direction'])
        fdtd.set('injection axis',sim_df.loc[0,'injection_axis'])
        fdtd.set('y',0)
        fdtd.set("y span",component_df.loc[1,'y_span']*10);
        fdtd.set('x',component_df.loc[0,'x']+(component_df.loc[0,'x_span']/4))
        fdtd.set('z span',component_df.loc[1,'z_span']*7)
        fdtd.set('center wavelength',sim_df.loc[0,'center_wavelength'])
        fdtd.set('wavelength span',0)
        fdtd.set('mode selection',sim_df.loc[0,'mode_selection'])
        #normally you would just select the fundamental TE mode, but for some reason that 
        #doesn't work
        
    @staticmethod 
    def add_port(fdtd,df):
        """
        Adds ports for S-parameter sweeps

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        df :panda dataframe
            Dataframe with component physical parameters.

        Returns
        -------
        None.

        """
        for i in range(len(df)):
            if df.loc[i,'name'] != "Si02":
                fdtd.addport()
                fdtd.set('name',df.loc[i,'name'])
                fdtd.set('x span', 0)
                if df.loc[i,'x']<0:
                    fdtd.set('x', (df.loc[i,'x']+(df.loc[i,'x_span']/2)))
                    #fdtd.set('x', -1e-06 )
                    fdtd.set('y', df.loc[i,'y'])
                    fdtd.set('y span', df.loc[i,'y_span'])
                else:
                    fdtd.set('x', (df.loc[i,'x']-(df.loc[i,'x_span']/2)))
                    #fdtd.set('x', 1e-06 )
                    fdtd.set('y', df.loc[i,'y'])
                    fdtd.set('y span', df.loc[i,'y_span']+0.2e-6)
                fdtd.set('z', df.loc[i,'z'])
                fdtd.set('z span',df.loc[i,'z_span'])
                if df.loc[i,'x'] <0:
                    fdtd.set('direction','Forward')
                else:
                    fdtd.set('direction','Backward')
                fdtd.set('injection axis','x-axis')
                fdtd.set('mode selection','fundamental TE mode');
                #dtd.select('Calculate Modes')
                #fdtd.select('Select Mode(s)')

    @staticmethod 
    def add_mesh(fdtd,df):
        """
        Adds Mesh Region for Better Simulation Accuracy

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        df :panda dataframe
            Dataframe with component physical parameters.

        Returns
        -------
        None.

        """
        fdtd.addmesh();
        fdtd.set('x',0);
        fdtd.set('x span',(df.loc[1,'x']-(df.loc[1,'x_span']/2))*(9/5)*2)
        fdtd.set('y',0);
        fdtd.set('y span',(5/6)* 3e-6)
        #fdtd.set('y span',(df.loc[1,'y']+(df.loc[1,'y_span']/2))*(6/5)*2)
        fdtd.set('z',0);
        fdtd.set('z span',(df.loc[1,'z_span']/2)*30)
        fdtd.set('dx',mesh_x);
        fdtd.set('dy',mesh_y);
        fdtd.set('dz',mesh_z);
    
    @staticmethod 
    def add_monitors(fdtd,df):
        """
        Add monitors to provide time-domain information for field components

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        df :panda dataframe
            Dataframe with component physical parameters.

        Returns
        -------
        None.

        """
        fdtd.addpower();
        fdtd.set('name','opt_fields');
        fdtd.set('monitor type','3D');
        fdtd.set('x',0);
        fdtd.set('x span',(df.loc[1,'x']-(df.loc[1,'x_span']/2))*(9/5)*2);
        fdtd.set('y',0);
        fdtd.set('y span',(5/6)* 3e-6);
        fdtd.set('z',0);
        fdtd.set('z span',0.4e-6);
    
    @staticmethod
    def add_fom(fdtd,df):
        """
        Add monitor for figure of merit 
        
        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product
        df :panda dataframe
            Dataframe with component physical parameters.

        Returns
        -------
        None.

        """
        fdtd.addpower();
        fdtd.set('name','fom');
        fdtd.set('monitor type','2D X-Normal');
        fdtd.set('x',(df.loc[1,'x']-(df.loc[1,'x_span']/2))*(9/5));
        fdtd.set('y',0);
        fdtd.set('y span',3e-6);
        fdtd.set('z',0);
        fdtd.set('z span',1.2e-6)
        
    # Main function 
    @staticmethod
    def main(fdtd):
        """
        Main function

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        Nothing signifcant to the code (layer_df is just the layering information)

        """
        #Initialize FDTD Session
        recipe.y_branch_init_(fdtd)
        
        component_df = recipe.create_df_component()
        
        layer_df = recipe.define_material(fdtd)
        
        sim_df = recipe.extract_sim_param()
        
        draw_waveguides = recipe.draw_waveguide(component_df,fdtd)
        
        configure_fdtd = recipe.configure_fdtd(fdtd,component_df,sim_df)
        
        add_mode = recipe.add_mode_source(fdtd,component_df,sim_df)
        
        add_mesh = recipe.add_mesh(fdtd,component_df)
    
        add_monitors = recipe.add_monitors(fdtd,component_df)
        
        add_fom = recipe.add_fom(fdtd,component_df)
        
        fdtd.save("y_branch_3D")
        
        return layer_df
    
    def insert_ports(fdtd):
        """
        Calls the function that adds ports for FDTD

        Parameters
        ----------
        fdtd : method
            calls the contructor for the Lumerical FDTD product

        Returns
        -------
        None.

        """
        
        component_df = recipe.create_df_component()
        add_ports = recipe.add_port(fdtd,component_df)
    
# This function is called by the optimizer and constructs the base script 
def __call__(fdtd):
    """
    This function is called by the optimizer and constructs the base script 
    Parameters
    
    ----------
    fdtd : method
            calls the contructor for the Lumerical FDTD product

    Returns
    -------
    None.

    """
    
    FDTD = recipe.main(fdtd)

#This class retrieves the optimization requirements     
class retrieve_reqs:
    
    @staticmethod
    def parse_reqs():
        """
        Retrieves optimization requirements from Design Intent YAML

        Returns
        -------
        req_arr : int array
            Array that lists optimization requirements

        """
        _parseparse = parse()
        _df = _parseparse.extract_YAML(datafile)
        _opt_req_df = _df.iloc[0]['optimization_reqs']
        _opt_req_df = pd.DataFrame(_opt_req_df)
        
        req_arr = []
        for i in range(len(_opt_req_df)):
            req_dict.append(_opt_req_df.loc[i,'gain_through_single_port'])
            
        return req_arr
    