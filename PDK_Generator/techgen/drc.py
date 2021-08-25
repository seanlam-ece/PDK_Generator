import yaml
from common.common_methods import convert_to_macro

class DRC():
    """Class associated with DRC params
    
    A Process YAML is used to define DRC params and this class can create
    the .lydrc (XML formatted) string, which can be written to a .lydrc file to
    be used for KLayout's DRC engine
    (https://www.klayout.de/doc-qt5/manual/drc.html).
    
    DRC only supports the following checks:
        min feature size
        min spacing
        min overlap
        min enclosing
        min exclusion
        FloorPlan boundary
    
    Parameters
    ----------
    process_yaml_file_path : str, optional
        Absolute file path for the Process YAML.
        
    Attributes
    ----------
    tol : float
        Absolute tolerance used to remove false errors (micrometers).
    angle_limit : float
        Any angle above this will not be checked
    keywords : list of str
        List of keywords associated to DRC params
    layers : dict
        List of layers and their process params
    chip : dict
        Chip type used
    units : str
        Units for the params
    layer_setups : dict
        Layer sources. Ex. {'Si': [1,0]}
    layer_masks : dict
        Layer masks for each layer. Either 'negative' or 'positive'
    layer_min_feature_sizes : dict
        Min feature sizes for each layer. Ex. {'Si': 0.06}
    layer_min_spacings : dict
        Min spacings for each layer. Ex. {'Si': 0.06}
    layer_min_overlaps : dict
        Min overlaps for each pair of layers. Ex. {'Si': {'Si_Npp': 0.02}}
    layer_min_enclosures : dict
        Min enclosures for each pair of layers. Ex. {'Si': {'Si_rib': 0.01}}
    layer_min_exclusions : dict
        Min exclusions for each pair of layers. Ex. {'Si': {'M1': 0.02}}
    layer_is_device : dict
        Used to check whether layer is within FloorPlan. Ex. {'Si': True}
    layer_names : list of str
        List of layer names associated with DRC
    lydrc_file : str
        String representing the .lydrc code for KLayout's DRC engine
    drc_dict : dict
        DRC params that can be dumped to a YAML file
    
    Examples
    --------
    The following shows how to instantiate the class, create the .lydrc string,
    then print the .lydrc string and write the .lydrc string to a file
    
    >>> FoundryDRC = DRC(tech_file_location)
    >>> FoundryDRC.create_lydrc_file()
    >>> print(FoundryDRC.lydrc_file)
    >>> with open('test1.lydrc', 'w') as f:
            f.write(FoundryDRC.lydrc_file)
    
    """
    
    
    ## Constructor:
    #
    def __init__(self, process_yaml_file_path):
        # Users usually shoot for exactly min features
        # For curves, this leeads to lots of false errors
        self.tol = 1e-3
        self.angle_limit = 80
        
        # Used to check whether layer is part of DRC checks
        self.keywords = ['is-device-layer', 'min-feature-size', 'min-spacing', 'min-exclusion',
                         'min-overlap', 'min-enclosing']

        self.get_DRC_params(process_yaml_file_path)

    ## Parses foundry spec YAML file for DRC params then
    #  Initializes DRC params as dictionaries and lists in class variables
    def get_DRC_params(self, process_yaml_file_path):
        """Get DRC params from Process YAML
        
        Parse Process YAML for DRC params and save DRC params as instance vars.
        
        Parameters
        ----------
        process_yaml_file_path : str
            Absolute file path for Process YAML.
        
        Returns
        -------
        None.

        """
        try:
            with open(process_yaml_file_path) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain DRC params... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain DRC params... Passing...")
            return

        self.layers = data['layers']
        self.chip = data['chip']
        self.units = data['units']
        self.techname = data['technology']['name']

        # Parse and populate appropriate layer parameters
        layer_setups = {}
        layer_masks = {}
        layer_min_feature_sizes = {}
        layer_min_spacings = {}
        layer_min_overlaps = {}
        layer_min_enclosures = {}
        layer_min_exclusions = {}
        layer_is_device = {}
        for layer in self.layers:
            layer_keys = list(layer.keys())
            # If layer has any DRC related params, get layer params
            try:
                layer_name = layer['name']
            except KeyError:
                print("No available layer name... Layer might be a group... Continuing to next layer...")
                continue
                
            if (any(item in self.keywords for item in layer_keys)
                or layer_name == "FloorPlan"
                or layer_name == "DevRec") \
                and layer.get('include-layer', True):
                layer_source = layer['source'].split('@')
                layer_number_datatype = layer_source[0]
                layer_number = int(layer_number_datatype.split('/')[0])
                layer_datatype = int(layer_number_datatype.split('/')[1])
                layer_setups.update({layer_name: [layer_number,layer_datatype]})
                if layer.get('mask', None) != None:
                    layer_masks.update({layer_name: layer['mask']})
                if layer.get('min-feature-size', None) != None:
                    layer_min_feature_sizes.update({layer_name: layer['min-feature-size']})
                if layer.get('min-spacing', None) != None:
                    layer_min_spacings.update({layer_name: layer['min-spacing']})
                if layer.get('min-overlap', None) != None:
                    layer_min_overlaps.update({layer_name: layer['min-overlap']})
                if layer.get('min-enclosing', None) != None:
                    layer_min_enclosures.update({layer_name: layer['min-enclosing']})
                if layer.get('min-exclusion', None) != None:
                    layer_min_exclusions.update({layer_name: layer['min-exclusion']})
                if layer.get('is-device-layer', None) != None:
                    layer_is_device.update({layer_name: layer['is-device-layer']})

        # Save layer params as class variables to be accessed
        self.layer_setups = layer_setups
        self.layer_masks = layer_masks
        self.layer_min_feature_sizes = layer_min_feature_sizes
        self.layer_min_spacings = layer_min_spacings
        self.layer_min_overlaps = layer_min_overlaps
        self.layer_min_enclosures = layer_min_enclosures
        self.layer_min_exclusions = layer_min_exclusions
        self.layer_is_device = layer_is_device
        self.layer_names = list(layer_setups.keys())

        # Parse and populate chip params
        chip_type = self.chip['type']
        self.chip = data['chip'][chip_type]

    ## Creates .lydrc DRC macro from a YAML file
    def create_lydrc_file(self):
        """Create string, respresenting .lydrc code
        
        The .lydrc file is created from DRC params from a Process YAML. The .lydrc
        file can be run in command line by running KLayout in batch mode in
        command line.

        """
        # Create array to store each line of .lydrc code
        # Initialize array with some comments
        self.lydrc_file = ["## = DRC Implementation",
                         "#  ---",
                         "#  Implements DRC based on a YAML DRC file",
                         "",
                         "# Run DRC",
                         "# Specify a source GDS file and an output results database file to run the DRC in command line",
                         "source($in_gdsfile)",
                         "report(\"DRC\", $out_drc_results)",
                         ""]

        # Get input layers
        self.get_input_layers(self.layer_setups)

        # Create section for non-physical checks
        self.write_lines(["",
                      "#################",
                      "# non-physical checks",
                      "#################"
                      "",
                      "# Check device overlaps (functional check)",
                      "overlaps = layer_DevRec.merged(2)",
                      "output(overlaps, \"Devices\",\"Devices cannot be overlapping\")",
                      ""])

        # Make sure devices are in floor plan
        self.check_devices_in_floor_plan(self.layer_is_device)

        # Create section for physical checks:
        # min feature sizes, min spacing, min overlap, min exclusion, min enclosures
        self.write_lines(["",
                          "#################",
                          "# physical checks",
                          "#################",
                          "",
                          "# Users usually shoot for exactly min features",
                          "# For curves, this leeads to lots of false errors",
                          "tol = {}".format(self.tol),
                          ""])

        # Perform min feature size checks
        self.perform_min_feature_size_check(self.layer_min_feature_sizes)
        self.write_line("")

        # Perform min spacing checks
        self.perform_min_spacing_check(self.layer_min_spacings)
        self.write_line("")

        # Perform min exclusion checks
        self.perform_min_exclusion_check(self.layer_min_exclusions)
        self.write_line("")
        
        # Perform min overlap checks
        self.perform_min_overlap_check(self.layer_min_overlaps)
        self.write_line("")

        # Perform min enclosure checks
        self.perform_min_enclosing_check(self.layer_min_enclosures)
        self.write_line("")
        
        # Convert from list to string
        lydrc_code = ""
        for line in self.lydrc_file:
            lydrc_code += line + "\n"
        
        # Convert to XML macro
        macro_dict = {
                        'description': 'KLayout Manufacturing DRC - ' + self.techname,
                        'category': 'drc',
                        'autorun': 'false',
                        'autorun-early': 'false',
                        'show-in-menu': 'true',
                        "shortcut": "D",
                        'menu-path': 'siepic_menu.verification.begin',
                        'group-name': 'drc_scripts',
                        'interpreter': 'dsl',
                        'dsl-interpreter-name': 'drc-dsl-xml',
                        'text': lydrc_code
                    }
        
        self.lydrc_file = convert_to_macro(macro_dict)
        

    ## Appends a single line of code to the lydrc file
    def write_line(self, line):
        """Append single line of Ruby DRC code to lydrc_file str

        Parameters
        ----------
        line : str
            Line of Ruby DRC code.

        Returns
        -------
        None.

        """
        self.lydrc_file.append(line)

    ## Appends lines of code to the lydrc file assuming lines is a list
    def write_lines(self, lines):
        """Append lines of Ruby DRC code to lydrc_file str
        
        Parameters
        ----------
        lines : list of str
            Lines of Ruby DRC code.

        Returns
        -------
        None.

        """
        for line in lines:
            self.lydrc_file.append(line)


    def get_input_layers(self, layer_setups):
        """Append function calls to lydrc_file str to get input layers
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine.
        
        Ex. Function Call:
            layer_Si_rib = input(2,0)

        Parameters
        ----------
        layer_setups : dict
            Layer sources. Ex. {'Si': [1,0]'}

        Returns
        -------
        None.

        """
        
        if len(layer_setups) > 0:
            self.lydrc_file.append("# Get layers from layout")
            for layer_name, layer_info in layer_setups.items():
                # Get layer number, datatype, layer name
                layer_number = layer_info[0]
                layer_datatype = layer_info[1]
                layer_name = self.convert_layer_name(layer_name)
    
                # Create input layer function statements
                self.lydrc_file.append("{} = input({},{})".format(layer_name,\
                                                                layer_number,\
                                                                layer_datatype))


    def check_devices_in_floor_plan(self, layer_is_device):
        """Append function calls to lydrc_file str to check layers are inside floor plan
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. 
        
        Ex. Function Call:
            layer_Si_rib.outside(layer_FP).output("Boundary",
                                "Si_rib devices are out of boundary")

        Parameters
        ----------
        layer_is_device : dict
            Dict of bools signalling whether a layer should be inside the 
            FloorPlan layer. Ex. {'Si': True}.

        Returns
        -------
        None.

        """
        
        if len(layer_is_device) > 0:
            self.lydrc_file.append("# Make sure devices are within floor plan layer region")
            for layer_name, is_device in layer_is_device.items():
                if is_device:
                    layer_name_r = self.convert_layer_name(layer_name)
                    self.lydrc_file.append("{}.outside(layer_FloorPlan).output(\"Boundary\",\"{}"\
                                         " devices are out of boundary\")".format(layer_name_r, layer_name))


    def convert_layer_name(self, layer_name):
        """Convert layer name to a Ruby variable name
        
        Replace spaces with underscores, plus signs with 'p', minus signs with 'n'.
        Resultant Ruby variable name must be syntactically correct in Ruby 
        language.
        
        Parameters
        ----------
        layer_name : str
            Layer name found in Process YAML

        Returns
        -------
        layer_name : str
            Syntactically-correct Ruby variable name

        """
        layer_name_split = layer_name.split(" ")
        num_spaces = len(layer_name.split(" "))
        if num_spaces > 1:
            layer_name = "layer"
            for name in layer_name_split:
                layer_name += "_" + name
        else:
            layer_name = "layer_" + layer_name_split[0]
            
        layer_name = layer_name.replace("+","p")
        layer_name = layer_name.replace("-","n")
        return layer_name


    def perform_min_feature_size_check(self, layer_min_feature_sizes):
        """Append function calls to lydrc_file str to check min feature size
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. Projection metrics, angle limits, and tolerances are
        used.
        
        Ex. Function Calls:
            layer_Si.width(layer_min_feature_size-tol, angle_limit(80), projection)
            .output("Si width", "Si minimum feature size violation; min 0.06 um")
        
        Parameters
        ----------
        layer_min_feature_sizes : dict
            Min spacing between features on the same layer. Ex. {'Si': 0.06}.

        Returns
        -------
        None.

        """
        
        if len(layer_min_feature_sizes) > 0:
            self.lydrc_file.append("# Perform min feature size check")
            for layer_name, min_feature_size in layer_min_feature_sizes.items():
                layer_name_r = self.convert_layer_name(layer_name)
                self.lydrc_file.append("{layer_name_r}.width({min_feature_size}-tol,"\
                                     "angle_limit({angle_limit}), projection).output(\"{layer_name} "\
                                     "width\", \"{layer_name} minimum feature size violation; "\
                                     "min {min_feature_size} {units}\")".format(layer_name_r=layer_name_r, \
                                                                                layer_name=layer_name, \
                                                                                min_feature_size=min_feature_size, \
                                                                                angle_limit=self.angle_limit, \
                                                                                units=self.units))


    def perform_min_spacing_check(self, layer_min_spacings):
        """Append function calls to lydrc_file str to check min spacing
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. Projection metrics, angle limits, and tolerances are
        used.   
        
        Ex. Function Calls:
            layer_Si.space(layer_min_spacing-tol, angle_limit(80), projection)
            .output("Si space", "Si minimum space violation; min 0.06 um")
        
        Parameters
        ----------
        layer_min_spacings : dict
            Min spacing between features on the same layer. Ex. {'Si': 0.06}.

        Returns
        -------
        None.

        """
        
        if len(layer_min_spacings) > 0:
            self.lydrc_file.append("# Perform min spacing check")
            for layer_name, min_spacing in layer_min_spacings.items():
                layer_name_r = self.convert_layer_name(layer_name)
                self.lydrc_file.append("{layer_name_r}.space({min_spacing}-tol,"\
                                     "angle_limit({angle_limit}), projection).output(\"{layer_name} "\
                                     "space\", \"{layer_name} minimum space violation; "\
                                     "min {min_spacing} {units}\")".format(layer_name_r=layer_name_r, \
                                                                           layer_name=layer_name, \
                                                                           min_spacing=min_spacing, \
                                                                           angle_limit=self.angle_limit, \
                                                                           units=self.units))


    def perform_min_exclusion_check(self, layer_min_exclusions):
        """Append function calls to lydrc_file str to check min exclusion between layers
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. Projection metrics and tolerances are used.     
        
        Ex. Function Calls:
            layer_Si.separation(layer_Si_rib, layer_min_exclusion-tol, projection)
            .output("Si-Si_rib separation", "Si-Si_rib minimum separation violation;
            min 0.06 um")
        
        Parameters
        ----------
        layer_min_exclusions : dict
            Min exclusions between two layers. Ex. {'Si': {'M1': 0.02}}

        Returns
        -------
        None.

        """
        if len(layer_min_exclusions) > 0:
            self.lydrc_file.append("# Perform min exclusion check")
            for layer_name1, layer2 in layer_min_exclusions.items():
                layer_name_r1 = self.convert_layer_name(layer_name1)
    
                for layer_name2, min_exclusion in layer2.items():
                    layer_name_r2 = self.convert_layer_name(layer_name2)
                    self.lydrc_file.append("{layer_name_r1}.separation({layer_name_r2}, "\
                                         "{min_exclusion}-tol, projection).output(\"{layer_name1}-{layer_name2} separation\","\
                                         "\"{layer_name1}-{layer_name2} minimum separation violation; "\
                                         "min {min_exclusion} {units}\")".format(layer_name_r1=layer_name_r1, \
                                                                                 layer_name_r2=layer_name_r2, \
                                                                                 layer_name1=layer_name1, \
                                                                                 layer_name2=layer_name2, \
                                                                                 min_exclusion=min_exclusion, \
                                                                                 units=self.units))


    def perform_min_overlap_check(self, layer_min_overlaps):
        """Append function calls to lydrc_file str to check min overlap between layers
    
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. Projection metrics and tolerances are used.       
        
        Ex. Function Call:
            layer_Si.overlap(layer_Si_rib, layer_min_overlap-tol, projection)
            .output("Si-Si_rib overlap", "Si-Si_rib minimum overlap violation;
                    min 0.06 um")
        
        Parameters
        ----------
        layer_min_overlaps : dict
            Min overlaps between two layers. Ex. {'Si': {'Si_Npp': 0.02}}

        Returns
        -------
        None.

        """
        
        if len(layer_min_overlaps) > 0:
            self.lydrc_file.append("# Perform min overlap check")
            for layer_name1, layer2 in layer_min_overlaps.items():
                layer_name_r1 = self.convert_layer_name(layer_name1)
    
                for layer_name2, min_overlap in layer2.items():
                    layer_name_r2 = self.convert_layer_name(layer_name2)
                    self.lydrc_file.append("{layer_name_r1}.overlap({layer_name_r2}, "\
                                         "{min_overlap}-tol, projection).output(\"{layer_name1}-{layer_name2} overlap\","\
                                         "\"{layer_name1}-{layer_name2} minimum overlap violation; "\
                                         "min {min_overlap} {units}\")".format(layer_name_r1=layer_name_r1, \
                                                                                 layer_name_r2=layer_name_r2, \
                                                                                 layer_name1=layer_name1, \
                                                                                 layer_name2=layer_name2, \
                                                                                 min_overlap=min_overlap, \
                                                                                 units=self.units))


    def perform_min_enclosing_check(self, layer_min_enclosures):
        """Append function calls to lydrc_file str to check min enclosures between layers
        
        Function calls are done within .lydrc scripts, which run in KLayout's
        Ruby DRC engine. Projection metrics and tolerances are used.
        
        Ex. Function Call:
            layer_Si.enclosing(layer_Si_rib, layer_min_enclosure-tol, 
                               projection).output("Si-Si_rib enclosure",
                               "Si-Si_rib minimum enclosure vilation;
                               min 0.02 um")

        Parameters
        ----------
        layer_min_enclosures : dict
            Min enclosures between two layers. Ex. {'Si': {'Si_rib': 0.01}}

        Returns
        -------
        None.

        """
        if len(layer_min_enclosures) > 0:
            self.lydrc_file.append("# Perform min enclosing check")
            for layer_name1, layer2 in layer_min_enclosures.items():
                layer_name_r1 = self.convert_layer_name(layer_name1)
    
                for layer_name2, min_enclosure in layer2.items():
                    layer_name_r2 = self.convert_layer_name(layer_name2)
                    self.lydrc_file.append("{layer_name_r1}.enclosing({layer_name_r2}, "\
                                         "{min_enclosure}-tol,projection).output(\"{layer_name1}-{layer_name2} enclosure\","\
                                         "\"{layer_name1}-{layer_name2} minimum enclosure violation; "\
                                         "min {min_enclosure} {units}\")".format(layer_name_r1=layer_name_r1, \
                                                                                 layer_name_r2=layer_name_r2, \
                                                                                 layer_name1=layer_name1, \
                                                                                 layer_name2=layer_name2, \
                                                                                 min_enclosure=min_enclosure, \
                                                                                 units=self.units))
    
    def create_drc_dict(self):
        """Create DRC dict
        
        DRC dict is used for generating the DRC YAML found in a particular PDK

        Returns
        -------
        None.

        """
        drc_dict = {'units': self.units}
        for name in self.layer_names:
            drc_dict[name] = {}

            source = self.layer_setups.get(name, False)
            mask = self.layer_masks.get(name, False)
            min_feature_size = self.layer_min_feature_sizes.get(name, False)
            min_spacing = self.layer_min_spacings.get(name, False)
            min_overlaps = self.layer_min_overlaps.get(name, False)
            min_enclosures = self.layer_min_enclosures.get(name, False)
            min_exclusions = self.layer_min_exclusions.get(name, False)
            
            if source:
                drc_dict[name]['source'] = "{}/{}".format(source[0], source[1])
            if mask:
                drc_dict[name]['mask'] = mask
            if min_feature_size:
                drc_dict[name]['min-feature-size'] = min_feature_size
            if min_spacing:
                drc_dict[name]['min-spacing'] = min_spacing
            if min_overlaps:
                drc_dict[name]['min-overlap'] = min_overlaps
            if min_enclosures:
                drc_dict[name]['min-enclosing'] = min_enclosures
            if min_exclusions:
                drc_dict[name]['min-exclusion'] = min_exclusions
        
        self.drc_dict = drc_dict
                
