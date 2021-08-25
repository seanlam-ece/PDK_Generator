import yaml

class XSection():
    r"""Class associated with XSection or cross section information
    
    A Process YAML is used to define XSection params and this class can create
    the .xs code necessary for KLayout's XSection functionality
    (https://github.com/klayoutmatthias/xsection) 
    
    Parameters
    ----------
    process_yaml_file_path : str
        Absolute file path for the Process YAML.
    
    Attributes
    ----------
    data : dict
        Layer information from the Process YAML.
    height : float
        Height of XSection processing window. Any layers taller than this will
        not be shown in the cross section view.
    keywords_priority : list of str
        Keywords found in the Process YAML used to determine the order in which
        XSection code should be generated and the XSection function called in
        the .xs code.
    layer_sequence : list of str
        Ordered sequence of layers that is used to generate the cross section.
    layer_xsection_cmds : list of dict
        Data structure with ordered sequence of layers along with ordered
        sequence of XSection commands
    layer_sources : dict
        Keys = Layer Names; Values = Layer Sources (i.e. {Si: "1/0@1"})
    xs_file : str
        XSection code that can be written to a .xs file
    
    Examples
    --------
    The following shows how to instantiate the class, create the .xs code, then
    print the .xs code and write the .xs code to a file
    
    >>> testxs = XSection(r'C:\test.yaml')
    >>> testxs.create_xs_file() 
    >>> print(testxs.xs_file) 
    >>> with open('test.xs', 'w') as f:
            f.write(testxs.xs_file)

    """

    def __init__(self, process_yaml_file_path):
        self.data = {}
        self.height = 7.5
        self.keywords_priority = ['grow-entire-layer','mask', 'grow', 'etch', 'output']
        self.get_xsection_params(process_yaml_file_path)


    def get_xsection_params(self, process_yaml_file_path):
        '''Get and save XSection params as instance variables
        
        Parses a Process YAML (containing foundry specific parameters) for 
        XSection params.

        Parameters
        ----------
        process_yaml_file_path : str
            Absolute file path for the Process YAML

        Returns
        -------
        None

        '''
        try:
            with open(process_yaml_file_path) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain XSection params... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain XSection params... Passing...")
            return

        self.data = data['layers']
        
        # Get Xsection info
        layer_sequence = []
        layer_sources = {}
        layer_xsection_commands = []
        
        for layer in data['layers']:
            layer_name = layer.get('name', None)
            if layer.get('include-layer', False) and layer_name:
                
                # Append layer name to sequence
                layer_sequence.append(layer_name)
                
                # Save layer sources by name
                layer_sources[layer_name] = layer.get('source').split("@")[0]
                
                # Get xsection commands in layer
                xsection_cmds = []
                layer_keywords = list(layer.keys())
                for keyword in self.keywords_priority:
                    if keyword in layer_keywords:
                        # Check for additiional options
                        if keyword == 'grow':
                            bias = layer.get('bias', '0')
                            sidewall_angle = layer.get('sidewall-angle', None)
                            layer['grow'].append(':bias => {}'.format(bias))
                            # Check to ensure :mode is not specified when sidewall angle is specified
                            if sidewall_angle and any(":mode" in str(param) for param in layer['grow']):
                                print("ERROR: mode and taper cannot be specified in same command")
                            elif sidewall_angle:
                                layer['grow'].append(':taper => {}'.format(90.0-sidewall_angle))
                        elif keyword == 'etch':
                            bias = layer.get('bias', '0')
                            sidewall_angle = layer.get('sidewall-angle', '0')
                            layer['etch'].append(':bias => {}'.format(bias))
                            # Check to ensure :mode is not specified when sidewall angle is specified
                            if sidewall_angle and any(":mode" in str(param) for param in layer['etch']):
                                print("ERROR: mode and taper cannot be specified in same command")
                            elif sidewall_angle:
                                layer['etch'].append(':taper => {}'.format(90.0-sidewall_angle))
                            
                        xsection_cmds.append({keyword: layer[keyword]})

                # Add xsection commands to layer
                layer_xsection_commands.append({layer_name: xsection_cmds})
                
        # Save XSection info
        self.layer_sequence = layer_sequence
        self.layer_xsection_cmds = layer_xsection_commands
        self.layer_sources = layer_sources

    ## Creates .xs file
    def create_xs_file(self):
        """Create string that represents XSection code"""
        
        # Create string used to generate .xs file
        self.xs_file = ""
        
        # Insert comments about the cross section script
        self.write_lines(["## = SiEPIC Cross-Section",
                          "#  ---",
                          "#  Creates a cross section view based on a layout",
                          "#  XSection Tool: https://klayoutmatthias.github.io/xsection/DocIntro",
                          "",
                          "# Configure processing window",
                          "height({}) # Anything above this will not appear in cross section\n".format(self.height)])
        
        # Create input layers
        for layer_name, layer_source in self.layer_sources.items():
            layer_name = self.convert_layer_name(layer_name)
            self.write_line("{} = layer(\"{}\")".format(layer_name, layer_source))
        
        # Output substrate
        self.write_line("\noutput(\"0/0\", bulk)")
        
        # Stores temporary layer object variable names used in xs script
        layer_objs = []
        # Create process steps
        for layer_ind in range(0,len(self.layer_sequence)):
            # Get layer_name
            layer_name = self.layer_sequence[layer_ind]
            
            # Loop through each step inside each layer_step and create the process steps
            for step in self.layer_xsection_cmds[layer_ind][layer_name]:
                # Get the current and next step names
                curr_step_name = list(step.keys())[0]
                # Only get next step if we are not at the last step
                if step != self.layer_xsection_cmds[layer_ind][layer_name][-1]:
                    next_step_name = list(self.layer_xsection_cmds[layer_ind][layer_name][self.layer_xsection_cmds[layer_ind][layer_name].index(step)+1].keys())[0]
            
                # Mask - Invert layer depending on negative vs. positive resist
                if curr_step_name == "mask" and next_step_name == "etch":
                    if step[curr_step_name] == "negative":
                        layer_name_r = self.convert_layer_name(layer_name) + ".inverted"
                    elif step[curr_step_name] == "positive":
                        layer_name_r = self.convert_layer_name(layer_name)
                elif curr_step_name == "mask" and next_step_name == "grow":
                    if step[curr_step_name] == "negative":
                        layer_name_r = self.convert_layer_name(layer_name)
                    elif step[curr_step_name] == "positive":
                        layer_name_r = self.convert_layer_name(layer_name) + ".inverted"
                
                # Grow entire layer
                if curr_step_name == "grow-entire-layer":
                    # If more than 1 param specified, iterate to create comma separated string
                    if len(step[curr_step_name]) == 1:
                        grow_params = str(step[curr_step_name][0])
                    elif len(step[curr_step_name]) > 1:
                        grow_params = str(step[curr_step_name][0])
                        for i in range(1, len(step[curr_step_name])):
                            grow_params = grow_params + "," + str(step[curr_step_name][i])
                    
                    # If layer_obj already exists, "OR" with previous layer definition
                    layer_obj = "x_" + layer_name
                    if layer_obj in layer_objs:
                        self.write_line("{} = {}.or(grow({}))".format(layer_obj, layer_obj, grow_params))
                    else:
                        self.write_line("{} = grow({})".format(layer_obj, grow_params))
                        layer_objs.append(layer_obj)
                   
                # Etch
                if curr_step_name == "etch":
                    
                    # If more than 1 param is specified, create etch params as a comma separated string
                    if len(step[curr_step_name]) == 1:
                        etch_params = str(step[curr_step_name][0])
                    elif len(step[curr_step_name]) > 1:
                        etch_params = str(step[curr_step_name][0])
                        for i in range(1, len(step[curr_step_name])):
                            # Check whether layer is included in XSection
                            if step[curr_step_name][i] in self.layer_sequence:
                                # Check whether temporary layer object exists
                                if ("x_"+str(step[curr_step_name][i])) in layer_objs:
                                    etch_params = etch_params + "," + " :into => x_" + str(step[curr_step_name][i])
                                else:
                                    print("ERROR-ETCH: layer object not available")
                            else:
                                etch_params = etch_params + "," + str(step[curr_step_name][i])

                    self.write_line("mask({}).etch({})".format(layer_name_r, etch_params))

                # Grow
                if curr_step_name == "grow":
                    # If more than 1 param is specified, create grow params as a comma separated string
                    if len(step[curr_step_name]) == 1:
                        grow_params = str(step[curr_step_name][0])
                    elif len(step[curr_step_name]) > 1:
                        grow_params = str(step[curr_step_name][0])
                        for i in range(1, len(step[curr_step_name])):
                            # Check whether layer is included in XSection
                            if step[curr_step_name][i] in self.layer_sequence:
                                # Check whether temporary layer object exists
                                if ("x_"+str(step[curr_step_name][i])) in layer_objs:
                                    grow_params = grow_params + "," + " :into => x_" + str(step[curr_step_name][i])
                                else:
                                    print("ERROR-GROW: layer object not available")
                            else:
                                grow_params = grow_params + "," + str(step[curr_step_name][i])
                    
                    # If layer_obj already exists, "OR" with previous layer definition
                    layer_obj = "x_" + layer_name
                    if layer_obj in layer_objs:
                        self.write_line("{} = {}.or(mask({}).grow({}))".format(layer_obj, layer_obj, layer_name_r, grow_params))
                    else:
                        self.write_line("{} = mask({}).grow({})".format(layer_obj, layer_name_r, grow_params))
                        layer_objs.append(layer_obj)
                    
                # Output
                if curr_step_name == "output":
                    layer_obj = "x_" + str(step[curr_step_name])
                    if layer_obj in layer_objs:
                        self.write_line("output(\"{}\", {})\n".format(self.layer_sources[str(step[curr_step_name])], layer_obj))
                    else:
                        print("ERROR-OUTPUT: layer object not available")


    def write_line(self, line):
        """Append a single line of code to 'self.xs_file'

        Parameters
        ----------
        line : str
            A single line of XSection code.

        Returns
        -------
        None

        """
        self.xs_file = self.xs_file + "\n" + line

    def write_lines(self, lines):
        """Append multiple lines of code to 'self.xs_file'
        
        Parameters
        ----------
        lines : list of str
            Multiple lines of XSection code.

        Returns
        -------
        None

        """
        for line in lines:
            self.xs_file = self.xs_file + "\n" + line


    def convert_layer_name(self, layer_name):
        """Convert layer name to a Ruby variable name
        
        Replaces spaces with underscores. Cannot handle plus signs or dashes.
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
        return layer_name

