import sys, os
try:
    import pya
    from pya import QWidget, QPushButton, QMessageBox, QFont,\
    QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog
except:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox,\
    QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog
    from PyQt5.QtGui import QFont
    
import yaml
from distutils.dir_util import copy_tree
from tech import Technology
from laystack import LayerStack
from drc import DRC
from xsection import XSection
from common.common_methods import convert_to_macro
from libgen import generate_library

def generate_technology():
    """Main TECHGEN function used to generate base PDK with tech files
    
    Returns
    -------
    None.

    """
    try:
        tech_gen_dialog = TechGenFileDialog(pya.Application.instance())
    except:
        tech_gen_dialog = TechGenFileDialog(QApplication.instance())
    
    tech_file_location = tech_gen_dialog.get_yaml_file_location()
    if type(tech_file_location) == tuple:
        tech_file_location = tech_file_location[0]
    
    if tech_file_location != "":
        
        # Create warning about overwriting existing tech files
        overwrite_msg = QMessageBox()
        overwrite_msg.setIcon(QMessageBox.Warning)
        reply = overwrite_msg.warning(overwrite_msg, 'TECHGEN OVERWRITE WARNING',"Continuing may overwrite existing technology files."\
                                        " Are you sure you want to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Get tech name if available
            with open(tech_file_location) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                tech_name = data.get('technology', {}).get('name', '')
            tech_gen_dialog.save_lyt_file_dialog(tech_name)
            
            # Create LayerStack object
            FoundryLayerStack = LayerStack(tech_file_location)
            FoundryLayerStack.create_lyp_file()
            tech_gen_dialog.save_lyp_file(FoundryLayerStack.lyp_file, tech_name)
            
            # Create DRC object
            FoundryDRC = DRC(tech_file_location)
            FoundryDRC.create_lydrc_file()
            FoundryDRC.create_drc_dict()
            tech_gen_dialog.save_lydrc_file(FoundryDRC.lydrc_file, tech_name)
            tech_gen_dialog.save_drc_yaml(FoundryDRC.drc_dict, tech_name)
            
            # Create XSection object
            FoundryXSection = XSection(tech_file_location)
            FoundryXSection.create_xs_file()
            tech_gen_dialog.save_xs_file(FoundryXSection.xs_file, tech_name)
            
            tech_complete = QMessageBox()
            tech_complete.setWindowTitle("TechGen")
            if tech_gen_dialog.tech_folder_location != "":
                tech_complete.setText(tech_gen_dialog.tech_name + " technology generated. \nLocation: " + tech_gen_dialog.tech_folder_location)
                # Show message box
                tech_complete.exec_()
                
                generate_library(tech_gen_dialog.tech_name, tech_gen_dialog.tech_folder_location.replace('/', os.sep))
            else:
                if tech_gen_dialog.lyp_file_location != "" or tech_gen_dialog.lydrc_file_location != ""\
                or tech_gen_dialog.xs_file_location != "" or tech_gen_dialog.pymacro_file_location != ""\
                or tech_gen_dialog.drc_yaml_file_location != "":
                    text = "Generated the following files...\n\n"\
                            "Layer Formatting (.lyp):\n{}\n\n"\
                            "DRC Macro (.lydrc):\n{}\n\n"\
                            "DRC YAML (.yaml):\n{}\n\n"\
                            "XSection Script(s) (.xs):\n{}\n\n"\
                            "Keybinding(s) (.lym):\n{}"
                    tech_complete.setText(text.format(tech_gen_dialog.lyp_file_location,
                                                      tech_gen_dialog.lydrc_file_location,
                                                      tech_gen_dialog.drc_yaml_file_location,
                                                      tech_gen_dialog.xs_file_location,
                                                      tech_gen_dialog.pymacro_file_location))
                else:
                    tech_complete.setText("No files generated.")
                
                # Show message box
                tech_complete.exec_()
            

class TechGenFileDialog(QFileDialog):
    r"""A file dialog for locating and saving technology files
    
    This runs in KLayout's python interpreter with its Qt binding.
    
    Generates the following files:
        1. Technology file (.lyt) 
        2. Layer properties file (.lyp) 
        3. DRC script (.lydrc) 
        4. DRC params (.yaml)
        5. XSection script (.xs) 
        6. XSection keybinding (.lym)
        7. tech_tools python scripts
    
    Generates the following folders:
        1. Technology base folder
        2. drc folder
        3. pymacros folder
        4. tech_tools folder
        
    Parameters
    ----------
    klayout_application_inst : Q.Application.instance()
        The KLayout application instance.
    
    Attributes
    ----------
    app_location : str
        Absolute path of KLayout application data folder. In Windows, this is
        usually 'C:\Users\<username>\KLayout'. In MacOS, this is usually located
        in a folder called '.klayout'.
    tech_folder_location : str
        Base path for generated technology files.
    lyt_file_location : str
        Absolute path for .lyt file.
    drc_yaml_file_location : str
        Absolute path for DRC YAML file.
    lyp_file_location : str
        Absolute path for .lyp file.
    lydrc_file_location : str
        Absolute path for .lydrc file.
    xs_file_location : str
        Absolute path for .xs file.
    pymacro_file_location : str
        Absolute path for .xs keybinding file.
    tech_name : str
        Technology name.
    
    """
    
    ## Initialize dialog and get KLayout application location
    def __init__(self, klayout_application_inst):
        # Set up dialog
        super(TechGenFileDialog, self).__init__()
        self.resize(1500, 1000)
        
        # Get KLayout application location and initialize base path (lyt location)
        try:
            self.app_location = klayout_application_inst.application_data_path()
        except:
            self.app_location = os.getcwd()
        self.tech_folder_location = ""
        
        # Initialize file locations
        self.lyt_file_location = ""
        self.drc_yaml_file_location = ""
        self.lyp_file_location = ""
        self.lydrc_file_location = ""
        self.xs_file_location = ""
        self.pymacro_file_location = ""
        self.tech_name = ""
    

    def get_yaml_file_location(self):
        """Get Process YAML absolute file path
        
        Opens a dialog box to locate the Process YAML.
        
        Returns
        -------
        str
            Absolute path of Process YAML.

        """
        file_location = self.getOpenFileName(self, 'Generate Technology: Open YAML File', "", "*.yaml *.yml")
        if file_location == "":
            print("No YAML file chosen... Passing...")
            return ""
        else:
            return file_location
    

    def save_lyt_file_dialog(self, tech_name):
        """Save Technology (.lyt) file
        
        Prompts the user for directory where the technology files will be generated.
        Ensures the generated tech folder matches with the technology file names
        (i.e. folder name 'Cheam' must be same as 'Cheam.lyt' file).
        
        Parameters
        ----------
        tech_name : str
            Technology name.

        Returns
        -------
        None.

        """
        # If tech_name is specified, prompt user for location, else prompt user for tech_name
        file_location = self.getExistingDirectory(self, 'Generate Technology: Save Technology File (.lyt)', self.app_location + "/tech")

        if file_location == "":
            file_name = ""
        elif tech_name == "":
            file_name = file_location + "/" + file_location.split('/')[-1] + ".lyt"
        elif tech_name != file_location.split('/')[-1]:
            select_techname = QMessageBox()
            select_techname.setIcon(QMessageBox.Warning)
            reply = select_techname.warning(select_techname, 'TechGen: Select Technology Name',"Location: {tech_folder}\n"\
                                            "Tech folder name \"{folder}\" conflicts with tech name \"{file}\".\n"\
                                            "Select Yes to continue with \"{folder}\" as tech name.\n"\
                                            "Select No to continue with \"{file}\" as tech name.".format(tech_folder=file_location,folder=file_location.split('/')[-1], file=tech_name),
                                            QMessageBox.Yes | QMessageBox.No)
                
            if reply == QMessageBox.Yes:
                tech_name = file_location.split('/')[-1]
            else:
                os.rename(file_location, os.path.dirname(file_location) + "/" + tech_name)
                file_location = os.path.dirname(file_location) + "/" + tech_name
                
            file_name = file_location + "/" + tech_name + ".lyt"
        elif tech_name == file_location.split('/')[-1]:
            file_name = file_location + "/" + tech_name + ".lyt"
        else:
            file_name = ""
        
        # If user exits by either cancelling or closing window, print error message and pass
        if file_name == "":
            print("No .lyt file name entered... Passing...")
        else:
            # Save folder and file location of .lyt file
            self.tech_folder_location = os.path.abspath(os.path.join(file_name, os.pardir)).replace(os.sep, '/')
            self.lyt_file_location = file_name.replace(os.sep, '/')
            self.tech_name = self.lyt_file_location.split('/')[-1].split('.')[0]
            
            # Set technology params and create lyt file
            FoundryTech = Technology()
            FoundryTech.technology['technology']['name'] = self.tech_name
            FoundryTech.technology['technology']['original-base-path'] = self.tech_folder_location.replace('/', "\\")
            FoundryTech.technology['technology']['layer-properties_file'] = self.tech_name + ".lyp"
            FoundryTech.technology['technology']['writer-options']['gds2']['libname'] = self.tech_name + "_Library"
            FoundryTech.create_lyt_file()
            
            # Create .lyt file
            with open(file_name, 'w') as f:
                f.write(FoundryTech.lyt_file)
                

    def save_lyp_file(self, lyp_file, file_name=""):
        """Save Layer Properties (.lyp) file
        
        If tech folder was created, the .lyp file is saved in the technology
        base folder.
        
        If tech folder was not created, a file dialog window prompts the user
        for the location and perhaps the file name.
        
        Parameters
        ----------
        lyp_file : str
            String representing the XML formatted layer properties (.lyp) file.
        file_name : str, optional
            Name of .lyp file. The default is "".

        Returns
        -------
        None.

        """
        if self.tech_folder_location != "":
            
            # Create file path
            file_name = self.tech_folder_location + '/' + self.tech_name + ".lyp"
            # Save .lyp file location
            self.lyp_file_location = file_name.replace(os.sep, '/')
            
            # Create lyp file
            with open(file_name, 'w') as f:
                f.write(lyp_file)
                
        else:
            # Ensure file_name does not have the .lyp extension
            file_name = file_name.split('.')[0]
            
            # If file_name is specified, prompt user for folder location, else prompt user for file_name
            if file_name == "":
                file_name = self.getSaveFileName(self, 'Generate Technology: Save Layer Formatting File (.lyp)', self.app_location + "/tech", "*.lyp")
            else:
                file_location = self.getExistingDirectory(self, 'Generate Technology: Save Layer Formatting File (.lyp)', self.app_location + "/tech")
                # If the user cancels out of the window, file_location will be an empty string
                if file_location != "":
                    file_name = file_location + "/" + file_name + ".lyp"
                else:
                    file_name = ""
                            
            # If user exits by either cancelling or closing window, print error message and pass
            if file_name == "":
                print("No .lyp file name entered... Passing...")
            else:
                # Save .lyp file location
                self.lyp_file_location = file_name.replace(os.sep, '/')
                # Create .lyp file
                with open(file_name, 'w') as f:
                    f.write(lyp_file)
                

    def save_lydrc_file(self, lydrc_file, file_name=""):
        """Save DRC script (.lydrc) script
        
        If tech folder was created, the .lydrc script is saved in the 'drc' folder
        of the generated technology with a '_DRC' tag in the file name.
        
        If tech folder was not created, a file dialog window prompts the user
        for the location and perhaps the file name.
        
        Parameters
        ----------
        lydrc_file : str
            String representing the .lydrc script.
        file_name : str, optional
            Name of .lydrc file. The default is "".

        Returns
        -------
        None.

        """
        
        if self.tech_folder_location != "":
            # Create drc folder
            if not os.path.isdir(self.tech_folder_location + "/drc"):
                os.makedirs(self.tech_folder_location + '/drc')
            
            # Use tech name
            file_name = self.tech_folder_location + "/drc/" + self.tech_name + "_DRC" + ".lydrc"
            
            # Save .lydrc file location
            self.lydrc_file_location = file_name.replace(os.sep, '/')
            # Create .lydrc file
            with open(file_name, 'w') as f:
                f.write(lydrc_file)
                    
        else:
            # Ensure file_name does not have the .lydrc extension
            file_name = file_name.split('.')[0]
            
            if file_name == "":
                file_name = self.getSaveFileName(self, 'Generate Technology: Save DRC Macro File (.lydrc)', self.app_location + "/drc", "*.lydrc")
            else:
                file_location = self.getExistingDirectory(self, 'Generate Technology: Save DRC Macro File (.lydrc)', self.app_location + "/drc/" + file_name)
                # If the user cancels out of the window, file_location will be an empty string
                if file_location == "":
                    file_name = ""
                else:
                    file_name = file_location + "/" + file_name + "_DRC" + ".lydrc"
                
            if file_name == "":
                print("No .lydrc file name entered... Passing...")
            else:
                # Save .lydrc file location
                self.lydrc_file_location = file_name.replace(os.sep, '/')
                # Create .lydrc file
                with open(file_name, 'w') as f:
                    f.write(lydrc_file)
                   
                    
    def save_drc_yaml(self, drc_dict, file_name = ""):
        """Save DRC params to YAML file
        
        If tech folder was created, the DRC YAML is saved in the tech base path
        with a '_DRC' tag in the file name.
        
        If tech folder was not created, a file dialog window prompts the user
        for the location and perhaps the file name.

        Parameters
        ----------
        drc_dict : dict
            Keys = Process layer names. Values = DRC params.
        file_name : str, optional
            Name of DRC YAML file. The default is "".

        Returns
        -------
        None.

        """
        if self.tech_folder_location != "":
            # Use tech name
            file_name = self.tech_folder_location + "/" + self.tech_name + "_DRC" + ".yaml"
            
            # Save yaml file
            self.drc_yaml_file_location = file_name.replace(os.sep, '/')
            with open(file_name, 'w') as f:
                yaml.dump(drc_dict, f)
            self.save_tech_tools()
        else:
            if file_name == "":
                file_name = self.getSaveFileName(self, 'Generate Technology: Save DRC YAML File (.yaml)', self.app_location, "*.yaml *.yml")
            else:
                file_location = self.getExistingDirectory(self, 'Generate Technology: Save DRC YAML File (.yaml)', self.app_location)
                # If the user cancels out of the window, file_location will be an empty string
                if file_location == "":
                    file_name = ""
                else:
                    file_name = file_location + "/" + file_name + "_DRC" + ".yaml"
            
            if file_name == "":
                print("No .yaml file name entered... Passing...")
            else:
                # Save .yaml file
                self.drc_yaml_file_location = file_name.replace(os.sep, '/')
                with open(file_name, 'w') as f:
                    yaml.dump(drc_dict, f)
                self.save_tech_tools()
    

    def save_tech_tools(self):
        r"""Copy and rename python scripts in the tech_tools folder
        
        tech_tools folder is found in 'PDK_Generator\PDK_Generator\tech_tools'

        Returns
        -------
        None.

        """
        function_techname = self.tech_name.replace(' ', '_').replace('-', '_')
        src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tech_tools").replace('/', os.sep)
        dst = (self.tech_folder_location + "/pymacros/"+function_techname+"_tech_tools").replace('/', os.sep)
        copy_tree(src, dst)
        
        # Rename files
        try:
            os.rename(os.path.join(dst, '__init__py.py'), os.path.join(dst, '__init__.py'))
            os.rename(os.path.join(dst, 'drc_parser_py.py'), os.path.join(dst, 'drc_parser.py'))
            os.rename(os.path.join(dst, 'layout_functions_py.py'), os.path.join(dst, 'layout_functions.py'))
        except:
            os.remove(os.path.join(dst, '__init__.py'))
            os.remove(os.path.join(dst, 'drc_parser.py'))
            os.remove(os.path.join(dst, 'layout_functions.py'))
            
            os.rename(os.path.join(dst, '__init__py.py'), os.path.join(dst, '__init__.py'))
            os.rename(os.path.join(dst, 'drc_parser_py.py'), os.path.join(dst, 'drc_parser.py'))
            os.rename(os.path.join(dst, 'layout_functions_py.py'), os.path.join(dst, 'layout_functions.py'))
        
        # Replace relevant fields
        with open(self.tech_folder_location + "/pymacros/"+function_techname+"_tech_tools/drc_parser.py", 'r') as f:
            code = f.read().replace('{drc_yaml_file_name}', self.drc_yaml_file_location.split('/')[-1]).replace('{function_techname}', function_techname)
        with open(self.tech_folder_location + "/pymacros/"+function_techname+"_tech_tools/drc_parser.py", 'w') as f:
            f.write(code)
            
        with open(self.tech_folder_location + "/pymacros/"+function_techname+"_tech_tools/__init__.py", 'r') as f:
            code = f.read().replace('{orig_techname}', self.tech_name)
        with open(self.tech_folder_location + "/pymacros/"+function_techname+"_tech_tools/__init__.py", 'w') as f:
            f.write(code)
            

    def save_xs_file(self, xs_file, file_name=""):
        """Save XSection file (.xs)
        
        If tech folder was created, the xs file is saved in the tech base
        folder with the '_XSection' tag in the file name. 
        
        If tech folder was not created, a file dialog window prompts the user
        for the location and perhaps the file name.

        Parameters
        ----------
        xs_file : str
            String representing XSection script.
        file_name : str, optional
            Name of .xs file. The default is "".

        Returns
        -------
        None.

        """
        if self.tech_folder_location != "":

            # Use tech name
            file_name = self.tech_folder_location + "/" + self.tech_name + "_XSection.xs"
            
            # Save .xs file location
            self.xs_file_location = file_name.replace(os.sep, '/')
            # Create .xs file
            with open(file_name, 'w') as f:
                f.write(xs_file)
        else:
            # Ensure file_name does not have the .xs extension
            file_name = file_name.split('.')[0]
            
            if file_name == "":
                file_name = self.getSaveFileName(self, 'Generate Technology: Save XSection File (.xs)', self.app_location + "/pymacros", "*.xs")
            else:
                file_location = self.getExistingDirectory(self, 'Generate Technology: Save XSection File (.xs)', self.app_location + "/pymacros")
                # If the user cancels out of the window, file_location will be an empty string
                if file_location == "":
                    file_name = ""
                else:
                    file_name = file_location + "/" + file_name + ".xs"
            
            # If user exits by either cancelling or closing window, print error message and pass
            if file_name == "":
                print("No .xs file name entered... Passing...")
            else:
                # Save .xs file location
                self.xs_file_location = file_name.replace(os.sep, '/')
                # Create .xs file
                with open(file_name, 'w') as f:
                    f.write(xs_file)
            
        # If xs file was created, generate pymacro for keybinding
        if self.xs_file_location != "":
            macro_dict = {"text": "# Key Binding for SiEPIC XSection\n"\
                                  "include RBA\n"\
                                  "fn = File.join(File.expand_path(File.dirname(__FILE__)), \"../{}\")\n"\
                                  "print(fn)\n"\
                                  "$xsection_processing_environment.run_script(fn)".format(self.xs_file_location.split('/')[-1]),
                          "description": "XSection - {} Process".format(self.tech_name),
                          "autorun": "false",
                          "autorun-early": "false",
                          "shortcut": "Shift+X",
                          "show-in-menu": "true",
                          "menu-path": "siepic_menu.layout.begin",
                          "interpreter": "ruby"}
            
            macro_file = convert_to_macro(macro_dict)
            self.save_macro_keybinding(macro_file, self.xs_file_location)
    

    def save_macro_keybinding(self, macro_file, file_name=""):
        """Save macro as a keybinding script so keyboard shortcuts can be used in KLayout
        
        If tech folder was created, the macro keybinding is saved in the pymacros
        folder with the '_KEYBIND' tag in the file name. This ensures that KLayout
        reads any macros defined in the pymacros folder. 
        
        If tech folder was not created, a file dialog window prompts the user
        for the location and perhaps the file name.
        
        Parameters
        ----------
        macro_file : str
            String representing the XML formatted macro, including all metadata.
        file_name : str, optional
            Name of file. The default is "".

        Returns
        -------
        None.

        """
        if self.tech_folder_location != "":
            # Create macros folder
            if not os.path.isdir(self.tech_folder_location + "/pymacros"):
                os.makedirs(self.tech_folder_location + '/pymacros')
            
            # If file_name not specified, use tech name, else use file_name
            if file_name == "":
                file_name = self.tech_folder_location + "/pymacros/" + self.tech_name + "_KEYBIND" + ".lym"
            else:
                file_name = self.tech_folder_location + "/pymacros/" + file_name.split('/')[-1].split('.')[0] + "_KEYBIND" + ".lym"
            
            # Save pymacro file location
            self.pymacro_file_location = file_name.replace(os.sep, '/')
            # Create pymacro file
            with open(file_name, 'w') as f:
                f.write(macro_file)
                    
        else:
            # Ensure file_name does not have the .lym extension and does not have the path
            file_name = file_name.split('/')[-1].split('.')[0]
            
            if file_name == "":
                file_name = self.getSaveFileName(self, 'Generate Technology: Save PyMacro (.lym)', self.app_location + "/pymacros", "*.lym")
            else:
                file_location = self.getExistingDirectory(self, 'Generate Technology: Save PyMacro (.lym)', self.app_location + "/pymacros")
                # If the user cancels out of the window, file_location will be an empty string
                if file_location == "":
                    file_name = ""
                else:
                    file_name = file_location + "/" + file_name + ".lym"
            
            if file_name == "":
                print("No .lym file name entered... Passing...")
            else:
                # Save .lydrc file location
                self.pymacro_file_location = file_name.replace(os.sep, '/')
                # Create .lydrc file
                with open(file_name, 'w') as f:
                    f.write(macro_file)

def techgen_window():
   app = QApplication(sys.argv)
   generate_technology()
   sys.exit(app.exec_())
   
if __name__ == "__main__":
    techgen_window()