from . import *

class ebeam_irph_wg(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the IRPH straight waveguide.
  
  Authors: Jaspreet Jhoja, Lukas Chrostowski
  """

  def __init__(self):

    # Important: initialize the super class
    super(ebeam_irph_wg, self).__init__()
    TECHNOLOGY = get_technology_by_name('{orig-techname}')

    # declare the parameters
    self.param("w", self.TypeDouble, "Waveguide Width", default = {Waveguide-Width})
    self.param("w_rib", self.TypeDouble, "Waveguide Rib Width", default = {Waveguide-Rib-Width})
    self.param("length", self.TypeDouble, "Waveguide length", default = {Waveguide-Length})
    self.param("n_w", self.TypeDouble, "N Width", default = {N-Width})
    self.param("npp_w", self.TypeDouble, "N++ Width (um)", default = {Npp-Width})
    self.param("npp_dw", self.TypeDouble, "N++ Edge to Si Edge (um)", default = {Npp-Si-Separation})
    self.param("vc_dw", self.TypeDouble, "VC Edge to Si Edge (um)", default = {VC-Si-Separation})
    self.param("vc_w", self.TypeDouble, "VC Width", default = {VC-Width})
    self.param("m_dw", self.TypeDouble, "Metal edge to Si Edge (um)", default = {Metal-Si-Separation})
    self.param("m_w", self.TypeDouble, "Metal Width", default = {Metal-Width})
    self.param("overlay", self.TypeDouble, "Overlay accuracy (optical litho) (um)", default = {Overlay-OL})
    self.param("overlay_ebl", self.TypeDouble, "Overlay accuracy (EBL) (um)", default = {Overlay-EBL})
    
    # declare layer params
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['{{Layer}Waveguide}'], hidden = True)
    self.param("siriblayer", self.TypeLayer, "Si rib Layer", default = TECHNOLOGY['{{Layer}Waveguide Partial (Rib)}'], hidden = True)
    self.param("nlayer", self.TypeLayer, "N Layer", default = TECHNOLOGY['{{Layer}N Dope}'], hidden = True)
    self.param("npplayer", self.TypeLayer, "N++ Layer", default = TECHNOLOGY['{{Layer}N++ Dope}'], hidden = True)
    self.param("vclayer", self.TypeLayer, "VC Layer", default = TECHNOLOGY['{{Layer}Via (VC)}'], hidden = True)
    self.param("mlayer", self.TypeLayer, "Metal Layer", default = TECHNOLOGY['{{Layer}Metal (M2)}'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['{{Layer}PinRec}'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['{{Layer}DevRec}'], hidden = True)
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['{{Layer}Text}'], hidden = True)

    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "ebeam_irph_wg" # (R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ")"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    from math import pi, cos, sin
    from SiEPIC.utils import arc_wg, arc_wg_xy
    from SiEPIC._globals import PIN_LENGTH
    from SiEPIC.extend import to_itype

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerSiN = ly.layer(self.silayer)
    LayerSiRibN = ly.layer(self.siriblayer)
    LayerNN = ly.layer(self.nlayer)
    LayerNPPN = ly.layer(self.npplayer)
    LayerVCN = ly.layer(self.vclayer)
    LayerMN = ly.layer(self.mlayer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    TextLayerN = ly.layer(self.textl)

    w = to_itype(self.w,dbu)
    w_rib = to_itype(self.w_rib,dbu)
    length = to_itype(self.length,dbu)
    n_w = to_itype(self.n_w,dbu)
    npp_w=to_itype(self.npp_w,dbu)
    npp_dw=to_itype(self.npp_dw,dbu)
    vc_w = to_itype(self.vc_w,dbu)
    vc_dw = to_itype(self.vc_dw,dbu)
    m_dw = to_itype(self.m_dw,dbu)
    m_w = to_itype(self.m_w,dbu)
    overlay = to_itype(self.overlay, dbu)
    
    #draw the waveguide
    xtop = 0
    ytop = -1*(w/2)
    xbottom = length
    ybottom = 1*(w/2)
    wg1 = Box(0, -w/2, length, w/2)
    shapes(LayerSiN).insert(wg1)

    # Pins on the bottom waveguide side:    
    pin = Path([Point(xtop+PIN_LENGTH/2, 0), Point(xtop-PIN_LENGTH/2, 0)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin1", Trans(Trans.R0, xtop, 0))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      

    pin = Path([Point(xbottom-PIN_LENGTH/2, 0), Point(xbottom+PIN_LENGTH/2, 0)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin2", Trans(Trans.R0, xbottom, 0))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      
  
    #draw N
    b = Box(0, -n_w/2, length, n_w/2)
    shapes(LayerNN).insert(b)
    
    #draw NPP
    b = Box(0, npp_dw+w/2, length, npp_dw+w/2+npp_w)
    shapes(LayerNPPN).insert(b)
    b = Box(0, -npp_dw-w/2, length, -npp_dw-w/2-npp_w)
    shapes(LayerNPPN).insert(b)

    #draw via
    b = Box(overlay, vc_dw+w/2, length-overlay, vc_dw+w/2+vc_w)
    shapes(LayerVCN).insert(b)
    b = Box(overlay, -vc_dw-w/2, length-overlay, -vc_dw-w/2-vc_w)
    shapes(LayerVCN).insert(b)
    
    #draw metal
    b = Box(0, m_dw+w/2, length, m_dw+w/2+m_w)
    shapes(LayerMN).insert(b)
    b = Box(0, -m_dw-w/2, length, -m_dw-w/2-m_w)
    shapes(LayerMN).insert(b)

    w_devrec = 2 * max(m_dw+m_w+w/2, vc_dw+w/2+vc_w, npp_dw+w/2+npp_w, w_rib/2)

    #devrec layer
    b = Box(0, w_devrec/2+w, length, -w_devrec/2-w)
    shapes(LayerDevRecN).insert(b)

    # Si rib layer
    b = Box(0, w_rib/2, length, -w_rib/2)
    shapes(LayerSiRibN).insert(b)
    
    # Compact model information
    t = Trans(Trans.R0, 0, -w)
    text = Text ("Lumerical_INTERCONNECT_library=Design kits/{orig-techname}", t)
    shape = shapes(LayerDevRecN).insert(text)
    #shape.text_size = self.r*0.07/dbu
    t = Trans(Trans.R0, 0,0)
    text = Text ('Component={cm-name}', t)
    shape = shapes(LayerDevRecN).insert(text)
    # shape.text_size = self.r*0.07/dbu
    
#    print("Done drawing the layout for - ebeam_irph_wg: %.3f-%g" % ( self.r, self.g))
    
