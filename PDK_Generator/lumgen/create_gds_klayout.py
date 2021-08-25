import pya
import json

from SiEPIC.extend import to_itype
from SiEPIC.utils import get_library_names, get_layout_variables

# Variables to be declared over cmd line
# - techname
# - libname
# - pcellname
# - out_dir
# - params

#'''
#SAMPLE TEST CODE
#
#techname = "EBeam"
#libname = "EBeam"
#pcellname = "Waveguide"
#out_dir = r"C:\Users\seanl\Downloads\test2.gds"
#'''

params = json.loads(params)

if "path" in params:
    points = []
    for point in params.get("path",[[]]):
        points.append(DPoint(point[0],point[1]))
    params["path"] = DPath(points, 0.5)

 # Layout functions
def insertCell(parent_cell, child_cell, x, y, rotation=0):
  ''' Insert cell into layout
  
  child_cell: cell
    Cell object that represents the cell to place in layout
  x: float
    absolute x coordinate of center of cell in um
  y: float
    absolute y coordinate of center of cell in um
  rotation: float
    angle in degrees
  '''
  t = pya.Trans.from_s('r{} {},{}'.format(rotation, to_itype(x,dbu), to_itype(y,dbu)))
  return parent_cell.insert(pya.CellInstArray(child_cell.cell_index(), t))
  

# Check technology and library names are valid
technames = pya.Technology().technology_names()
if techname not in technames:
    exception_str = "Cannot find '{}' in KLayout's technology database.\nAvailable technologies are:\n".format(techname)
    for n in technames:
        exception_str = exception_str + " - '" + n + "'\n"
    raise Exception(exception_str)

libnames = get_library_names(techname)
if libname not in libnames:
    exception_str = "Cannot find '{}' in KLayout's library database.\nAvailable libraries are:\n".format(libname)
    for n in libnames:
        exception_str = exception_str + " - '" + n + "'\n"
    raise Exception(exception_str)


# Create layout in specified technology
ly = pya.Application.instance().main_window().create_layout(techname, 1).layout()
cv = pya.Application.instance().main_window().current_view().active_cellview()

# Set up top cell
topcell = ly.create_cell("TOP")
cv.cell_name = "TOP"

# Set up tools       
TECH, lv, ly, cell = get_layout_variables()
dbu = ly.dbu
create_cell = ly.create_cell
shapes = cell.shapes

# Create cell and insert into layout
c1 = create_cell(pcellname, libname,params)
if c1 == None:
    raise Exception("Cannot find '{}' in '{}' library.\nCheck whether the cell is in the library.".format(pcellname, libname))

cInst = insertCell(cell, c1,0,0)

# Create chip boundary
try:
    c2 = create_cell("chip_boundary", libname, {})
    if c2 == None:
        raise Exception("Cannot find chip_boundary PCell in {} library.\nCheck whether cell is in the library.".format(libname))
    
    cInst1 = insertCell(cell, c2, -c2.bbox().width()/2*dbu, -c2.bbox().height()/2*dbu)
except:
    print("No chip_boundary PCell in {} library. Passing...".format(libname))
    pass

# Write to output GDS
ly.write(out_dir)