'''
Parses DRC YAML for params
'''

import yaml
import os
import sys

drc_yaml_file_location = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "{drc_yaml_file_name}")


r'''
DRC Class
-----------
yaml_file_path - File path to DRC YAML file (i.e. C:\Users\username\KLayout\tech\my_tech\my_tech_DRC.yaml)

Methods:
    get_layer_names()
        Returns a list of layer names in the DRC YAML file
        
    get_layer_source(layer_name)
        Returns a string representing the layer source (i.e. "1/0" for layer number 1, datatype 0)
        
    get_layer_mask(layer_name)
        Returns a string representing the layer mask (i.e. "negative" or "positive")
        
    get_layer_min_feature_size(layer_name)
        Returns a float representing the min feature size on the layer (i.e. 3.0)
    
    get_layer_min_spacing(layer_name)
        Returns a float representing the min spacing on the layer (i.e. 2.0)
        
    get_layer_min_overlap(layer1_name, layer2_name)
        Returns a float representing layer1 overlapping layer2 by this amount.
        
    get_layer_min_enclosure(layer1_name, layer2_name)
        Returns a float representing layer1 enclosing layer2 by this amount.
        
    get_layer_min_exlusion(layer1_name, layer2_name)
        Returns a float representing layer1 separated by layer2 by this amount, vice versa.

'''
class DRC():
    
    def __init__(self, yaml_file_path):
        self.get_DRC_params(yaml_file_path)
            
    def get_DRC_params(self, filepath):
        try:
            with open(filepath) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist at {}... Cannot obtain DRC params... Passing...".format(filepath))
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain DRC params... Passing...")
            return
        
        self.data = data
        
        # Parse and populate appropriate layer parameters
        layer_sources = {}
        layer_masks = {}
        layer_min_feature_sizes = {}
        layer_min_spacings = {}
        layer_min_overlaps = {}
        layer_min_enclosures = {}
        layer_min_exclusions = {}

        for layer_name, params in data.items():
            if type(params) == dict:
                if data[layer_name].get('source', None):
                    layer_sources.update({layer_name: data[layer_name]['source']})
                if data[layer_name].get('mask', None) != None:
                    layer_masks.update({layer_name: data[layer_name]['mask']})
                if data[layer_name].get('min-feature-size', None) != None:
                    layer_min_feature_sizes.update({layer_name: data[layer_name]['min-feature-size']})
                if data[layer_name].get('min-spacing', None) != None:
                    layer_min_spacings.update({layer_name: data[layer_name]['min-spacing']})
                if data[layer_name].get('min-overlap', None) != None:
                    layer_min_overlaps.update({layer_name: data[layer_name]['min-overlap']})
                if data[layer_name].get('min-enclosing', None) != None:
                    layer_min_enclosures.update({layer_name: data[layer_name]['min-enclosing']})
                if data[layer_name].get('min-exclusion', None) != None:
                    layer_min_exclusions.update({layer_name: data[layer_name]['min-exclusion']})

        # Save layer params as class variables
        self.layer_sources = layer_sources
        self.layer_masks = layer_masks
        self.layer_min_feature_sizes = layer_min_feature_sizes
        self.layer_min_spacings = layer_min_spacings
        self.layer_min_overlaps = layer_min_overlaps
        self.layer_min_enclosures = layer_min_enclosures
        self.layer_min_exclusions = layer_min_exclusions
        self.layer_names = list(layer_sources.keys())
        
    def get_layer_names(self):
        return self.layer_names
    
    def get_layer_source(self, layer_name):
        try:
            return self.layer_sources[layer_name]
        except KeyError:
            names = list(self.layer_sources.keys())[0]
            for name in list(self.layer_sources.keys()):
                names += ", " + name
            raise KeyError("{} is not a valid layer that has a layer source. "\
                  "Available layers with sources are: {}".format(layer_name, names)) from None
            return None
    
    def get_layer_mask(self, layer_name):
        try:
            return self.layer_masks[layer_name]
        except KeyError:
            names = list(self.layer_masks.keys())[0]
            for name in list(self.layer_masks.keys()):
                names += ", " + name
            raise KeyError("{} is not a valid layer that has a layer mask. "\
                  "Available layers with masks are: {}".format(layer_name, names)) from None
            return None
    
    def get_layer_min_feature_size(self, layer_name):
        try:
            return self.layer_min_feature_sizes[layer_name]
        except KeyError:
            names = list(self.layer_min_feature_sizes.keys())[0]
            for name in list(self.layer_min_feature_sizes.keys()):
                names += ", " + name
            raise KeyError("{} is not a valid layer that has a min feature size. "\
                  "Available layers with min feature sizes are: {}".format(layer_name, names)) from None
            return None
    
    def get_layer_min_spacing(self, layer_name):
        try:
            return self.layer_min_spacings[layer_name]
        except KeyError:
            names = list(self.layer_min_spacings.keys())[0]
            for name in list(self.layer_min_spacings.keys()):
                names += ", " + name
            raise KeyError("{} is not a valid layer that has a min spacing. "\
                  "Available layers with min spacings are: {}".format(layer_name, names)) from None
            return None
    
    def get_layer_min_overlap(self, layer1_name, layer2_name):
        try:
            return self.layer_min_overlaps[layer1_name][layer2_name]
        except KeyError:
            if self.layer_min_overlaps.get(layer2_name, {}).get(layer1_name, None):
                raise KeyError("{l1} (L1) does not overlap {l2} (L2). Did you mean {l2} (L2) overlaps {l1} (L1)?".format(l1=layer1_name, l2=layer2_name)) from None
            elif self.layer_min_overlaps.get(layer1_name, None):
                raise KeyError("{l2} (L2) is an invalid layer and does not have a min overlap param with {l1} (L1).".format(l1=layer1_name, l2=layer2_name)) from None
            else:
                raise KeyError("{} (L1) is an invalid layer that does not have a min overlap param.".format(layer1_name)) from None
                
    def get_layer_min_enclosure(self, layer1_name, layer2_name):
        try:
            return self.layer_min_enclosures[layer1_name][layer2_name]
        except KeyError:
            if self.layer_min_enclosures.get(layer2_name, {}).get(layer1_name, None):
                raise KeyError("{l1} (L1) does not enclose {l2} (L2). Did you mean {l2} (L2) encloses {l1} (L1)?".format(l1=layer1_name, l2=layer2_name)) from None
            elif self.layer_min_enclosures.get(layer1_name, None):
                raise KeyError("{l2} (L2) is an invalid layer and does not have a min enclosing param with {l1} (L1).".format(l1=layer1_name, l2=layer2_name)) from None
            else:
                raise KeyError("{} (L1) is an invalid layer that does not have a min enclosing param.".format(layer1_name)) from None
    
    def get_layer_min_exlusion(self, layer1_name, layer2_name):
        try:
            return self.layer_min_exclusions[layer1_name][layer2_name]
        except KeyError:
            if self.layer_min_exclusions.get(layer2_name, {}).get(layer1_name, None):
                return self.layer_min_exclusions[layer2_name][layer1_name]
            elif self.layer_min_exclusions.get(layer1_name, None):
                raise KeyError("{l2} (L2) is an invalid layer and does not have a min exclusion param with {l1} (L1).".format(l1=layer1_name, l2=layer2_name)) from None
            else:
                raise KeyError("{} (L1) is an invalid layer that does not have a min exclusion param.".format(layer1_name)) from None

{function_techname}_DRC=DRC(drc_yaml_file_location)