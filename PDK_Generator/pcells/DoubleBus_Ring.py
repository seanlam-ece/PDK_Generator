from . import *

def layout_pgtext(cell, layer, x, y, text, mag):
    # example usage:
    # cell = Application.instance().main_window().current_view().active_cellview().cell
    # layout_pgtext(cell, LayerInfo(10, 0), 0, 0, "test", 1)

    # for the Text polygon:
    textlib = Library.library_by_name("Basic")
    if textlib == None:
      raise Exception("Unknown lib 'Basic'")

    textpcell_decl = textlib.layout().pcell_declaration("TEXT");
    if textpcell_decl == None:
      raise Exception("Unknown PCell 'TEXT'")
    param = { 
      "text": text, 
      "layer": layer, 
      "mag": mag 
    }
    pv = []
    for p in textpcell_decl.get_parameters():
      if p.name in param:
        pv.append(param[p.name])
      else:
        pv.append(p.default)
    # "fake PCell code" 
    text_cell = cell.layout().create_cell("Temp_text_cell")
    textlayer_index = cell.layout().layer(layer)
    textpcell_decl.produce(cell.layout(), [ textlayer_index ], pv, text_cell)

    # fetch the database parameters
    dbu = cell.layout().dbu
    t = Trans(Trans.R0, x/dbu, y/dbu)
    cell.insert(CellInstArray(text_cell.cell_index(), t))
    # flatten and delete polygon text cell
    cell.flatten(True)

    print("Done layout_pgtext")


def layout_Ring(cell, layer, x, y, r, w, npoints):
    # function to produce the layout of a ring resonator
    # cell: layout cell to place the layout
    # layer: which layer to use
    # x, y: location of the origin
    # r: radius
    # w: waveguide width
    # units in microns

    # example usage.  Places the ring layout in the presently selected cell.
    # cell = Application.instance().main_window().current_view().active_cellview().cell
    # layout_Ring(cell, cell.layout().layer(TECHNOLOGY['Si']), 0, 0, 10, 0.5, 400)


    # fetch the database parameters
    dbu = cell.layout().dbu
    
    # compute the circle
    pts = []
    da = math.pi * 2 / npoints
    for i in range(0, npoints+1):
      pts.append(Point.from_dpoint(DPoint((x+(r+w/2)*math.cos(i*da))/dbu, (y+(r+w/2)*math.sin(i*da))/dbu)))
    for i in range(npoints, -1, -1):
      pts.append(Point.from_dpoint(DPoint((x+(r-w/2)*math.cos(i*da))/dbu, (y+(r-w/2)*math.sin(i*da))/dbu)))
    
    # create the shape
    cell.shapes(layer).insert(Polygon(pts))

    # end of layout_Ring

class DoubleBus_Ring(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the double bus ring resonator.
  Consists of a ring with 2 straight waveguides.
  """

  def __init__(self):

    # Important: initialize the super class
    super(DoubleBus_Ring, self).__init__()
    TECHNOLOGY = get_technology_by_name('{orig-techname}')

    # declare the parameters
    self.param("s", self.TypeShape, "", default = DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = {radius})
    self.param("w", self.TypeDouble, "Waveguide Width", default = {width})
    self.param("g", self.TypeDouble, "Gap", default = {gap})
    self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default = {text-polygon})
    
    # declare layer params
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['{{Layer}Waveguide}'], hidden = True)
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['{{Layer}Text}'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['{{Layer}PinRec}'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['{{Layer}DevRec}'], hidden = True)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "DoubleBus_Ring(R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ")"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerSi = self.silayer
    LayerSiN = ly.layer(LayerSi)
    TextLayerN = ly.layer(self.textl)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    from SiEPIC.utils import points_per_circle
    
    # Create the ring resonator:
    layout_Ring(self.cell, LayerSiN, self.r+self.w/2, self.r+self.g+self.w, self.r, self.w, points_per_circle(self.r))

    w = int(round(self.w/dbu))
    r = int(round(self.r/dbu))
    g = int(round(self.g/dbu))

 #   pcell = ly.create_cell("DirectionalCoupler_HalfRing_Straight", "SiEPIC", { "r": self.r, "w": self.w, "g": self.g, "silayer": LayerSi, "bustype": 0 } )
 #   print ("Cell: pcell: #%s" % pcell.cell_index())
 #   t = Trans(Trans.R0, 0, 0) 
 #   instance = self.cell.insert(CellInstArray(pcell.cell_index(), t))
 #   t = Trans(Trans.R180, 0, 2*r+2*g+2*w) 
 #   instance = self.cell.insert(CellInstArray(pcell.cell_index(), t))


    # Create the two waveguides
    wg1 = Box(0, -w/2, w+2*r, w/2)
    shapes(LayerSiN).insert(wg1)
    y_offset = 2*r + 2*g + 2*w
    wg2 = Box(0, y_offset-w/2, w+2*r, y_offset+w/2)
    shapes(LayerSiN).insert(wg2)

    from SiEPIC._globals import PIN_LENGTH as pin_length
    # Create the pins, as short paths:
    
    pin = Path([Point(pin_length/2, 0), Point(-pin_length/2, 0)], w)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, 0, 0)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    pin = Path([Point(w+2*r-pin_length/2, 0), Point(w+2*r+pin_length/2, 0)],w )
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, w+2*r, 0)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    pin = Path([Point(pin_length/2, y_offset), Point(-pin_length/2, y_offset)], w)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, 0, y_offset)
    text = Text ("pin3", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    pin = Path([Point(w+2*r-pin_length/2, y_offset), Point(w+2*r+pin_length/2, y_offset)], w)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, w+2*r, y_offset)
    text = Text ("pin4", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu


    # Create the device recognition layer
    dev = Box(0, -w*3, w+2*r, y_offset+w*3 )
    shapes(LayerDevRecN).insert(dev)


    # Add a polygon text description
    if self.textpolygon:
      layout_pgtext(self.cell, self.textl, self.w, self.r+self.w, "%.3f-%g" % ( self.r, self.g), 1)

    print("Done drawing the layout for - DoubleBus_Ring: %.3f-%g" % ( self.r, self.g) )

