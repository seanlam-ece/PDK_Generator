"""
Lumerical Generation

Prepares config files, runs design recipes, and compiles CML


"""

# Set up path to modules. PDK-Generator/python needs to be in sys.path
import sys, os
proj_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if proj_path not in sys.path:
    sys.path.append(proj_path)
    
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox,\
QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog
from PyQt5.QtGui import QFont

from techgen.laystack import LayerStack
from techgen.tech import Technology
from importlib import import_module
from cml_compiler.cml_compiler_helper import CMLCompilerHelper

import yaml
import xml.etree.ElementTree as ET

class LayerMappingDialog(QDialog):
    r"""A window for mapping Component layers and Process layers
    
    Parameters
    ----------
    component_layer_names : list of str
        List of component layer tags/names
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
    component_category : pya.QLabel
        QLabel used to make the component layers column
    process_category : pya.QLabel
        QLabel used to make the process layers column
    component_layer : pya.QLabel
        Temporary label to list the component layer tags
    component_combo_dict : dict
        Keys = component layer names/tags. Values = QComboBoxes with process layer
        names.
    layer_mapping : dict
        Keys = component layer names/tags. Values = Process layer names.
    button : pya.QDialogButtonBox
        'Ok' and 'Cancel' buttons.
        
    Examples
    --------
    The following shows how the LayerMappingDialog can be used to open a layer
    mapping window and receive input from the user to continue or exit.
    
    >>> component_layer_names = ['Waveguide', 'Metal', 'Text']
    >>> process_layer_sources = {'Si': '1:0', 'M1': '10:0', 'FloorPlan': '4:0',
                                  'Text': '5:0'}
    >>> destination = r'C:\Layer_Mapping'
    >>> LayerMapDialog = LayerMappingDialog(component_layer_names,
                                                  process_layer_sources,
                                                  destination)
    >>> if LayerMapDialog.exec_():
            print("User wants to continue. Dialog returned True")
        else:
            print("User wants to exit. Dialog returned False")
    
    """

    def __init__(self, component_layer_names, process_layer_sources, destination=None):
        # Initialize layer mapping to be populated by component layer names as keys
        # and process layer names as values
        self.destination = destination
        self.read_layer_mapping()
        
        super(LayerMappingDialog, self).__init__()
        component_layer_names.sort()
        
        self.setWindowTitle("Layer Mapping")
        self.resize(400, 120)
        self.groupBox = QGroupBox("Map process layers to component layers")
    
        layout = QGridLayout(self)
        self.setLayout(layout)
        
        # Set category titles
        font = QFont()
        font.setBold(True)
        self.component_category = QLabel("Component Layers", self)
        self.process_category = QLabel("Process Layers", self)
        self.component_category.setFont(font)
        self.process_category.setFont(font)
        layout.addWidget(self.component_category, 0, 0)
        layout.addWidget(self.process_category, 0, 1)
            
        # Add default empty string as choice in drop down menu
        process_layer_sources[''] = ''
        
        # Create labels associated to drop down menus
        self.component_combo_dict = {}
        for i in range(0, len(component_layer_names)):
            self.component_layer = QLabel(component_layer_names[i], self)
            layout.addWidget(self.component_layer, i+1, 0)
            # Create drop down menu
            self.component_combo_dict[component_layer_names[i]] = QComboBox()
            ind = 0
            for layer_name, source in process_layer_sources.items():
                self.component_combo_dict[component_layer_names[i]].addItem("{} - {}".format(layer_name, source))
                if self.layer_mapping.get(component_layer_names[i],'').split(' - ')[0] == layer_name:
                    self.component_combo_dict[component_layer_names[i]].setCurrentIndex(ind)
                ind += 1
            try:
                self.component_combo_dict[component_layer_names[i]].activated(self.update_component_to_process_layer_mapping)
            except:
                self.component_combo_dict[component_layer_names[i]].activated.connect(self.update_component_to_process_layer_mapping)
            layout.addWidget(self.component_combo_dict[component_layer_names[i]], i+1, 1)
            
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
        
    def update_component_to_process_layer_mapping(self):
        """Update component layer tag to Process layer mapping
        
        Returns
        -------
        None.

        """
        for component_layer, combo_box in self.component_combo_dict.items():
            if type(combo_box.currentText) != str:
                process_layer = combo_box.currentText()
            else:
                process_layer = str(combo_box.currentText)
            print("{}: {}".format(component_layer, process_layer))
            self.layer_mapping[component_layer] = process_layer
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
        for component_layer, combo_box in self.component_combo_dict.items():
            if type(combo_box.currentText) != str:
                process_layer = combo_box.currentText()
            else:
                process_layer = str(combo_box.currentText)
            print("{}: {}".format(component_layer, process_layer))
            self.layer_mapping[component_layer] = process_layer
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
                
def get_component_layer_names(path, component_list):
    """Get list of component layer names
    
    If path is folder, return all layer names in all component YAML files.
    If path is YAML file, return all layer names in component YAML files.
    Layer names are under a dict called 'layers'.
    
    Parameters
    ----------
    path : str
        Absolute path to folder or file.
    component_list: list
        List of components to find layer names for.

    Returns
    -------
    component_layer_names : list of str
        List of component layer names from component YAML files.

    """
    
    component_layer_names = []
    
    # If path is folder, get all layer names in all component YAML files
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if (file.endswith(".yaml") or file.endswith(".yml")) and file.split('.')[0] in component_list:
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        data = yaml.load(f, Loader=yaml.FullLoader)
                        layers = list(data.get('layers',{}).keys())
                        for layer in layers:
                            if layer not in component_layer_names:
                                component_layer_names.append(layer)
    elif os.path.isfile(path):
        if path.split("\\")[-1].split('/')[-1].split('.')[0] in component_list:
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                layers = list(data.get('layers',{}).keys())
                for layer in layers:
                    component_layer_names.append(layer)
    else:
        print("File path does not exist... Passing...")
    
    return component_layer_names


def get_process_layer_sources(process_path):
    
    process_layer_sources = {}
    if process_path.endswith(".lbr"):
        tree = ET.parse(process_path)
        all_layers = tree.findall('.//layer')
        
        for layer in all_layers:
            process_layer_sources[layer.attrib['name']] = layer.attrib['layer_name']
    elif process_path.endswith(".yaml") or process_path.endswith('.yml'):
        tech_LS = LayerStack(process_path)

        for layer_name, source in tech_LS.layer_sources.items():
            process_layer_sources[layer_name] = source.split('@')[0].replace('/',':')
    else:
        print("Unsupported file type... Returning...")
    return process_layer_sources

def replace_design_files(path, techname, layer_mapping, component_lib_list):
    
    design_automation_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))),'design_automation')
    
    # If path is folder, find all YAML files and replace 'layer' fields with layer def
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if (file.endswith(".yaml") or file.endswith(".yml")) and \
                        any(file.split('.')[0] in list(component_list) for component_list in component_lib_list.values()):
                    name = file.split('.')[0]
                    for libname, component_list in component_lib_list.items():
                        if name in component_list:
                            libname = libname
                            break
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        data = yaml.load(f, Loader=yaml.FullLoader)
                        data['techname'] = techname
                        data['libname'] = libname
                        if 'CML' in data['design-params'].keys():
                            data['design-params']['CML'] = techname
                        layers = list(data.get('layers',{}).keys())
                        for layer in layers:
                            if layer in layer_mapping:
                                data['layers'][layer] = layer_mapping[layer]
                    with open(os.path.join(design_automation_dir, name, name+"_design.yml"), 'w') as f:
                        yaml.dump(data,f)
                    
    elif os.path.isfile(path):
        name = path.split('\\')[-1].split('/')[-1].split('.')[0]
        for libname, component_list in component_lib_list.items():
            if name in component_list:
                libname = libname
                break
        if any(name in list(component_list) for component_list in component_lib_list.values()):
            with open(path, 'r') as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                data['techname'] = techname
                data['libname'] = libname
                if 'CML' in data['design-params'].keys():
                    data['design-params']['CML'] = techname
                layers = list(data.get('layers',{}).keys())
                for layer in layers:
                    if layer in layer_mapping:
                        data['layers'][layer] = layer_mapping[layer]
            with open(os.path.join(design_automation_dir, name, name+"_design.yml"), 'w') as f:
                yaml.dump(data,f)
    else:
        print("File path does not exist... Passing...")
 
def get_component_list(component_list_yaml):
    with open(component_list_yaml, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        component_list = []
        for sub_comp_list in data['components-to-compile'].values():
            for comp in sub_comp_list:
                component_list.append(comp)
    return component_list

def get_component_lib_list(component_list_yaml):
    with open(component_list_yaml, 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    return data['components-to-compile']

def get_techname(process_path):
    techname = ''
    if process_path.endswith('.yml') or process_path.endswith('.yaml'):
        T = Technology(process_path)
        techname = T.technology['technology']['name']
    return techname


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # File locations
    process_yaml_path = QFileDialog().getOpenFileName(caption='Generate Lumerical Designs: Select Process YAML', options=QFileDialog.DontUseNativeDialog)
    process_lbr_path = QFileDialog().getOpenFileName(caption='Generate Lumerical Designs: Select Process LBR', options=QFileDialog.DontUseNativeDialog)
    component_list_yaml = QFileDialog().getOpenFileName(caption='Generate Lumerical Designs: Select Component List YAML', options=QFileDialog.DontUseNativeDialog)
    
    if type(process_yaml_path) == tuple:
        process_yaml_path = process_yaml_path[0]
    if type(process_lbr_path) == tuple:
        process_lbr_path = process_lbr_path[0]
    if type(component_list_yaml) == tuple:
        component_list_yaml = component_list_yaml[0]
    
    designs_yaml_path = os.path.join(os.path.dirname(proj_path),'yaml_designs')
    
    # Get techname
    techname = get_techname(process_yaml_path)
    
    # Map layers
    process_layer_sources = get_process_layer_sources(process_lbr_path)
    component_list = get_component_list(component_list_yaml)
    component_layer_names = get_component_layer_names(designs_yaml_path, component_list)
    window = LayerMappingDialog(component_layer_names, process_layer_sources)
    window.exec_()
    
    # Replace yaml design files
    component_lib_list = get_component_lib_list(component_list_yaml)
    replace_design_files(designs_yaml_path, techname, window.layer_mapping, component_lib_list)
    
    # Import design automation files then
    # Run design process or create compact models
    design_or_compile = input("(1) Run design process\n(2) Create compact models\nSelect number:\n")
    show_sim = input("Show simulation window(s)? y/n\n")
    if show_sim == 'y':
        hide = False
    else:
        hide = True
    cml_model_mapping = {}
    cml_model_list = []
    for component in component_list:
        component_dir = os.path.join(proj_path, "design_automation", component)
        if component_dir not in sys.path:
            sys.path.append(component_dir)
        
        mod = import_module("design_automation.{name}.{name}_main".format(name=component))
        if design_or_compile == '2':
            compact_modelling = mod.create_compact_model(process_lbr_path, hide)
        elif design_or_compile == '1':
            compact_modelling = mod.run_design_process(process_lbr_path, hide)
        
        # Handles compact models mapped to photonic models
        if type(compact_modelling) == dict:
            for cm_path, p_model in compact_modelling.items():
                cml_model_mapping[cm_path] = p_model
        # Handles pre-generated compact model (.ice) files
        elif type(compact_modelling) == str:
            cml_model_list.apppend(compact_modelling)
 
    # Generate and update compact model files
    CCH = CMLCompilerHelper()
    CCH.update_cml_with_new_models(techname, cml_model_mapping)
    CCH.update_cml_with_new_models(techname, cml_model_list)

    print("Done LUMGEN...")
    sys.exit(app.exec_())
