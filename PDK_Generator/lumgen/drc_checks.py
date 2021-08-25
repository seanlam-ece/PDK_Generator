from common.common_methods import get_klayout_app_path, get_klayout_folder_path
from datetime import datetime
import subprocess
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
        
        # Create folder to save DRC results
        self.drc_results_dir = os.path.join(os.path.dirname(gds_filepath), 'drc_results')
        if not os.path.isdir(self.drc_results_dir):
            os.mkdir(self.drc_results_dir)
        
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
            now = datetime.now()
            out_file_name = now.strftime("%Y-%m-%d-%H%M-")+component_name+"_drc_results.lyrdb"
            command = ["{}".format(self.klayout_app_path), "-b", "-r",
                       "{}".format(self.drc_file_path), "-rd", 
                       "in_gdsfile={}".format(gds_filepath), "-rd",
                       "out_drc_results={}".format(os.path.join(self.drc_results_dir, out_file_name))]
            for cmd in command:
                print(cmd, end=" ")
            subprocess.run(command, shell=True)
            print("\nDRC Complete\n")
            
            drc_results_filepath = os.path.join(self.drc_results_dir, out_file_name)
            total_drc_errors = self.get_total_drc_errors(drc_results_filepath)
            continue_result = self.prompt_drc_check(total_drc_errors)
            
            if continue_result:
                # Open GDS file along with DRC results
                print("Opening GDS and DRC results...")
                command = ["{}".format(self.klayout_app_path),
                           "{}".format(gds_filepath), "-m",
                           "{}".format(os.path.join(os.path.dirname(gds_filepath), drc_results_filepath))]
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
            



