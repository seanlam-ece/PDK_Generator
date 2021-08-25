from . import *

class mmi_2x2(pya.PCellDeclarationHelper):
  """
  """

  def __init__(self):

    # Important: initialize the super class
    super(mmi_2x2, self).__init__()
    TECHNOLOGY = get_technology_by_name('{orig-techname}')

    # declare the parameters
    self.param("w", self.TypeDouble, "Waveguide Width", default = {waveguide-io-width})
    self.param("w_mmi", self.TypeDouble, "Waveguide Width", default = {waveguide-mmi-width})
    self.param("w_a", self.TypeDouble, "Access waveguide Width", default = {waveguide-access-width})
    self.param("L_mmi", self.TypeDouble, "MMI Length", default = {mmi-length})
    self.param("L_a", self.TypeDouble, "Access waveguide Length", default = {waveguide-access-length})

    # declare layer params
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['{{Layer}Waveguide}'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['{{Layer}PinRec}'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['{{Layer}DevRec}'], hidden = True)
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['{{Layer}Text}'], hidden = True)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "mmi_2x2"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    from math import pi, cos, sin

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerSi = self.silayer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    TextLayerN = ly.layer(self.textl)

    
    w = int(round(self.w/dbu))
    w_mmi = int(round(self.w_mmi/dbu))
    w_a = int(round(self.w_a/dbu))
    L_mmi = int(round(self.L_mmi/dbu))
    L_a = int(round(self.L_a/dbu))

    # Create the MMI
    mmi = Box(-L_mmi/2, -w_mmi/2, L_mmi/2, w_mmi/2)
    shapes(LayerSiN).insert(mmi)

    # Draw taper access waveguides
    # Create a sub-cell
    cell = self.cell.layout().create_cell("MMI_access_waveguide")
    pts = []
    pts.append(Point.from_dpoint(DPoint(0, w_a/2)))
    pts.append(Point.from_dpoint(DPoint(L_a, w/2)))
    pts.append(Point.from_dpoint(DPoint(L_a, -w/2)))
    pts.append(Point.from_dpoint(DPoint(0, -w_a/2)))
    polygon = Polygon(pts)
    cell.shapes(LayerSiN).insert(polygon)
    # place the cell in the top cell
    self.cell.insert(CellInstArray(cell.cell_index(), Trans(Trans.R0, L_mmi/2, w_a)))
    self.cell.insert(CellInstArray(cell.cell_index(), Trans(Trans.R0, L_mmi/2, -w_a)))
    self.cell.insert(CellInstArray(cell.cell_index(), Trans(Trans.R180, -L_mmi/2, w_a)))
    self.cell.insert(CellInstArray(cell.cell_index(), Trans(Trans.R180, -L_mmi/2, -w_a)))


    pin(500,"pin1", Trans(Trans.R180, -L_mmi/2-L_a, w_a), LayerPinRecN, dbu, self.cell)
    pin(500,"pin2", Trans(Trans.R180, -L_mmi/2-L_a, -w_a), LayerPinRecN, dbu, self.cell)
    pin(500,"pin3", Trans(Trans.R0, L_mmi/2+L_a, w_a), LayerPinRecN, dbu, self.cell)
    pin(500,"pin4", Trans(Trans.R0, L_mmi/2+L_a, -w_a), LayerPinRecN, dbu, self.cell)

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    dev = Box(-L_mmi/2-L_a, w_mmi/2+w, L_mmi/2+L_a, -w_mmi/2-w )
    shapes(LayerDevRecN).insert(dev)

    print("Done drawing the layout for - mmi" )

