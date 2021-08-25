from . import *

class ebeam_taper_strip_rib(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the strip waveguide taper.
  """

  def __init__(self):

    # Important: initialize the super class
    super(ebeam_taper_strip_rib, self).__init__()
    TECHNOLOGY = get_technology_by_name('{orig-techname}')

    # declare the parameters
    self.param("rib_wg_width1", self.TypeDouble, "Rib Waveguide Width 1", default = {rib-wg-width1})
    self.param("rib_wg_width2", self.TypeDouble, "Rib Waveguide Width 2", default = {rib-wg-width2})
    self.param("strip_wg_width", self.TypeDouble, "Strip Waveguide Width", default = {strip-wg-width})
    self.param("wg_length", self.TypeDouble, "Waveguide Length", default = {wg-length})
    # declare layer params
    self.param("si220layer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['{{Layer}Waveguide}'], hidden = True)
    self.param("si90layer", self.TypeLayer, "Si slab Layer", default = TECHNOLOGY['{{Layer}Waveguide Partial (Slab)}'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['{{Layer}PinRec}'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['{{Layer}DevRec}'], hidden = True)
    # hidden parameters, can be used to query this component:
    self.param("p1", self.TypeShape, "DPoint location of pin1", default = Point(-10000, 0), hidden = True, readonly = True)
    self.param("p2", self.TypeShape, "DPoint location of pin2", default = Point(0, 10000), hidden = True, readonly = True)
    

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "ebeam_taper_strip_rib(R=" + ('%.3f-%.3f-%.3f-%.3f' % (self.rib_wg_width1,self.rib_wg_width2,self.strip_wg_width,self.wg_length) ) + ")"

  def can_create_from_shape_impl(self):
    return False


  def produce(self, layout, layers, parameters, cell):
    """
    coerce parameters (make consistent)
    """
    self._layers = layers
    self.cell = cell
    self._param_values = parameters
    self.layout = layout
    shapes = self.cell.shapes


    # cell: layout cell to place the layout
    # LayerSiN: which layer to use
    # w: waveguide width
    # length units in dbu

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    
    LayerSi = self.si220layer
    LayerSiN = self.si220layer_layer
    LayerSi90 = self.si90layer
    LayerSi90N = self.si90layer_layer
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    
    w1 = int(round(self.rib_wg_width1/dbu))
    w2 = int(round(self.rib_wg_width2/dbu))
    w3 = int(round(self.strip_wg_width/dbu))
    length = int(round(self.wg_length/dbu))

    pts_rib = [Point(0,-w1/2), Point(0,w1/2), Point(length,w2/2), Point(length,-w2/2)]
    shapes(LayerSi90N).insert(Polygon(pts_rib))
    
    pts_strip = [Point(0,-w3/2), Point(0,w3/2), Point(length,w3/2), Point(length,-w3/2)]
    shapes(LayerSiN).insert(Polygon(pts_strip))
    
    
    # Create the pins on the waveguides, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    
    # Pin on the left side:
    p1 = [Point(pin_length/2,0), Point(-pin_length/2,0)]
    p1c = Point(0,0)
    self.set_p1 = p1c
    self.p1 = p1c
    pin = Path(p1, w1)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, 0, 0)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Pin on the right side:
    p2 = [Point(length-pin_length/2,0), Point(length+pin_length/2,0)]
    p2c = Point(length, 0)
    self.set_p2 = p2c
    self.p2 = p2c
    pin = Path(p2, w2)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, length, 0)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 2

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    path = Path([Point(0,0),Point(length,0)],w2+w1*2)
    shapes(LayerDevRecN).insert(path.simple_polygon())

    return "ebeam_taper_strip_rib(R=" + ('%.3f-%.3f-%.3f-%.3f' % (self.rib_wg_width1,self.rib_wg_width2,self.strip_wg_width,self.wg_length) ) + ")"

