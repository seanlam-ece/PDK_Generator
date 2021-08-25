#Parser function for YAML + Export function for GDS

try:
    import yaml
except:
    import pip
    pip.main(['install', 'yaml'])
    import yaml

try:
    import pandas as pd
except:
    import pip
    pip.main(['install', 'pandas'])
    import pandas as pd
    
try:
    import pya
except:
    import pip
    pip.main(['install', 'klayout'])
    import pya

class parse:
    
    def extract_YAML(self,datafile):
        """
        Function that parses YAML file and stores into a panda dataframe

        Parameters
        ----------
        datafile : yaml file
            Design intent YAML file 

        Returns
        -------
        panda dataframe
            Dataframe that organizes information on the Design Intent YAML

        """
        with open (datafile, 'r') as yaml_datafile: 
            #Load as python object 
            yaml_datafile = yaml.load(yaml_datafile, Loader=yaml.FullLoader)
            #Organize by layers
            self.df = pd.json_normalize(yaml_datafile)
            self.df.to_csv('test.csv')
            return self.df
        
        
class exports():
    def export_klayout(points, layer = [1,0]):
        # this method creates a OAS layout file for a given PCell using klayout pya library
        ly = pya.Layout()
        # create pcell
        top = ly.create_cell("Y Branch")
        # define layer
        l1 = ly.layer(layer[0], layer[1])
        
        shape = []
        for x in points:
            shape.append(x)

        pts = [pya.DPoint(i[0]/0.0000001,i[1]/0.0000001) for i in shape]
        poly = pya.DPolygon(pts); poly.new(pts)  

        top.shapes(l1).insert(poly)
        ly.write('y_branch_3D.gds')

        return ly
    
