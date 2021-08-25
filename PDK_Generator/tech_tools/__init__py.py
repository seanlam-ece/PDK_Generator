#################################################################################
#                Tech Tools                                                     #
#################################################################################

'''
Author: Sean Lam
Contact: seanlm@student.ubc.ca
'''

import os, sys
from pathlib import Path
import SiEPIC
import math
try: 
  import siepic_tools
except:
  pass

op_tag = "" #operation tag which defines whether we are loading library in script or GUI env

try:
  # import pya from klayout
  import pya
  if("Application" in str(dir(pya))):
    from SiEPIC.utils import get_technology_by_name, get_technology, arc, arc_xy, arc_wg, arc_to_waveguide, points_per_circle
    from SiEPIC._globals import PIN_LENGTH
    op_tag = "GUI" 
    #import pya functions
  else:
    raise ImportError

except:
  import klayout.db as pya
  from zeropdk import Tech
  op_tag = "script" 
  lyp_filepath = Path(str(Path(os.path.dirname(os.path.realpath(__file__))).parent) + r"/{orig_techname}.lyp")
  print(lyp_filepath)

from pya import Box, Point, Polygon, Text, Trans, LayerInfo, \
    PCellDeclarationHelper, DPoint, DPath, Path, ShapeProcessor, \
    Library, CellInstArray, Region

# package dependancies

try:
    import yaml
except:
    import pip
    pip.main(['install', 'yaml'])
    import yaml
