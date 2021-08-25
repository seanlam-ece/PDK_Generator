from common.common_methods import prettify
import yaml
import xml.etree.ElementTree as ET

class LayerStack():
    r"""Class associated with layer properties
    
    A Process YAML is used to define layer properties and this class can create
    the .lyp (XML formatted) string necessary for KLayout's Layer Properties File
    (https://www.klayout.de/lyp_format.html) 
    
    Parameters
    ----------
    process_yaml_file_path : str
        Absolute file path for the Process YAML.
    
    Attributes
    ----------
    layer_properties : dict
        Layer properties dict used to generate the .lyp file. This dict has the
        following structure in YAML format:
            
            layer-properties:
                properties:
                    - 'name': "Waveguides"
                      'source': "*/*@*"
                      'frame-color': "#000000"
                      'fill-color': "#000000"
                      'frame-brightness': 0
                      'fill-brightness': 0
                      'dither-pattern': ''
                      'line-style': ''
                      'valid': 'true'
                      'visible': 'true'
                      'transparent': 'false'
                      'width': ''
                      'marked': 'false'
                      'xfill': 'false'
                      'animation': 0
                      'group-members':
                          - 'name': "Si"
                            'source': "1/0@1"
                            'frame-color': "#F00000"
                            'fill-color': "#F00000"
                            'frame-brightness': 0
                            'fill-brightness': 0
                            'dither-pattern': ''
                            'line-style': ''
                            'valid': 'true'
                            'visible': 'true'
                            'transparent': 'false'
                            'width': ''
                            'marked': 'false'
                            'xfill': 'false'
                            'animation': 0
                          - 'name': "Si_Slab"
                            'source': "2/0@1"
                            'frame-color': "#FF0000"
                            'fill-color': "#FF0000"
                            'frame-brightness': 0
                            'fill-brightness': 0
                            'dither-pattern': ''
                            'line-style': ''
                            'valid': 'true'
                            'visible': 'true'
                            'transparent': 'false'
                            'width': ''
                            'marked': 'false'
                            'xfill': 'false'
                            'animation': 0
                    - 'name': "Text"
                      'source': "3/0@1"
                      'frame-color': "#FFFF00"
                      'fill-color': "#FFFF00"
                      'frame-brightness': 0
                      'fill-brightness': 0
                      'dither-pattern': ''
                      'line-style': ''
                      'valid': 'true'
                      'visible': 'true'
                      'transparent': 'false'
                      'width': ''
                      'marked': 'false'
                      'xfill': 'false'
                      'animation': 0
    
    default_layer_properties : dict
        Default layer properties to define the visual aspect of the layer.
    data : dict
        Data that represents all layer information
    layer_sources : dict
        Keys = layer names. Values = layer source. Ex. {'Si': '1/0@1'}
    layer_names : list
        Ordered list of layer names in the sequence appearing in the
        Process YAML.
    lyp_file : str
        A string representing the XML-formatted layer properties .lyp file

    Examples
    --------
    The following shows how to instantiate the class, create the .lyp string,
    then print the .lyp string and write the .lyp string to a file
    
    >>> test_lyp = LayerStack(r'C:\test.yaml')
    >>> test_lyp.create_lyp_file() 
    >>> print(test_lyp.lyp_file) 
    >>> with open('test.lyp', 'w') as f:
            f.write(test_lyp.lyp_file)
    
    """
    

    ## Constructor:
    #  Get layer formatting params
    def __init__(self, process_yaml_file_path):
        self.layer_properties = {}
        self.default_layer_properties = {
                                            'frame-color': "#000000",
                                            'fill-color': "#000000",
                                            'frame-brightness': 0,
                                            'fill-brightness': 0,
                                            'dither-pattern': '',
                                            'line-style': '',
                                            'valid': 'true',
                                            'visible': 'true',
                                            'transparent': 'false',
                                            'width': '',
                                            'marked': 'false',
                                            'xfill': 'false',
                                            'animation': 0
                                        }
        self.get_layer_formatting_params(process_yaml_file_path)

    ## Parses foundry spec YAML for layer formatting
    #
    def get_layer_formatting_params(self, process_yaml_file_path):
        """Get layer properties from Process YAML and save to instance vars 
        
        Parses Process YAML for layer properties, keeping the layer sequence,
        layer order, and groupings. Restructures the layer properties as a dict.
        
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
                
        
        self.layer_data = data['layers']
        self.chip_data = data['chip']
        
        self.chip_type = data['chip']['type']
        for key, val in data['chip'].items():
            if key == self.chip_type:
                self.chip_dx = data['chip'][key]['design-area']['dx']
                self.chip_dy = data['chip'][key]['design-area']['dy']
        
        # Get layers in sequence
        layer_sequence = []
        layer_properties = {}
        layer_sources = {}
        # Get group sequences
        group_sequences = {}
        group_properties = {}
        group_sources = {}
        for layer in data['layers']:
            if layer.get('layer-properties') and layer.get('include-layer', True):
                # Set default layer properties
                # If YAML file specifies certain layer-properties, then replace default with YAML properties
                layer_prop = self.default_layer_properties.copy()
                
                name = layer.get('name')
                group_name = layer.get('group-name')
                if name:
                    # layer sequence
                    layer_sequence.append(name)
                    layer_sources[name] = layer.get('source')
                    
                    # If property specified in YAML, replace default with specified value
                    for prop, val in layer.get('layer-properties').items():
                        if prop in layer_prop:
                            layer_prop[prop] = val
                        else:
                            print("ERROR: \"{}\" does not exist in layer properties".format(prop))

                    layer_properties[name] = layer_prop
                elif group_name:
                    # group sequence
                    group_sequences[group_name] = layer.get('group-members')
                    group_sources[group_name] = layer.get('source')
                    
                    # If property specified in YAML, replace default with specified value
                    for prop, val in layer.get('layer-properties').items():
                        if prop in layer_prop:
                            layer_prop[prop] = val
                        else:
                            print("ERROR: \"{}\" does not exist in layer properties".format(prop))

                    group_properties[group_name] = layer_prop
                else:
                    pass
        
        # Save params as class instance variables
        self.layer_sources = layer_sources   
        self.layer_names = layer_sequence
        
        # Refactor with groups first then remaining layers
        for group, members_list in group_sequences.items():
            # Find first occurence of member in layer sequence
            try:
                first_occr_ind = layer_sequence.index(members_list[0])
            except ValueError:
                first_occr_ind = len(layer_sequence) - 1
                print("\"{}\" layer in group \"{}\" is not included or cannot be found in layer definitions... Skipping...".format(members_list[0],group))
                group_sequences[group].remove(members_list[0])
                 
            for member in members_list:
                try:
                    member_ind = layer_sequence.index(member)
                    if  member_ind < first_occr_ind:
                        first_occr_ind = layer_sequence.index(member)
                    layer_sequence.remove(member)
                except ValueError:
                    print("\"{}\" layer in group \"{}\" is not included  or cannot be found in layer definitions... Skipping...".format(member,group))
                    group_sequences[group].remove(member)

            # Re-insert group in layer sequence
            layer_sequence.insert(first_occr_ind, group)

        # Create layer-properties data structure
        self.layer_properties = {'layer-properties': {'properties': []}}
        for name in layer_sequence:
            # If name is group, expand and create members
            if name in group_sequences.keys():
                group_properties_dict = group_properties[name]
                group_properties_dict['name'] = name
                group_properties_dict['source'] = group_sources[name]
                group_properties_dict['group-members'] = []
                
                for member in group_sequences[name]:
                    member_dict = layer_properties[member]
                    member_dict['name'] = member
                    member_dict['source'] = layer_sources[member]
                    group_properties_dict['group-members'].append(member_dict)
                
                self.layer_properties['layer-properties']['properties'].append(group_properties_dict)
            else:
                layer_dict = layer_properties[name]
                layer_dict['name'] = name
                layer_dict['source'] = layer_sources[name]
                
                self.layer_properties['layer-properties']['properties'].append(layer_dict)
        
    ## Creates lyp file from foundry spec YAML file
    #
    def create_lyp_file(self):
        """Create .lyp (XML formatted) string
        
        Creates a string representing the XML formatted layer properties 
        .lyp file from a Process YAML.

        """
        # Create root element (level 0)
        root = ET.Element(list(self.layer_properties.keys())[0])
          
        # Recursively traverse the YAML file and create the XML doc
        self.create_sub_element(root, None, self.layer_properties['layer-properties'])
        
        # Save XML as string
        self.lyp_file = prettify(root)
        
    ## Recursively traverses a YAML doc and generates an XML tree
    #
    def create_sub_element(self, root, tag, element):
        """Create XML tree from layer properties dict
        
        Recursively traverses the layer properties dict to create the XML tree.
        
        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The root element of an XML tree.
        tag : str
            The `element` tag name.
        element : dict, list, str, int, float, bool
            The layer properties params dict, which is further parsed for values.
        
        Returns
        -------
        None.
        
        Examples
        --------
        The following shows how an XML tree is generated from a layer properties
        dict called `test_lyp_dict` assuming the root of the dict is 
        'layer-properties'. The `root` variable contains the generated XML tree.
        
        >>> import xml.etree.ElementTree as ET
        >>> root = ET.Element('layer-properties')
        >>> create_sub_element(root, None, test_lyp_dict['layer-properties'])

        """
        
        if type(element) == str or type(element) == int or type(element) == float or type(element) == bool:
            subelement = ET.SubElement(root, tag)
            if type(element) == bool:
                subelement.text = str(element).lower()
            else:
                subelement.text = str(element)
            return
        elif type(element) == dict:
            parent = ET.SubElement(root, tag)
            for tag_name, element_var in element.items():
                self.create_sub_element(parent, tag_name, element_var)
        elif type(element) == list:
            for i in range(0, len(element)):
                self.create_sub_element(root, tag, element[i])
        else:
            subelement = ET.SubElement(root, tag)
