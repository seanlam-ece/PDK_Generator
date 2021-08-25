import sys, os
try:
    import pya
    from pya import QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog, QFont, QMessageBox
except:
    from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox,\
    QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog
    from PyQt5.QtGui import QFont
    
import yaml
from common.common_methods import convert_to_macro
from laystack import LayerStack

def generate_library(techname, tech_folder):
    r"""Main LIBGEN function used to generate cell libraries given a technology
    
    This function runs in KLayout's python interpreter since it relies on KLayout's
    pya module and its Qt binding.
    
    Generates:
    1. .lym script that is set to autorun to instantiate libraries
    2. .py library script that registers PCells and fixed cells
    3. dev and mature folders for PCells (.py) and fixed cells (.gds/.oas)
    4. README.md files to start the dev and mature cell folders
    
    Parameters
    ----------
    techname : str
        Technology name.
    tech_folder : str
        Technology base path.

    Returns
    -------
    None.
    
    Examples
    --------
    The following shows how to generate cell libraries for a technology that has 
    already been generated. Assuming Cheam is a technology that has been
    generated in the base path r'C:\Cheam':
    
    >>> generate_library('Cheam', r'C:\Cheam')

    """
    
    print("Generating {} library...".format(techname))
    
    # Create warning about overwriting existing folders and files
    overwrite_msg = QMessageBox()
    overwrite_msg.setIcon(QMessageBox.Warning)
    reply = overwrite_msg.warning(overwrite_msg, 'LIBGEN OVERWRITE WARNING',"Continuing may overwrite existing folders and files."\
                                    " Are you sure you want to continue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
    if reply == QMessageBox.Yes:
        # Replace spaces or dashes with underscores
        orig_techname = techname
        function_techname = techname.replace(' ', '_').replace('-', '_')
        
        # Create library names
        dev_lib_name = orig_techname+"-Dev"
        mature_lib_name = orig_techname+"-Mature"
        
        # Create lym library instantiation file
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_instantiation_script_lym.txt")) as f:
            lym_code = f.read().replace('{orig_techname}', orig_techname).replace('{function_techname}', function_techname)
        
        macro_dict = {
                        'category': 'pymacros',
                        'autorun': 'true',
                        'autorun-early': 'false',
                        'show-in-menu': 'false',
                        'interpreter': 'python',
                        'text': lym_code
                    }
        
        lib_lym_file = convert_to_macro(macro_dict)
        try:
            with open(os.path.join(tech_folder, 'pymacros', '{}_Library.lym'.format(function_techname)), 'w') as f:
                f.write(lib_lym_file)
        except:
            if not os.path.isdir(os.path.join(tech_folder, 'pymacros')):
                os.mkdir(os.path.join(tech_folder, 'pymacros'))
                with open(os.path.join(tech_folder, 'pymacros', '{}_Library.lym'.format(function_techname)), 'w') as f:
                    f.write(lib_lym_file)
        print("Created {}_Library.lym...".format(function_techname))
        
        # Create py library instantiation file
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "library_instantiation_script_py.txt")) as f:
            lib_py_code = f.read().replace('{orig_techname}', orig_techname).replace('{function_techname}', function_techname)\
                                  .replace('{dev_lib_name}', dev_lib_name).replace('{mature_lib_name}', mature_lib_name)
            
        with open(os.path.join(tech_folder, 'pymacros', '{}_Library.py'.format(function_techname)), 'w') as f:
            f.write(lib_py_code)
        print("Created {}_Library.py...".format(function_techname))
        
        # Create fixed cell modules
        create_fixed_cell_modules(techname, tech_folder)
        
        # Create PCell modules
        create_pcell_modules(techname, tech_folder, dev_lib_name)
        
        libgen_complete = QMessageBox()
        libgen_complete.setWindowTitle("LibGen")
        libgen_complete.setText("{} library generated. \nLocation: {}".format(techname, tech_folder))
        
        print("Finished generating {} library...\n".format(orig_techname))
    else:
        libgen_complete = QMessageBox()
        libgen_complete.setWindowTitle("LibGen")
        libgen_complete.setText("No library generated.")
        
    libgen_complete.exec_()


class LayerSelectionDialog(QDialog):
    r"""A window for mapping PCell layers and Process layers
    
    Parameters
    ----------
    pcell_layer_names : list of str
        List of PCell layer tags/names
    process_layer_sources : dict
        Keys = Process layer name. Values = Process layer source
    destination : str, optional
        Absolute path to directory for saving/reading the layer mapping YAML. 
        Default is None.
        
    Attributes
    ----------
    destination : str
        Absolute path to directory for saving/reading the layer mapping YAML.
    groupBox : pya.QGroupBox
        Main QGroupBox to encapsulate the layer mapping QComboBoxes
    pcell_category : pya.QLabel
        QLabel used to make the PCell layers column
    process_category : pya.QLabel
        QLabel used to make the process layers column
    pcell_layer : pya.QLabel
        Temporary label to list the PCell layer tags
    pcell_combo_dict : dict
        Keys = PCell layer names/tags. Values = QComboBoxes with process layer
        names.
    layer_mapping : dict
        Keys = PCell layer names/tags. Values = Process layer names.
    button : pya.QDialogButtonBox
        'Ok' and 'Cancel' buttons.
        
    Examples
    --------
    The following shows how the LayerSelectionDialog can be used to open a layer
    mapping window and receive input from the user to continue or exit.
    
    >>> pcell_layer_names = ['Waveguide', 'Metal', 'Text']
    >>> process_layer_sources = {'Si': '1/0@1', 'M1': '10/0@1', 'FloorPlan': '4/0@1',
                                 'Text': '5/0@1'}
    >>> destination = r'C:\Layer_Mapping'
    >>> LayerMappingDialog = LayerSelectionDialog(pcell_layer_names,
                                                  process_layer_sources,
                                                  destination)
    >>> if LayerMappingDialog.exec_():
            print("User wants to continue. Dialog returned True")
        else:
            print("User wants to exit. Dialog returned False")
    
    """

    def __init__(self, pcell_layer_names, process_layer_sources, destination=None):
        # Initialize layer mapping to be populated by pcell layer names as keys
        # and process layer names as values
        self.destination = destination
        self.read_layer_mapping()
        
        super(LayerSelectionDialog, self).__init__()
        pcell_layer_names.sort()
        
        self.setWindowTitle("Layer Mapping")
        self.resize(400, 120)
        self.groupBox = QGroupBox("Map process layers to PCell layers")
    
        layout = QGridLayout(self)
        self.setLayout(layout)
        
        # Set category titles
        font = QFont()
        font.setBold(True)
        self.pcell_category = QLabel("PCell Layers", self)
        self.process_category = QLabel("Process Layers", self)
        self.pcell_category.setFont(font)
        self.process_category.setFont(font)
        layout.addWidget(self.pcell_category, 0, 0)
        layout.addWidget(self.process_category, 0, 1)
            
        # Add default empty string as choice in drop down menu
        process_layer_sources[''] = ''
        
        # Create labels associated to drop down menus
        self.pcell_combo_dict = {}
        for i in range(0, len(pcell_layer_names)):
            self.pcell_layer = QLabel(pcell_layer_names[i], self)
            layout.addWidget(self.pcell_layer, i+1, 0)
            # Create drop down menu
            self.pcell_combo_dict[pcell_layer_names[i]] = QComboBox()
            ind = 0
            for layer_name, source in process_layer_sources.items():
                self.pcell_combo_dict[pcell_layer_names[i]].addItem("{} - {}".format(layer_name, source))
                if self.layer_mapping.get(pcell_layer_names[i],'').split(' - ')[0] == layer_name:
                    self.pcell_combo_dict[pcell_layer_names[i]].setCurrentIndex(ind)
                ind += 1
            try:
                self.pcell_combo_dict[pcell_layer_names[i]].activated(self.update_pcell_to_process_layer_mapping)
            except:
                self.pcell_combo_dict[pcell_layer_names[i]].activated.connect(self.update_pcell_to_process_layer_mapping)
            layout.addWidget(self.pcell_combo_dict[pcell_layer_names[i]], i+1, 1)
            
        # Create group box around labels and drop down menus
        self.groupBox.setLayout(layout)
        vbox = QVBoxLayout()
        vbox.addWidget(self.groupBox)
        
        # Create OK and Cancel buttons
        try:
            self.button = QDialogButtonBox().new_buttons(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button.accepted(self.ok_clicked)
            self.button.rejected(self.cancel_clicked)
        except:
            self.button = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            self.button.accepted.connect(self.ok_clicked)
            self.button.rejected.connect(self.cancel_clicked)
               
        vbox.addWidget(self.button)
        self.setLayout(vbox)
        
    def update_pcell_to_process_layer_mapping(self):
        """Update PCell layer tag to Process layer mapping
        
        Returns
        -------
        None.

        """
        for pcell_layer, combo_box in self.pcell_combo_dict.items():
            if type(combo_box.currentText) != str:
                process_layer = combo_box.currentText()
            else:
                process_layer = str(combo_box.currentText)
            print("{}: {}".format(pcell_layer, process_layer))
            self.layer_mapping[pcell_layer] = process_layer
        print("")
        
    def ok_clicked(self):
        """Function handler for when user selects 'Ok'
        
        Updates layer mapping and saves layer mapping before exiting. Upon
        window closing, this function handler signals the window to return True.
        This can be used to signal whether a program continues further or stops.
        
        Returns
        -------
        None.

        """
        for pcell_layer, combo_box in self.pcell_combo_dict.items():
            if type(combo_box.currentText) != str:
                process_layer = combo_box.currentText()
            else:
                process_layer = str(combo_box.currentText)
            print("{}: {}".format(pcell_layer, process_layer))
            self.layer_mapping[pcell_layer] = process_layer
        self.save_layer_mapping()
        print("Closing window...\n")
        self.accept()
    
    def cancel_clicked(self):
        """Function handler for when user selects 'Cancel'
        
        Saves layer mapping before exiting. Upon window closing, this function 
        handler signals the window to return False. This can be used to signal 
        whether a program continues further or stops.
        
        Returns
        -------
        None.

        """
        self.save_layer_mapping()
        print("Closing window...\n")
        self.reject()
        
    def read_layer_mapping(self):
        """Read layer mapping from YAML file if it exists
        
        Returns
        -------
        None.

        """
        # Find layer_mapping.yml in current file directory or in destination
        matches = []
        for root, dirs, files in os.walk(os.path.dirname(os.path.realpath(__file__))):
            for file in files:
                if file == 'layer_mapping.yml':
                    matches.append(os.path.join(root,file))
        if self.destination:
            for root, dirs, files in os.walk(self.destination):
                for file in files:
                    if file == 'layer_mapping.yml':
                        matches.append(os.path.join(root,file))
                        
        # If layer_mapping found, load it else set layer mapping to empty
        if matches:
            with open(matches[0], 'r') as f:
                self.layer_mapping = yaml.load(f, Loader=yaml.FullLoader)
        else:
            self.layer_mapping = {}
            
        print("Layer Mapping:")
        print(self.layer_mapping)
                
    def save_layer_mapping(self):
        """Save layer mapping to YAML file
        
        Used to pull layer mapping for the next time when this window is reopened.
        
        Returns
        -------
        None.

        """
        try:
            with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),'layer_mapping.yml'), 'w') as f:
                yaml.dump(self.layer_mapping, f)
            print("Saved layer mapping to {}".format(os.path.dirname(os.path.realpath(__file__))))
        except:
            if self.destination:
                with open(os.path.join(self.destination,'layer_mapping.yml'), 'w') as f:
                    yaml.dump(self.layer_mapping, f)
                print("Saved layer mapping to {}".format(self.destination))
            else:
                print("Could not save layer mapping... Passing...")
            
    
def create_fixed_cell_modules(techname, tech_folder):
    """Create fixed cell GDS and OAS folders for given technology
    
    Creates GDS and OAS, mature and dev folders each with a README.md.
    
    Parameters
    ----------
    techname : str
        Technology name.
    tech_folder : str
        Absolute path of base technology folder.

    Returns
    -------
    None.

    """
    print("Creating fixed cell modules...")
    
    ############ Create GDS folder structure ############
    gds_folder = os.path.join(tech_folder, "gds")
    try:
        os.mkdir(gds_folder)
        print("Created GDS Folder...")
    except FileExistsError:
        print("GDS folder already exists...")
    
    # Create GDS dev folder
    gds_dev_folder = os.path.join(gds_folder, "dev")
    try:
        os.mkdir(gds_dev_folder)
        print("Created GDS Dev folder...")
    except FileExistsError:
        print("GDS Dev folder already exists...")
    
    # Create README for GDS dev folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixed_cell_readme.md")) as f:
        text = f.read().replace('{file_format}', 'GDS').replace('{lib_phase}', 'Dev').replace('{orig_techname}', techname)
    create_readme(text, gds_dev_folder)
    print("Created GDS Dev README...")
        
    # Create GDS mature folder
    gds_mature_folder = os.path.join(gds_folder, "mature")
    try:
        os.mkdir(gds_mature_folder)
        print("Created GDS Mature folder")
    except FileExistsError:
        print("GDS Mature folder already exists...")
    
    # Create README for GDS dev folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixed_cell_readme.md")) as f:
        text = f.read().replace('{file_format}', 'GDS').replace('{lib_phase}', 'Mature').replace('{orig_techname}', techname)      
    create_readme(text, gds_mature_folder)
    print("Created GDS Mature README...")
    
    ############ Create OAS folder structure ############
    oas_folder = os.path.join(tech_folder, "oas")
    try:
        os.mkdir(oas_folder)
        print("Created OAS Folder...")
    except FileExistsError:
        print("OAS folder already exists...")
    
    # Create OAS dev folder
    oas_dev_folder = os.path.join(oas_folder, "dev")
    try:
        os.mkdir(oas_dev_folder)
        print("Created OAS Dev folder...")
    except FileExistsError:
        print("OAS Dev folder already exists...")
    
    # Create README for OAS dev folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixed_cell_readme.md")) as f:
        text = f.read().replace('{file_format}', 'OAS').replace('{lib_phase}', 'Dev').replace('{orig_techname}', techname)
    create_readme(text, oas_dev_folder)
    print("Created OAS Dev README...")
        
    # Create OAS mature folder
    oas_mature_folder = os.path.join(oas_folder, "mature")
    try:
        os.mkdir(oas_mature_folder)
        print("Created OAS Mature folder")
    except FileExistsError:
        print("OAS Mature folder already exists...")
    
    # Create README for OAS dev folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixed_cell_readme.md")) as f:
        text = f.read().replace('{file_format}', 'OAS').replace('{lib_phase}', 'Mature').replace('{orig_techname}', techname)        
    create_readme(text, oas_mature_folder)
    print("Created OAS Mature README...")
    print("Finished creating fixed cell library...\n")

def create_pcell_modules(techname, tech_folder, libname):
    """Create PCell python module for given technology
    
    Creates mature and dev folders with __init__.py, README.md, and copied
    PCells with updated layer information, techname, libname, design params,
    and simulation params.
    
    Parameters
    ----------
    techname : str
        Technology name.
    tech_folder : str
        Absolute path of base technology folder.
    libname : str
        Library name.

    Returns
    -------
    None.

    """
    function_techname = techname.replace(' ', '_').replace('-', '_')
    
    ##### Create PCell dev folder #####
    pcells_dev_folder = os.path.join(tech_folder, "pymacros", function_techname+"_pcells_dev").replace("\\","/")
    try:
        os.mkdir(pcells_dev_folder)
        print("Created PCell Dev Folder...")
    except FileExistsError:
        print("PCell Dev folder already exists...")
    
    # Create README for PCell dev folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcell_readme.md")) as f:
        text = f.read().replace('{lib_phase}', 'Dev').replace('{orig_techname}', techname)
    create_readme(text, pcells_dev_folder)
    print("Created PCell Dev README...")
    
    # Copy PCells into dev folder
    copy_pcells(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pcells"), pcells_dev_folder, techname, libname)
    
    ##### Create PCell mature folder #####
    pcells_mature_folder = os.path.join(tech_folder, "pymacros", function_techname+"_pcells_mature")
    try:
        os.mkdir(pcells_mature_folder)
        print("Created PCell Mature Folder...")
    except FileExistsError:
        print("PCell Mature folder already exists...")
    
    # Create README for PCell mature folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcell_readme.md")) as f:
        text = f.read().replace('{lib_phase}', 'Mature').replace('{orig_techname}', techname)
    create_readme(text, pcells_mature_folder)
    print("Created PCell Mature README...")
    
    # Create __init__.py for PCell dev and mature modules
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pcell_module_instantiation.txt")) as f1:
        code = f1.read().replace('{orig_techname}', techname).replace('{function_techname}', function_techname)
        with open(os.path.join(pcells_dev_folder, "__init__.py"), 'w') as f2:
            f2.write(code)
        with open(os.path.join(pcells_mature_folder, "__init__.py"), 'w') as f3:
            f3.write(code)
        print("Created __init__.py for Dev and Mature PCell folders...")
        
    print("Finished creating PCell modules...\n")
        
def create_readme(text, folder):
    """Create README.md with given text in given folder
    
    Parameters
    ----------
    text : str
        Text inside the README.
    folder : str
        Absolute path of folder.

    Returns
    -------
    None.

    """
    with open(os.path.join(folder,"README.md"), 'w') as f:
        f.write(text)
 
def copy_pcells(source, destination, techname, libname):
    """Copy PCells from source to destination replacing tags with techname and libname
    
    Gets Process layer information and PCell layer tags and opens a window for
    the user to map Process layers to PCell layer tags. Each PCell is checked 
    against the layer mapping to see if the Process can support the PCell layers.
    Then, PCells that are supported by the Process are copied from source to
    destination with PCell tags replaced by techname, libname, layer names, design
    params, and simulation params
    
    Parameters
    ----------
    source : str
        Absolute path of soure directory where original PCell scripts live.
    destination : str
        Absolute path of destination directory.
    techname : str
        Technology name.
    libname : str
        Library name.

    Returns
    -------
    None.

    """
    print("Copying PCells from {} to {}...".format(source, destination))
    
    # Get process layer sources
    YAMLFileDialog = QFileDialog()
    file_location = YAMLFileDialog.getOpenFileName(YAMLFileDialog, 'Generate Library: Open Process YAML File', "", "*.yaml *.yml")
    if file_location == "":
        print("No YAML file chosen... Cannot copy PCells... Passing...")
        return
    print(file_location)
    ProcessLayerStack = LayerStack(file_location)
    process_layer_sources = ProcessLayerStack.layer_sources
    
    # Get PCell layer names
    pcell_layer_names = get_pcell_layer_names(source)
    
    # Prompt user to map layers
    LayerMappingDialog = LayerSelectionDialog(pcell_layer_names, process_layer_sources, destination)
    if LayerMappingDialog.exec_():
        layer_mapping = LayerMappingDialog.layer_mapping
    else:
        print("Exited out of layer mapping... Cannot copy PCells... Passing...")
        msg = QMessageBox()
        msg.setWindowTitle("LibGen: Copying PCells...")
        msg.setText("No PCells copied.")
        msg.exec_()
        return
    
    # Copy PCell scripts suppported by process 
    for root, dirs, files in os.walk(source):
        for file in files:
            if check_pcell_layer_mapping(os.path.join(root, file), layer_mapping):
                pcell_name = file.split('.')[0]
                if os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(root)), 'yaml_designs', pcell_name + '.yml')):
                    params_yaml_path = os.path.join(os.path.dirname(os.path.dirname(root)), 'yaml_designs', pcell_name + '.yml')
                elif os.path.isfile(os.path.join(os.path.dirname(os.path.dirname(root)), 'yaml_designs', pcell_name + '.yaml')):
                    params_yaml_path = os.path.join(os.path.dirname(os.path.dirname(root)), 'yaml_designs', pcell_name + '.yaml')
                
                with open(os.path.join(root, file), 'r') as f1:
                    pcell_script = f1.read()
                    pcell_script = replace_pcell_layers(pcell_script, layer_mapping)
                    pcell_script = replace_pcell_params_from_yaml(pcell_script, params_yaml_path)
                    pcell_script = replace_pcell_techname(pcell_script, techname)
                    pcell_script = replace_pcell_libname(pcell_script, libname)
                    
                    # Copy WAVEGUIDES.xml to tech folder, PCells to destination
                    if file == "WAVEGUIDES.xml":
                        tech_folder = os.path.dirname(destination)
                        while tech_folder.split(os.sep)[-1].split('/')[-1] != techname:
                            tech_folder = os.path.dirname(tech_folder)
                        with open(os.path.join(tech_folder, file), 'w') as f2:
                            f2.write(pcell_script)
                    elif file == "chip_boundary.py":
                        pcell_script = pcell_script.replace('{dx}', str(ProcessLayerStack.chip_dx))
                        pcell_script = pcell_script.replace('{dy}', str(ProcessLayerStack.chip_dx))
                        with open(os.path.join(destination, file), 'w') as f2:
                            f2.write(pcell_script)
                    else:
                        with open(os.path.join(destination, file), 'w') as f2:
                            f2.write(pcell_script)

                print("Copied {}...".format(file))
        
    msg = QMessageBox()
    msg.setWindowTitle("LibGen: Copying PCells...")
    msg.setText("Copied PCells.")
    msg.exec_()



def get_pcell_layer_names(path):
    """Get list of PCell layer names
    
    If path is folder, return all layer names in all PCell scripts.
    If path is file, return all layer names in PCell script.
    
    Parameters
    ----------
    path : str
        Absolute path to folder or file.

    Returns
    -------
    pcell_layer_names : list of str
        List of PCell layer names from PCell script(s).

    """
    
    pcell_layer_names = []
    
    # If path is folder, get all layer names in all pcell scripts
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if (file.endswith(".py") or file.endswith(".xml")) and file != "PCELL_STRUCTURE.py":
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        code = f.read()
                        
                        # Find {Layer} tags
                        substring_len = len('{Layer}')
                        num_occurences = code.count('{Layer}')
                        tag_ind = 0
                        for occurence in range(1, num_occurences+1):
                            tag_ind = code.find('{Layer}', tag_ind) + substring_len
                            end_layer_tag_ind = code.find('}', tag_ind)
                            layer_name = code[tag_ind:end_layer_tag_ind]
                            if layer_name not in pcell_layer_names:
                                pcell_layer_names.append(layer_name)
    elif os.path.isfile(path):
        with open(path, 'r') as f:
            code = f.read()
            
            # Find {Layer} tags
            substring_len = len('{Layer}')
            num_occurences = code.count('{Layer}')
            tag_ind = 0
            for occurence in range(1, num_occurences+1):
                tag_ind = code.find('{Layer}', tag_ind) + substring_len
                end_layer_tag_ind = code.find('}', tag_ind)
                layer_name = code[tag_ind:end_layer_tag_ind]
                if layer_name not in pcell_layer_names:
                    pcell_layer_names.append(layer_name)
    else:
        print("File path does not exist... Passing...")
    
    return pcell_layer_names


def check_pcell_layer_mapping(pcell_file_path, layer_mapping):
    """Return True if all PCell layers are supported by layer mapping, else return False
    
    Parameters
    ----------
    pcell_file_path : str
        Absolute path to PCell script.
    layer_mapping : dict
        Mapping of layer tags from PCell scripts to process layers from Process
        YAML.

    Returns
    -------
    bool
        True = PCell layers are supported layer mapping. False = PCell layers
        not supported by layer mapping.

    """
    pcell_layer_names = get_pcell_layer_names(pcell_file_path)
    pcell_supported_layer_names = [layer_name for layer_name, value in layer_mapping.items() if value.split(' - ')[0] != '']

    if all(layer in pcell_supported_layer_names for layer in pcell_layer_names) and pcell_layer_names:
        return True
    else:
        return False


def replace_pcell_layers(pcell_script, layer_mapping):
    """Replace PCell layer tags with process layer names from layer mapping
    
    Parameters
    ----------
    pcell_script : str
        Python PCell script.
    layer_mapping : dict
        Mapping of layer tags from PCell scripts to process layers from Process
        YAML.

    Returns
    -------
    pcell_script : str
        PCell script with layer tags replaced by process layer names

    """
    
    # Find {Layer} tags
    substring_len = len('{Layer}')
    tag_ind = 0

    while pcell_script.find('{Layer}') != -1:
        start_layer_tag_ind = pcell_script.find('{Layer}', tag_ind) - 1
        tag_ind = pcell_script.find('{Layer}', tag_ind) + substring_len
        end_layer_tag_ind = pcell_script.find('}', tag_ind)
        entire_tag = pcell_script[start_layer_tag_ind:end_layer_tag_ind + 1]
        layer_name = pcell_script[tag_ind:end_layer_tag_ind]
        
        process_layer_name = layer_mapping.get(layer_name).split(' - ')[0]
        pcell_script = pcell_script.replace(entire_tag, process_layer_name)
    
    return pcell_script


def replace_pcell_params_from_yaml(pcell_script, params_yaml_path):
    """Replace PCell params from YAML file
    
    Parameters
    ----------
    pcell_script : str
        Python PCell script.
    params_yaml_path : str
        Absolute path of design params YAML.

    Returns
    -------
    pcell_script : str
        PCell script with tags replaced with params in YAML file

    """
    try:
        with open(params_yaml_path, 'r') as f:
            params_dict = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        print("YAML file does not exist... Cannot obtain design params... Passing...")
        return pcell_script
    except yaml.YAMLError:
        print("Error in YAML file... Cannot obtain design params... Passing...")
        return pcell_script
    
    design_params = params_dict.get('design-params')
    if design_params:
        for param_name, param_val in design_params.items():
            pcell_script = pcell_script.replace('{%s}' % param_name, str(param_val))
    
    simulation_params = params_dict.get('simulation-params')
    if simulation_params:
        for param_name, param_val in simulation_params.items():
            pcell_script = pcell_script.replace('{%s}' % param_name, str(param_val))
            
    compact_model_params = params_dict.get('compact-model')
    if compact_model_params:
        for param_name, param_val in compact_model_params.items():
            pcell_script = pcell_script.replace('{cm-%s}' % param_name, str(param_val))
        
    return pcell_script
    

def replace_pcell_techname(pcell_script, techname):
    """Replace {orig-techname} tag with original technology name
    
    Parameters
    ----------
    pcell_script : str
        Python PCell script.
    techname : str
        Technology name.

    Returns
    -------
    str
        PCell script with the {orig-techname} tag replaced by the technology name.

    """
    
    return pcell_script.replace('{orig-techname}', techname)


def replace_pcell_libname(pcell_script, libname):
    """Replace {libname} tag with library name
    
    Parameters
    ----------
    pcell_script : str
        Python PCell script.
    libname : str
        Library name.

    Returns
    -------
    str
        PCell script with the {libname} tag replaced by the library name.

    """
    return pcell_script.replace('{libname}', libname)


def libgen_window():
   app = QApplication(sys.argv)
   tech_dir = QFileDialog().getExistingDirectory(caption='Generate Library: Choose Technology Directory', options=QFileDialog.DontUseNativeDialog)
   print(tech_dir)
   generate_library(tech_dir.split("/")[-1], tech_dir)
   sys.exit(app.exec_())
   
if __name__ == "__main__":
    libgen_window()