"""
Create Lumerical Process File (.lbr)
"""

# Set up path to modules. PDK-Generator/python needs to be in sys.path
import sys, os
proj_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if proj_path not in sys.path:
    sys.path.append(proj_path)

from common.lumerical_lumapi import lumapi
from common.common_methods import prettify
from xml.etree.ElementTree import Element, SubElement, Comment
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox,\
QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog
from PyQt5.QtGui import QFont
from lumgen import get_process_layer_sources, LayerMappingDialog
import yaml
import xml.etree.ElementTree as ET

class LumericalLayerStack():
    
    def __init__(self, process_yaml_file_path):
        self.get_layer_params(process_yaml_file_path)
        self.create_lbr_file()
    
    def get_layer_params(self, process_yaml_file_path):
        """Get layer info from Process YAML and save to instance vars 
        
        Parses Process YAML for layer info pertinent to Lumerical Layer Builder.
        
        Parameters
        ----------
        process_yaml_file_path : str
            Absolute file path for the Process YAML.

        Returns
        -------
        None.

        """
        try:
            with open(process_yaml_file_path) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain layer formatting... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain layer formatting... Passing...")
            return
        except TypeError:
            if type(process_yaml_file_path) == tuple:
                process_yaml_file_path = process_yaml_file_path[0]
            with open(process_yaml_file_path) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
                
        self.process_name = data['technology']['name']
        self.data = data['layers']
        self.layer_stack = []
        
        if data['units'] == 'um':
            scale_factor = 1e-6
            
        # Map process layer to waveguide layer and ports for simulation
        process_layer_sources = get_process_layer_sources(process_yaml_file_path)
        window = LayerMappingDialog(['Waveguide', 'Ports'], process_layer_sources)
        window.exec_()
        self.layer_mapping = window.layer_mapping
        self.port_layer_name = window.layer_mapping['Ports'].split(' - ')[0]
        self.waveguide_layer_name = window.layer_mapping['Waveguide'].split(' - ')[0]
        
        # Parse process file for layers and layer info
        # Save data as instance var
        for layer in data['layers']:
            if layer.get('lumerical-layer', False):
                self.layer_stack.append({'name': layer.get('name', ''),
                                    'source': layer.get('source', '').split('@')[0].replace('/',':'),
                                    'material': layer.get('material', ''),
                                    'thickness1': layer.get('grow-entire-layer', [0])[0]*scale_factor,
                                    'thickness2': layer.get('grow', [0])[0]*scale_factor,
                                    'thickness3': layer.get('etch', [0])[0]*scale_factor,
                                    'sidewall-angle': layer.get('sidewall-angle', 90),
                                    })
                
    def create_lbr_file(self):
        """Create XML string representing the .lbr process file for Lumerical
        
        Creates a string in XML format that represents the .lbr process file for
        Lumerical and saves it in instance var.

        Returns
        -------
        None.

        """
        
        layer_builder = Element('layer_builder')
        
        process_name = SubElement(layer_builder, "process_name")
        process_name.text = self.process_name
        
        # Set layer attributes
        # NOTE: Some default params used here. PDK Developer will need to change
        # the params in Lumerical to ensure layer stack is representative of process.
        layers = SubElement(layer_builder, 'layers')
        for layer in self.layer_stack:
            lay = SubElement(layers, 'layer')
            if layer['name'] == self.port_layer_name or layer['name'] == 'PinRec':
                wg_layer_ind = self.find_waveguide_layer()
                
                layer['name'] = 'Ports'
                lay.set('enabled', '0')
                
                if self.layer_stack[wg_layer_ind]['thickness1'] > 0:
                    lay.set('thickness', str(self.layer_stack[wg_layer_ind]['thickness1']))
                elif self.layer_stack[wg_layer_ind]['thickness2'] > 0:
                    lay.set('thickness', str(self.layer_stack[wg_layer_ind]['thickness2']))
                else:
                    lay.set('thickness', str(self.layer_stack[wg_layer_ind]['thickness3']))
            
            else:
                lay.set('enabled', '1')
                
                if layer['thickness1'] > 0:
                    lay.set('thickness', str(layer['thickness1']))
                elif layer['thickness2'] > 0:
                    lay.set('thickness', str(layer['thickness2']))
                else:
                    lay.set('thickness', str(layer['thickness3']))
            
            lay.set('pattern_alpha', '0.8')
            
            lay.set('material', '')
            lay.set('sidewall_angle', str(layer['sidewall-angle']))
            lay.set('start_position_auto', '0')
            lay.set('process', 'Grow')
            lay.set('background_alpha', '0.3')
            lay.set('start_position', '0')
            lay.set('pattern_negative', '0')
            lay.set('pattern_material', layer['material'])
            lay.set('layer_name', layer['source'])
            lay.set('pattern_material_index', '0')
            lay.set('pattern_growth_delta', '0')
            lay.set('material_index', '0')
            lay.set('name', layer['name'])
            lay.set('pattern_material_index', '0')
            

        self.lbr_file = prettify(layer_builder).split('\n',1)[-1]
        
    def find_waveguide_layer(self):
        """ Find waveguide layer index in list

        Returns
        -------
        i : int
            Index of the waveguide layer in the self.layer_stack list

        """
        for i in range(0, len(self.layer_stack)):
            if self.layer_stack[i]['name'] == self.waveguide_layer_name:
                return i
     
def generate_process_file():
    # Find YAML process files
    pdk_gen_root = os.path.dirname(os.path.abspath(__file__))
    while pdk_gen_root.split(os.sep)[-1] != 'PDK-Generator':
        print("Finding PDK Generator root path... Current Dir: {}".format(pdk_gen_root))
        pdk_gen_root = os.path.dirname(pdk_gen_root)
   
    yaml_process = QFileDialog().getOpenFileName(caption='Generate Lumerical Process File: Choose Process YAML',
                                                      directory=os.path.join(pdk_gen_root,'yaml_processes'),
                                                      options=QFileDialog.DontUseNativeDialog)
    
    # Get raw str path
    if type(yaml_process) == tuple:
        yaml_process = yaml_process[0]
    
    print(yaml_process)
    LLS = LumericalLayerStack(yaml_process)
    
    filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)),LLS.process_name+'.lbr')
    with open(filepath, 'w') as writer:
        writer.write(LLS.lbr_file)
    print("\nCreated .lbr file: "+filepath+"\n")
    print("Opening MODE...")
    print("CHECK PROCESS LAYER DEFINITION AND MATERIALS IN MODE AND EDIT IF NECESSARY:")
    print("1. On the left side under 'Objects Tree' --> 'layer group', highlight 'layer group' and hit 'E' to edit the object")
    print("2. Import the process file (bottom left corner)")
    print("3. Check the process definition, especially thicknesses, starting points, and materials")
    print("4. Check the material fit parameters by opening the 'Material Database' window then navigating to 'Material Explorer'")
    print("ONCE CHECKED, PLEASE EXPORT AND SAVE THE PROCESS FILE FOR PDK USE")
    
    mode = lumapi.MODE(hide = False)
    mode.addlayerbuilder()
    mode.print("\nCreated .lbr file: "+filepath+"\n")
    mode.print("Opening MODE...")
    mode.print("CHECK PROCESS LAYER DEFINITION IN MODE AND EDIT IF NECESSARY:")
    mode.print("1. On the left side under 'Objects Tree' --> 'layer group', highlight 'layer group' and hit 'E' to edit the object")
    mode.print("2. Import the process file (bottom left corner)")
    mode.print("3. Check the process definition, especially thicknesses, starting points, and materials")
    mode.print("4. Check the material fit parameters by opening the 'Material Database' window then navigating to 'Material Explorer'")
    mode.print("ONCE CHECKED, PLEASE EXPORT AND SAVE THE PROCESS FILE FOR PDK USE")
    finish = input("Enter any key to continue...")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    generate_process_file()
    sys.exit(app.exec_())

