from common.lumerical_lumapi import lumapi
from klayout import db
from common.common_methods import get_klayout_app_path
try:
    from lumgen.lumgeo import generate_lum_geometry, generate_gds_from_pcell
except:
    from lumgeo import generate_lum_geometry, generate_gds_from_pcell
import yaml
import os

class WaveguideStripGeometry():
    
    def __init__(self, design_file, process_file, lum_app = None):
        self.lum_app = lum_app
        self.process_file = process_file
        self.design_file = design_file
        self.klayout_app_path = None
        self.create_gds_klayout_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),"lumgen","create_gds_klayout.py")
        self.layer = {}
        
        self.dbu = 0.001
        self.length = 3.0
        self.bend_to_straight_margin = 10.0 # Distance from edge of bent waveguide to edge of straight waveguide
        self.get_geometry_params()
        self.create_geometry_dirs()

    
    def get_geometry_params(self):
        ''' Get geometry params and GDS layer info (layer number and datatype)
        
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
        self.pcellname = data.get('pcellname', 'Waveguide')
        
        # Save base geometry params
        self.width = data['design-params']['width']
        self.radius = data['design-params']['radius']
        self.bezier = data['design-params']['bezier']
        
        # Save layer source info (i.e. 1:0)
        for name, info in data['layers'].items():
            self.layer[name] = info.split(' - ')[-1]
            
        
    def generate_gds_from_width(self, width):
        ''' Generate GDS of waveguide
        
        GDS is stored in same directory as python file.

        Parameters
        ----------
        width : float
            Waveguide width (um)
        length : float
            Waveguide length (um)

        Returns
        -------
        file_dir : str
            Absolute path of GDS file

        '''
        # TODO: Get technology params
        # TODO: Use SiEPIC to get tech params (dbu)
        self.dbu = 0.001
        
        # Create layout object with top cell
        ly = db.Layout()
        top = ly.create_cell("TOP")
        
        # Define layer(s)
        ly_number = int(self.layer['Waveguide'].split(':')[0])
        ly_datatype = int(self.layer['Waveguide'].split(':')[1])
        
        wg_layer = ly.layer(ly_number, ly_datatype)
        
        # Generate geometric shapes
        wg_geometry = db.Box(0, -self.length/self.dbu/2, width/self.dbu, self.length/self.dbu)
        
        # Insert shape(s) into layout under parent cell
        top.shapes(wg_layer).insert(wg_geometry)
        
        # Write to GDS
        file_dir = os.path.join(self.gds_dir,"Waveguide_w="+str(int(width/self.dbu))+"nm.gds")
        ly.write(file_dir)
        print("Created %s" % file_dir)
        
        return file_dir
        
   
    def generate_gds_from_params(self, width, radius, bezier):
        if self.klayout_app_path == None:
            self.klayout_app_path = get_klayout_app_path()
        
        length = radius + self.bend_to_straight_margin
        gds_path = os.path.join(self.gds_dir,"Waveguide_w={}nm_r={}nm_b={}.gds".format(int(width*1000), int(radius*1000), bezier))
        generate_gds_from_pcell(gds_path, self.techname, self.libname, self.pcellname,
                                    params = {"path": [[0,0],[length,0], [length,length]],
                                              "radius": radius, "widths": [width], "bezier": bezier, "adiab": 1})
        
        return gds_path
    
    def sweep_width(self, width_range, resolution):
        ''' Generate GDS sweep of widths given a resolution
        
        Sweep width given the resolution and get as close as possible to the end
        width range.

        Parameters
        ----------
        width_range : list
            List of size 2 where the first number indicates the start of the width
            sweep (um) and the second indicates the end of sweeping widths (um)
        resolution : float
            Amount incremented to get to next width (um)

        Returns
        -------
        self.width_sweep_mapping: dict
            Keys = GDS file paths (type: str), Vals = Waveguide widths in um (type: float) 

        '''
        print("Create waveguide GDS sweeping widths")
        
        self.width_sweep_mapping = {}
        width = width_range[0]
        while width <= width_range[1]:
            self.width_sweep_mapping[self.generate_gds_from_width(width)] = width
            width = width + resolution
            
        return self.width_sweep_mapping
    
    def sweep_radius(self, width, radius_range, resolution):
        ''' Generate GDS sweep of radii given a resolution
        
        Sweep radii give the resolution and get as close as possible to the end radius
        range.
        
        Command line commands that work:
        #C:\\klayout-0.26.6-win64\\klayout_app.exe -b -r C:\\Users\\seanl\\KLayout\\pymacros\\test_python_cmd_line.py -rd bob="hello world"                 
        #C:\\klayout-0.26.6-win64\\klayout_app.exe -r "C:\\Users\\seanl\\Documents\\01_UBC\\Academics\\Grad School\\01_Work\\PDK-Generator\\Repo\\PDK-Generator\\python\\lumgen\\create_gds_klayout.py" -rd techname="EBeam" -rd libname="EBeam" -rd pcellname="Waveguide" -rd out_dir="C:\\Users\\seanl\\Downloads\\test7.gds" -rd params="{\\"radius\\": 2}"

        Parameters
        ----------
        width : float
            Waveguide width (um)
        radius_range : list of floats (Size of 2)
            First entry is the minimum radius, second entry is the max radius. (um)
        resolution : float
            Increment size between each radii value. (um)

        Returns
        -------
        self.radius_sweep_mapping : dict
            Keys = GDS file location, Vals = Radius (um)

        '''
        
        print("Create waveguide GDS sweeping radii")
        print("Running KLayout in command line...")
        print("NOTE: If you copy and paste the following commands into cmd line, ensure quotations are around file paths so that spaces are captured\n")
        
        if self.klayout_app_path == None:
            self.klayout_app_path = get_klayout_app_path()
        
        self.radius_sweep_mapping = {}
        r = radius_range[0]
        while r <= radius_range[1]:
            gds_path = os.path.join(self.gds_dir,"Waveguide_r={}nm.gds".format(int(r*1000)))
            self.radius_sweep_mapping[gds_path] = r
            
            length = r + self.bend_to_straight_margin
            generate_gds_from_pcell(gds_path, self.techname, self.libname, self.pcellname,
                                    params = {"path": [[0,0],[length,0], [length,length]],
                                              "radius": r, "widths": [width],"adiab": 0})

            r = r + resolution
            
        return self.radius_sweep_mapping
            
    def sweep_bezier(self, width, radius, bezier_range, resolution):
        ''' Generate GDS sweep of radii given a resolution
        
        Sweep radii give the resolution and get as close as possible to the end radius
        range.
        
        Command line commands that work:
        #C:\\klayout-0.26.6-win64\\klayout_app.exe -b -r C:\\Users\\seanl\\KLayout\\pymacros\\test_python_cmd_line.py -rd bob="hello world"                 
        #C:\\klayout-0.26.6-win64\\klayout_app.exe -r "C:\\Users\\seanl\\Documents\\01_UBC\\Academics\\Grad School\\01_Work\\PDK-Generator\\Repo\\PDK-Generator\\python\\lumgen\\create_gds_klayout.py" -rd techname="EBeam" -rd libname="EBeam" -rd pcellname="Waveguide" -rd out_dir="C:\\Users\\seanl\\Downloads\\test7.gds" -rd params="{\\"radius\\": 2}"

        Parameters
        ----------
        width : float
            Waveguide width (um)
        radius : float
            Waveguide bend radius (um)
        bezier_range : list of floats (Size of 2)
            First entry is the minimum bezier param, second entry is the max bezier param.
        resolution : float
            Increment size between each bezier value.

        Returns
        -------
        self.bezier_sweep_mapping : dict
            Keys = GDS file location, Vals = bezier param 

        '''
        
        print("Create waveguide GDS sweeping bezier param")
        print("Running KLayout in command line...")
        print("NOTE: If you copy and paste the following commands into cmd line, ensure quotations are around file paths so that spaces are captured\n")
        
        if self.klayout_app_path == None:
            self.klayout_app_path = get_klayout_app_path()
        
        self.bezier_sweep_mapping = {}
        length = radius + self.bend_to_straight_margin
        b = bezier_range[0]
        while b <= bezier_range[1]:
            gds_path = os.path.join(self.gds_dir,"Waveguide_b={}_r={}nm.gds".format(b, int(radius*1000)))
            self.bezier_sweep_mapping[gds_path] = b
                       
            generate_gds_from_pcell(gds_path, self.techname, self.libname, self.pcellname,
                                    params = {"path": [[0,0],[length,0], [length,length]],
                                              "radius": radius, "widths": [width], "bezier": b, "adiab": 1})
            
            b = b + resolution
            
        return self.bezier_sweep_mapping

    def sweep_bezier_and_radius(self, width, radius_list, bezier_range, resolution):
        self.bezier_radius_sweep_mapping = {}
        for radius in radius_list:
            self.bezier_radius_sweep_mapping[radius] = self.sweep_bezier(width, radius, bezier_range, resolution)
        
        return self.bezier_radius_sweep_mapping
    
    def create_geometry_dirs(self):
        # define paths
        self.gds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gds")
        
        # create dirs if not available
        if not os.path.isdir(self.gds_dir):
            os.mkdir(self.gds_dir)

if __name__ == "__main__":
    # Test 1: Generate raw GDS and generate geometry in Lumerical
    # gds_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),r"design_automation\Waveguide\Waveguide_w=100nm.gds")
    # design_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),r"design_automation\Waveguide\Waveguide_design.yml")
    # process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),"yaml_processes","SiEPICfab-Grouse-Base.lbr")
    # mode = lumapi.MODE(hide = False)
    # WGS = WaveguideStripGeometry(design_file, process_file, mode)
    # generate_lum_geometry(mode, process_file, gds_file)
    
    # Test 2: Generate PCell GDS sweeping radius
    gds_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"gds","Waveguide_r=1000nm.gds")
    design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
    process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),"yaml_processes","SiEPICfab-Grouse-Base.lbr")
    
    fdtd = lumapi.FDTD(hide = False)
    WGS1 = WaveguideStripGeometry(design_file, process_file, fdtd)
    WGS1.sweep_radius(0.5,[1,2],1)
    generate_lum_geometry(fdtd, process_file, gds_file)
    
    # Test 3: Generate PCell GDS sweeping bezier
    # gds_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_r=1000nm.gds")
    # design_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),r"design_automation\Waveguide\Waveguide_design.yml")
    # process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),"yaml_processes","SiEPICfab-Grouse-Base.lbr")
    
    # WGS1 = WaveguideStripGeometry(design_file, process_file)
    # WGS1.sweep_bezier(0.5, 5, [0.1,0.2],0.1)

