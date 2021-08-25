from . import *

class ebeam_irph_mrr(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the IRPH MRR.
  
  Author: Jaspreet Jhoja
  jaspreetj@ece.ubc.ca
  """

  def __init__(self):

    # Important: initialize the super class
    super(ebeam_irph_mrr, self).__init__()
    TECHNOLOGY = get_technology_by_name('{orig-techname}')

    # declare the parameters
    self.param("r", self.TypeDouble, "Radius", default = {Radius})
    self.param("w", self.TypeDouble, "Waveguide Width", default = {Waveguide-Width})
    self.param("g", self.TypeDouble, "Gap", default = {Gap})
    
    self.param("n_w", self.TypeDouble, "N Width", default = {N-Width})
    self.param("n_theta_start", self.TypeDouble, "Start Theta", default = {N-Start-Theta})
    self.param("n_theta_stop", self.TypeDouble, "Stop Theta", default = {N-Stop-Theta})
    
    self.param("npp_si", self.TypeDouble, "N++ to Si edge", default = {Npp-Si-Separation})
    self.param("npp_w", self.TypeDouble, "N++ Donut Width", default = {Npp-Donut-Width})
    
    self.param("vc_cw", self.TypeDouble, "VC Center radius", default = {VC-Center-Radius})
    self.param("vc_aw", self.TypeDouble, "VC Arc Width", default = {VC-Arc-Width})

    self.param("m_cw", self.TypeDouble, "Metal Center radius", default = {Metal-Center-Radius})
    self.param("m_aw", self.TypeDouble, "Metal Arc Width", default = {Metal-Arc-Width})
        
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
    return "ebeam_irph_mrr(R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ")"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    from math import pi, cos, sin
    from SiEPIC.utils import arc_wg, arc_wg_xy
    from SiEPIC._globals import PIN_LENGTH
    from SiEPIC.extend import to_itype, to_dtype

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
    r = to_itype(self.r,dbu)
    g = to_itype(self.g,dbu)
    
    n_w = to_itype(self.n_w,dbu)
    npp_si = to_itype(self.npp_si, dbu)
    npp_w=to_itype(self.npp_w,dbu)
    theta_start = self.n_theta_start
    theta_stop = self.n_theta_stop

    vc_cw = to_itype(self.vc_cw,dbu)
    vc_aw = to_itype(self.vc_aw,dbu)
    
    m_cw = to_itype(self.m_cw,dbu)
    m_aw = to_itype(self.m_aw,dbu)
    x = 0
    y = 0
    
    #draw ring
    self.cell.shapes(LayerSiN).insert(arc_wg_xy(x, y, r, w, 0, 360))
        
    #draw bus waveguides  
    #bottom waveguide
    xtop = -2/3*r
    ytop = -1*(r+g+w/2)
    xbottom = 4/3*r
    ybottom = ytop-w
    wg1 = Box(xtop, ytop , xbottom, ybottom)
    shapes(LayerSiN).insert(wg1)
    #left waveguide
    wg1 = Box(ytop, xtop , ybottom, xbottom)
    shapes(LayerSiN).insert(wg1) 

    # Pins on the bottom waveguide side:    
    pin = Path([Point(xtop+PIN_LENGTH, ytop-w/2), Point(xtop-PIN_LENGTH, ytop-w/2)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin1", Trans(Trans.R0, xtop, ytop-w/2))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      

    pin = Path([Point(xbottom-PIN_LENGTH, ytop-w/2), Point(xbottom+PIN_LENGTH, ytop-w/2)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin2", Trans(Trans.R0, xbottom, ytop-w/2))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      
  
    # Pins on the left waveguide side:    
    pin = Path([Point(ytop-w/2, xtop+PIN_LENGTH), Point(ytop-w/2,xtop-PIN_LENGTH)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin3", Trans(Trans.R0,  ytop-w/2,xtop))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      
    
    pin = Path([Point(ybottom+w/2, xbottom-PIN_LENGTH), Point(ybottom+w/2,xbottom+PIN_LENGTH)], w)
    shapes(LayerPinRecN).insert(pin)
    text = Text ("pin4", Trans(Trans.R0,  ybottom+w/2,xbottom))
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu      

    #draw N
    arc_pts = arc_xy(x, y, n_w,  theta_start, theta_stop)
    arc_pts.append(pya.Point.from_dpoint(pya.DPoint(0,0))) #adding center point for polygon
    shapes(LayerNN).insert(pya.Polygon(arc_pts)) 
    
    #draw NPP
    #center
    arc_pts = arc_xy(x, y, r-npp_si-w/2,  0, 360)
    arc_pts.append(pya.Point.from_dpoint(pya.DPoint(0,0))) #adding center point for polygon    
    shapes(LayerNPPN).insert(pya.Polygon(arc_pts)) 
    #outer donut
    shapes(LayerNPPN).insert(arc_wg_xy(x, y,  r+w/2+npp_si+npp_w/2 , npp_w , theta_start, theta_stop))     

    #draw via
     #center
    arc_pts = arc_xy(x, y, vc_cw ,  0, 360)
    arc_pts.append(pya.Point.from_dpoint(pya.DPoint(0,0))) #adding center point for polygon        
    shapes(LayerVCN).insert(pya.Polygon(arc_pts))
     
    #outer donut
    shapes(LayerVCN).insert(arc_wg_xy(x, y,  4/dbu +  r + npp_w/2, vc_aw , theta_start+10, theta_stop-10))     
    
    #draw metal
    #center
    arc_pts = arc_xy(x, y, m_cw ,  0, 360)
    arc_pts.append(pya.Point.from_dpoint(pya.DPoint(0,0))) #adding center point for polygon 
    shapes(LayerMN).insert(pya.Polygon(arc_pts)) 
    #outer donut
    shapes(LayerMN).insert(arc_wg_xy(x, y,  4/dbu +  r + npp_w/2 , m_aw , theta_start, theta_stop))     

    #devrec layer
    xtop = -2/3*r
    ytop = -1*(r+g+w/2)
    xbottom = 4/3*r
    ybottom = ytop
    dev_array = [
        Point(ytop + 4*w,xbottom+npp_w),
        Point(ytop + 4*w,xbottom),
        Point(ytop - 3*w,xbottom),
        Point(ytop - 3*w,xtop),
        Point(ytop + 4*w,xtop),
        Point(xtop,ybottom+4*w),
        Point(xtop,ybottom-3*w),
        Point(xbottom,ybottom-3*w),
        Point(xbottom,ybottom+4*w),
        Point(xbottom+npp_w,ybottom+4*w),
        Point(xbottom+npp_w,xbottom+npp_w) ]
    shapes(LayerDevRecN).insert(pya.Polygon(dev_array)) 

    # Si rib layer
    shapes(LayerSiRibN).insert(pya.Polygon(dev_array))
    
    # Compact model information
    t = Trans(Trans.R0, 0, -w)
    text = Text ("Lumerical_INTERCONNECT_library=Design kits/{orig-techname}", t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = self.r*0.07/dbu
    t = Trans(Trans.R0, 0,0)
    text = Text ('Component={cm-name}', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = self.r*0.07/dbu
    
    print("Done drawing the layout for - ebeam_IRPH_MRR: %.3f-%g" % ( self.r, self.g))
    
