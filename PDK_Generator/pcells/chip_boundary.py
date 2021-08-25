from . import *

class chip_boundary(pya.PCellDeclarationHelper):

  def __init__(self):
    # Important: initialize the super class
    super(chip_boundary, self).__init__()
    # declare the parameters
    TECHNOLOGY = get_technology_by_name('{orig-techname}')
    TECHDRC = DRC(drc_yaml_file_location)
    
    # declare design params
    self.param("width", self.TypeDouble, "Width (um)", default = {dx})
    self.param("length", self.TypeDouble, "Length (um)", default = {dy})
    self.cellName="chip_boundary"
    
    # declare layer params
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['{{Layer}FloorPlan}'], hidden = True)
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "%s_w=%s_l=%s" % (self.cellName, self.width, self.length)
  
  def coerce_parameters_impl(self):
    pass
        
  def produce_impl(self):

    from SiEPIC.utils import  angle_vector
    from math import cos, sin, pi, sqrt
    import pya
    from SiEPIC.extend import to_itype
    
    # fetch params
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerFloorPlanN = ly.layer(self.layer)
    
    chip_bounds = Box(0, 0, to_itype(self.width, dbu), to_itype(self.length, dbu))
    shapes(LayerFloorPlanN).insert(chip_bounds)

