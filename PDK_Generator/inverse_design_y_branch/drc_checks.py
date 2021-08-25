import subprocess
import platform
import os
import xml.etree.ElementTree as ET

class DRCCheck():
    r"""Design Rule Check (DRC) class used to interface with KLayout's DRC engine
    
    Performs technology specific DRC on specified GDS file(s) through KLayout's
    DRC engine. KLayout runs in command line in batch mode.
    
    Attributes
    ----------
    klayout_folder_path : str
        Absolute path for KLayout folder
    klayout_app_path : str
        Absolute path for KLayout application executable
    drc_file_path : str
        Absolute path for DRC script (.lydrc)
        
    Examples
    --------
    The following shows how to use the DRCCheck class in simulation/optimization
    routines for a technology named 'Cheam' and a component called 'y_branch'
    
    >>> # Initial layout (base geometry with no optimizations) in 'C:\y_branch.gds'
    >>> tech_drc = DRCCheck()
    >>> continue_result = tech_drc.run_drc('Cheam', r'C:\y_branch.gds', 'y_branch')
    >>> if continue_result:
            # Perform optimizations/simulations
        else:
            # Exit to check design or rework design
            
    The above shows the first DRC check. Now, assume we continue into 
    simulations/optimizations. Then, we complete another DRC check:
    
    >>> # ROUND 1: Optimizations/simulations and GDS outputted in 'C:\y_branch1.gds'
    >>> continue_result = tech_drc.run_drc('Cheam', r'C:\y_branch1.gds', 'y_branch1')
    >>> if continue_result:
            # Perform further optimizations/simulations
        else:
            # Exit to check design or rework design
    
    We can continue further in another round of simulations/optimizations then
    DRC.
    
    >>> # ROUND 2: Optimizations/simulations and GDS outputted in 'C:\y_branch2.gds'
    >>> continue_result = tech_drc.run_drc('Cheam', r'C:\y_branch2.gds', 'y_branch2')
    >>> if continue_result:
            # Perform further optimizations/simulations
        else:
            # Exit to check design or rework design
    
    
    """
    
    
    def __init__(self):
        self.klayout_folder_path = get_klayout_folder_path()
        self.klayout_app_path = get_klayout_app_path()
        self.drc_file_path = ""

    def prompt_drc_check(self, num_errors):
        """Prompt user for input on whether to view layout with DRC results
        
        Parameters
        ----------
        num_errors : integer
            Number of errors resulting from a DRC check 

        Returns
        -------
        bool
            Returns True if user chooses to open KLayout and view DRC results by inputting Yes
            Returns False if user chooses to decline opening KLayout by inputting No

        """
        print("DRC completed with {} errors.\nOpen KLayout to view layout and DRC results?".format(num_errors))
        result = input("Enter 'Yes' or 'No': ")
        
        if result.lower() == 'yes' or result.lower() == 'y':
            return True
        else:
            return False
    
    def prompt_continue(self, num_errors):
        """Prompt user for input on whether to continue after DRC check
        
        Parameters
        ----------
        num_errors : integer
            Number of errors resulting from a DRC check 

        Returns
        -------
        bool
            Returns True if user chooses to continue by inputting Yes
            Returns False if user chooses to discontinue by inputting No

        """
        print("DRC completed with {} errors.\nAre you sure you want to continue?".format(num_errors))
        result = input("Enter 'Yes' or 'No': ")
        
        if result.lower() == 'yes' or result.lower() == 'y':
            return True
        else:
            return False

    def get_total_drc_errors(self, xml_file):
        """Get total DRC errors from XML formatted .lyrdb file
        
        Gets total number of DRC errors based on a database file (.lyrdb)

        Parameters
        ----------
        xml_file : string
             Path to XML formatted database file

        Returns
        -------
        integer
            Number of DRC Errors detected

        """
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        return len(list(root.iter('item')))
    
    def run_drc(self, techname, gds_filepath, component_name):
        """Run tech specific DRC on given GDS file
        
        Runs technology specific KLayout DRC on specified GDS file and
        saves DRC results in .lyrdb file in same location as GDS file.

        Parameters
        ----------
        techname : string
            Name of technology
        gds_filepath : string
            File path of GDS file
        component_name : string 
            Name of component the DRC is run upon

        Returns
        -------
        bool
            Returns True if user wants to continue
            Returns False if user wants to exit out to check design or error occurs

        """
        if not os.path.exists(gds_filepath):
            print("GDS file path {} does not exist... No DRC run...".format(gds_filepath))
            return False
        
        print("Finding {}_DRC.lydrc file...".format(techname))
        # Get path to DRC file if not available
        if not self.drc_file_path:
            for root, dirs, files in os.walk(self.klayout_folder_path):
                for file in files:
                    if file.endswith(".lydrc") and "{}_DRC".format(techname) in file:
                        print("KLAYOUT DRC FILE PATH:")
                        print(os.path.join(root, file) + "\n")
                        self.drc_file_path = os.path.join(root, file)
        else:
            print("KLAYOUT DRC FILE PATH:")
            print(self.drc_file_path + "\n")
        
        if self.drc_file_path:
            # Run DRC and save results
            print("Running KLayout in command line...")
            print("NOTE: If you copy and paste the following commands into cmd line, ensure quotations are around file paths so that spaces are captured\n")
            print("Running DRC on {}... Saving to {}...".format(os.path.split(gds_filepath)[-1], "{}_drc_results.lyrdb".format(component_name)))
            command = ["{}".format(self.klayout_app_path), "-b", "-r",
                       "{}".format(self.drc_file_path), "-rd", 
                       "in_gdsfile={}".format(gds_filepath), "-rd",
                       "out_drc_results={}_drc_results.lyrdb".format(component_name)]
            for cmd in command:
                print(cmd, end=" ")
            subprocess.run(command, shell=True)
            print("\nDRC Complete\n")
            
            drc_results_filepath = os.path.join(os.path.dirname(gds_filepath), "{}_drc_results.lyrdb".format(component_name))
            total_drc_errors = self.get_total_drc_errors(drc_results_filepath)
            continue_result = self.prompt_drc_check(total_drc_errors)
            
            if continue_result:
                # Open GDS file along with DRC results
                print("Opening GDS and DRC results...")
                command = ["{}".format(self.klayout_app_path),
                           "{}".format(gds_filepath), "-m",
                           "{}".format(os.path.join(os.path.dirname(gds_filepath), "{}_drc_results.lyrdb".format(component_name)))]
                for cmd in command:
                    print(cmd, end=" ")
                subprocess.run(command, shell=True)
                print("\nOpened GDS and showing results\n")
            
            # Ask user whether to continue
            continue_result = self.prompt_continue(total_drc_errors)
            if continue_result:
                print("Continuing...")
            else:
                print("Exiting...")
            
            return continue_result
        else:
            print("Could not find DRC file...")
            return False
            

def get_klayout_app_path():
    """Get KLayout application executable path
    
    Searches for KLayout application executable path locally (may take some time)

    Returns
    -------
    string
        Path for KLayout application executable

    """
    print("Finding KLayout application...")
    system = platform.system()
    if system == 'Windows':
        for root, dirs, files in os.walk("C:"+os.sep):
            for file in files:
                if file.endswith(".exe") and "klayout_app" in file:
                    print("KLAYOUT APPLICATION PATH:")
                    print(os.path.join(root, file) + "\n")
                    return os.path.join(root, file)
    elif system == "Darwin":
        location = os.popen("find /Applications -name klayout.app").read()
        if location:
            print("KLAYOUT APPLICATION LOCATION:")
            print(location  + "\n")
            return location
    print("Could not find KLayout app...\n")


def get_klayout_folder_path():
    """Get KLayout folder path
    
    Searches for KLayout folder path locally (may take some time)

    Returns
    -------
    string
        Path for KLayout folder

    """
    print("Finding KLayout folder...")
    system = platform.system()
    if system == 'Windows':
        for root, dirs, files in os.walk("C:"+os.sep+"Users"):
            for file in files:
                if root.split(os.sep)[-1] == "KLayout" and file == "klayoutrc":
                    print("KLAYOUT FOLDER:")
                    print(root + "\n")
                    return root
            
    elif system == "Darwin":
        for root, dirs, files in os.walk("/Users"):
            if root.split(os.sep)[-1] == ".klayout":
                print("KLAYOUT FOLDER:")
                print(root + "\n")
                return root
    print("Could not find KLayout folder...\n")
                
              
def open_klayout(klayout_app_path=None, filepath=None):
    """Open KLayout application
    
    If filepath to GDS file is specified, opens the GDS file in KLayout

    Parameters
    ----------
    klayout_app_path : string, optional
        Filepath of the Klayout application. The default is None.
    filepath : string, optional
        Filepath of the GDS file. The default is None.

    Returns
    -------
    None.

    """
    if not klayout_app_path:
        klayout_app_path = get_klayout_app_path()
    
    if filepath:
        print("Opening {} in KLayout...".format(filepath))
        subprocess.Popen([klayout_app_path, filepath])
    else:
        print("Opening KLayout...")
        subprocess.Popen(klayout_app_path)
    print("KLayout opened...")

    
def export_gds(lum_app, filename, top_cell_name, layer_def,
               n_circle = 64, n_ring = 64, n_custom = 64, n_wg = 64,
               round_to_nm = 1, grid = 1e-9, max_objects = 10000):
    """Export layout in Lumerical application to GDS II
    
    Lumerical_GDS_auto_export.lsfx must be present and 
    in the same working directory as the Lumerical application

    Parameters
    ----------
    lum_app : lumapi.FDTD() or lumapi.MODE()
        Lumerical application object from Lumerical's python API
    filename : string
        Name of GDS file (i.e. 'y_branch')
    top_cell_name : string
        Name of top cell in GDS file (i.e. 'model')
    layer_def : list of int
        A list of layer definitions defined as:
            [layer_number0, layer_datatype0, z_min0, z_max0,
            layer_number1, layer_datatype1, z_min1, z_max1,
            layer_number2, layer_datatype2, z_min2, z_max2,
            ...          , ...                    , ...   ]
    n_circle : integer, optional
        number of sides to use for circle approximation. The default is 64.
    n_ring : integer, optional
        number of slices to use for ring approximation. The default is 64.
    n_custom : integer, optional
        number of slices to use for custom approximation. The default is 64.
    n_wg : integer, optional
        number of slices to use for waveguide approximation. The default is 64.
    round_to_nm : integer, optional
        round the z and z span to the nearest integer of nm. The default is 1.
    grid : double, optional
        snap to grid. The default is 1e-9.
    max_objects : integer, optional
        the maximum number of objects within the workspace (Increasing this will increase export time). The default is 10000.

    Returns
    -------
    string
        File path of GDS file generated

    """
    
    print("Exporting from Lumerical application to GDS II...")
    layer_def_str = "layer_def = ["
    for i in range(0,len(layer_def)):
        if i == (len(layer_def) - 1):
            # Insert end bracket and semi-colon at end of array
            layer_def_str = layer_def_str + str(layer_def[i]) + "];"
        elif (i + 1) % 4 == 0:
            # Insert semi-colon after every 4 params
            layer_def_str = layer_def_str + str(layer_def[i]) + ";"
        else:
            layer_def_str = layer_def_str + str(layer_def[i]) + ","
       
    lsf_script = str("gds_filename = '{}.gds';".format(filename) +
                     "top_cell = '{}';".format(top_cell_name) +
                     layer_def_str.format(-220.0e-9/2, 220.0e-9/2) +
                     "n_circle = {};".format(n_circle) +
                     "n_ring = {};".format(n_ring) +
                     "n_custom = {};".format(n_custom) +
                     "n_wg = {};".format(n_wg) +
                     "round_to_nm = {};".format(round_to_nm) +
                     "grid = {};".format(grid) +
                     "max_objects = {};".format(max_objects) +
                     "Lumerical_GDS_auto_export;")
    #return lsf_script
    # Run lsf script to export gds
    lum_app.cd(os.getcwd())
    lum_app.eval(lsf_script)
    return os.path.join(os.getcwd(), filename+".gds")
