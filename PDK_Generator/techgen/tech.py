from common.common_methods import prettify
import yaml
import xml.etree.ElementTree as ET

class Technology():
    r"""Class associated with Technology params
    
    A Process YAML is used to define Technology params and this class can create
    the .lyt (XML formatted) string necessary for KLayout's Technology Management
    (https://www.klayout.de/doc-qt5/about/technology_manager.html) 
    
    Parameters
    ----------
    process_yaml_file_path : str, optional
        Absolute file path for the Process YAML.
    
    Attributes
    ----------
    technology : dict
        Technology params used to generate the .lyt file. Defaults params are 
        specified in the dict and can be updated or changed.
    lyt_file : str
        A string representing the XML formatted .lyt file

    Examples
    --------
    The following shows how to instantiate the class, create the .lyt string,
    then print the .lyt string and write the .lyt string to a file
    
    >>> test_tech = Technology(r'C:\test.yaml')
    >>> test_tech.create_lyt_file() 
    >>> print(test_tech.lyt_file) 
    >>> with open('test.lyt', 'w') as f:
            f.write(test_tech.lyt_file)
            
    The following shows another way to create the .lyt string. By specifying
    the Process YAML upon creating the .lyt file, the technology params can be
    updated with new params.
    
    >>> test_tech = Technology()
    >>> test_tech.create_lyt_file(r'C:\test1.yaml') 
    >>> print(test_tech.lyt_file) 
    >>> with open('test1.lyt', 'w') as f:
            f.write(test_tech.lyt_file)
            
    >>> test_tech.create_lyt_file(r'C:\test2.yaml')
    >>> print(test_tech.lyt_file) 
    >>> with open('test2.lyt', 'w') as f:
            f.write(test_tech.lyt_file)
    
    """
    
    ## Constructor:
    #
    def __init__(self, process_yaml_file_path=""):
        # Set default technology params
        self.lyt_file = ''
        self.technology = {'technology':
                               {'add-other-layers': True,
                                'base-path': None,
                                'connectivity': None,
                                'dbu': 0.001,
                                'description': '',
                                'group': None,
                                'layer-properties_file': '',
                                'name': '',
                                'original-base-path': '',
                                'reader-options':
                                    {'cif':
                                       {'create-other-layers': True,
                                        'dbu': 0.001,
                                        'keep-layer-names': False,
                                        'layer-map': 'layer_map()',
                                        'wire-mode': 0},
                                     'common':
                                       {'create-other-layers': True,
                                        'enable-properties': True,
                                        'enable-text-objects': True,
                                        'layer-map': 'layer_map()'},
                                     'dxf':
                                       {'circle-accuracy': 0,
                                        'circle-points': 100,
                                        'contour-accuracy': 0,
                                        'create-other-layers': True,
                                        'dbu': 0.001,
                                        'keep-layer-names': False,
                                        'keep-other-cells': False,
                                        'layer-map': 'layer_map()',
                                        'polyline-mode': 0,
                                        'render-texts-as-polygons': False,
                                        'text-scaling': 100,
                                        'unit': 1},
                                     'gds2':
                                       {'allow-big-records': True,
                                        'allow-multi-xy-records': True,
                                        'box-mode': 1},
                                     'lefdef':
                                       {'blockages-datatype': 4,
                                        'blockages-suffix': '.BLK',
                                        'cell-outline-layer': 'OUTLINE',
                                        'dbu': 0.001,
                                        'inst-property-name': '#1',
                                        'labels-datatype': 1,
                                        'labels-suffix': '.LABEL',
                                        'layer-map': 'layer_map()',
                                        'net-property-name': '#1',
                                        'obstructions-datatype': 3,
                                        'obstructions-suffix': '.OBS',
                                        'pin-property-name': '#1',
                                        'pins-datatype': 2,
                                        'pins-suffix': '.PIN',
                                        'placement-blockage-layer': 'PLACEMENT_BLK',
                                        'produce-blockages': True,
                                        'produce-cell-outlines': True,
                                        'produce-inst-names': True,
                                        'produce-labels': True,
                                        'produce-net-names': True,
                                        'produce-obstructions': True,
                                        'produce-pin-names': False,
                                        'produce-pins': True,
                                        'produce-placement-blockages': True,
                                        'produce-regions': True,
                                        'produce-routing': True,
                                        'produce-via-geometry': True,
                                        'read-all-layers': True,
                                        'region-layer': 'REGIONS',
                                        'routing-datatype': 0,
                                        'routing-suffix': None,
                                        'via-geometry-datatype': 0,
                                        'via-geometry-suffix': None},
                                     'mag':
                                       {'create-other-layers': True,
                                        'dbu': 0.001,
                                        'keep-layer-names': False,
                                        'lambda': 1,
                                        'layer-map': 'layer_map()',
                                        'lib-paths': None,
                                        'merge': True},
                                     'mebes':
                                       {'boundary-datatype': 0,
                                        'boundary-layer': 0,
                                        'boundary-name': 'BORDER',
                                        'create-other-layers': True,
                                        'data-datatype': 0,
                                        'data-layer': 1,
                                        'data-name': 'DATA',
                                        'invert': False,
                                        'layer-map': 'layer_map()',
                                        'num-shapes-per-cell': 0,
                                        'num-stripes-per-cell': 64,
                                        'produce-boundary': True,
                                        'subresolution': True}
                                    },
                                'writer-options':
                                    {'cif':
                                       [{'polygon-mode': 0},
                                        {'blank-separator': False,
                                         'dummy-calls': False}],
                                     'gds2':
                                       {'libname': '',
                                        'max-cellname-length': 32000,
                                        'max-vertex-count': 8000,
                                        'multi-xy-records': False,
                                        'no-zero-length-paths': False,
                                        'write-cell-properties': False,
                                        'write-file-properties': False,
                                        'write-timestamps': True},
                                     'mag':
                                       {'lambda': 0,
                                        'tech': None,
                                        'write-timestamp': True},
                                     'oasis':
                                       {'compression-level': 10,
                                        'permissive': False,
                                        'strict-mode': False,
                                        'subst-char': '*',
                                        'write-cblocks': False,
                                        'write-std-properties': 1}
                                    }
                               }
                          }
        
        if process_yaml_file_path != "":
            self.get_technology_params(process_yaml_file_path)
        
    ## Parses foundry spec YAML file for technology params
    #  Save params as class variables
    def get_technology_params(self, process_yaml_file_path=""):
        """Get tech params from Process YAML and save as instance variable
        
        Parameters
        ----------
        process_yaml_file_path : str, optional
            Absolute file path for the Process YAML. The default is "".

        Returns
        -------
        None.

        """
        try:
            with open(process_yaml_file_path) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except:
            print("No YAML file specified... Cannot obtain technology... Passing...")
            return
        
        technology_params = data.get('technology', None)
        if technology_params:
            technology = {'technology': technology_params}
            self.update_technology_params(self.technology, technology, 'technology', technology_params)
        

    def create_lyt_file(self, process_yaml_file_path=""):
        """Create string, representing the .lyt (XML formatted) file
        
        If no Process YAML specified, default params will be used to generate
        the .lyt file.
        
        Parameters
        ----------
        process_yaml_file_path : str, optional
            Absolute path of the Process YAML. The default is "".

        Returns
        -------
        None.

        """
        # If process_yaml_file_path is specified, get technology params
        if process_yaml_file_path != "":
            self.get_technology_params(process_yaml_file_path)

        # Create root element
        root = ET.Element(list(self.technology.keys())[0])

        # Recursively traverse the YAML file and create the XML doc
        self.create_sub_element(root, None, self.technology['technology'])
        
        # Save XML as string
        self.lyt_file = prettify(root)


    def create_sub_element(self, root, tag, element):
        """Create XML tree from tech dict
        
        Recursively traverses the tech dict to create the XML tree

        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            The root element of an XML tree.
        tag : str
            The `element` tag name.
        element : dict, list, str, int, float, bool
            The tech params dict, which is further parsed for values.

        Returns
        -------
        None.
        
        Examples
        --------
        The following shows how an XML tree is generated from a tech dict called
        `test_tech_dict`. `root` contains the generated XML tree.
        
        test_tech_dict = {'technology':
                            {'add-other-layers': True,
                             'base-path': None,
                             'connectivity': None,
                             ...
                             ...
                             ...
                            }
                        }
        
        >>> import xml.etree.ElementTree as ET
        >>> root = ET.Element('technology')
        >>> create_sub_element(root, None, test_tech_dict['technology'])

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
    

    def update_technology_params(self, tech_dict, params_dict, params_key, params_value):
        """Update tech params dict
        
        Recursively updates tech params if available 
        
        Parameters
        ----------
        tech_dict : dict
            Technology dictionary to be updated.
        params_dict : dict
            Technology dictionary with params used to update `tech_dict`.
        params_key : str
            Key from `params_dict`. As the first call to this method, `params_key`
            should be 'technology' since 'technology' is the keyword for the 
            root of the technology params dict.
        params_value : dict, list, str, int, float, bool
            Value from `params_dict`.

        Returns
        -------
        None.
        
        Examples
        --------
        The following shows how to update a technology dict called `test_tech1`
        based on a technology dict called `test_tech2`. Note that `test_tech1`
        and `test_tech2` have the 'technology' string as the first and only key
        in the first level or root of the dict:
            
        test_tech1 = {'technology':
                        {'add-other-layers': True,
                         'base-path': None,
                         'connectivity': None,
                         ...
                         ...
                         ...
                        }
                    }
            
        test_tech2 = {'technology':
                        {'add-other-layers': True,
                         'base-path': None,
                         'connectivity': None,
                         ...
                         ...
                         ...
                        }
                    }
                         
        >>> update_technology_params(test_tech1, test_tech2, 'technology',
                                     test_tech2['technology'])
        
        """
        if params_key not in tech_dict:
            print("ERROR: \"{}\" not in technology data structure... Passing...".format(params_key))
            return
        elif type(params_value) == str or type(params_value) == int or type(params_value) == float or type(params_value) == bool:
            tech_dict[params_key] = params_value
        elif type(params_value) == dict:
            for k, v in params_value.items():
                self.update_technology_params(tech_dict[params_key], params_value, k, v)
        elif type(params_value) == list:
            for i in range(0, len(params_value)):
                for k, v in params_value[i].items():
                    self.update_technology_params(tech_dict[params_key][i], params_value[i], k, v)

