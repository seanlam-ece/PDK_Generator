from . import *



class Ring_Modulator_DB(pya.PCellDeclarationHelper):
  """
  The PCell declaration for ring modulator.
  Consists of a ring with 2 straight waveguides
  With pn junction and heater
  Written by Anthony Park and Wei Shi, 2017
  """
  def __init__(self):
    super(Ring_Modulator_DB, self).__init__()
    # declare the parameters
    TECHNOLOGY = get_technology_by_name('{orig-techname}')
    TECHDRC = DRC(drc_yaml_file_location)
    
    # declare design params
    self.param("s", self.TypeShape, "", default = pya.DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = {radius})
    self.param("w", self.TypeDouble, "Waveguide Width", default = {waveguide-width})
    self.param("g", self.TypeDouble, "Gap", default = {gap})
    self.param("gmon", self.TypeDouble, "Gap Monitor", default = {gap-monitor})
    self.param("component_ID", self.TypeInt, "Component_ID (>0)", default = 0)
    self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default = 1)
    
    # declare layer params
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['{{Layer}Waveguide}'], hidden = True)
    self.param("si3layer", self.TypeLayer, "SiEtch2(Rib) Layer", default = TECHNOLOGY['{{Layer}Waveguide Partial (Rib)}'], hidden = True)
    self.param("nlayer", self.TypeLayer, "N Layer", default = TECHNOLOGY['{{Layer}N Dope}'], hidden = True)
    self.param("nplayer", self.TypeLayer, "N+ Layer", default = TECHNOLOGY['{{Layer}N+ Dope}'], hidden = True)
    self.param("pplayer", self.TypeLayer, "P+ Layer", default = TECHNOLOGY['{{Layer}P+ Dope}'], hidden = True)
    self.param("npplayer", self.TypeLayer, "N++ Layer", default = TECHNOLOGY['{{Layer}N++ Dope}'], hidden = True)
    self.param("ppplayer", self.TypeLayer, "P++ Layer", default = TECHNOLOGY['{{Layer}P++ Dope}'], hidden = True)
    self.param("vclayer", self.TypeLayer, "VC Layer", default = TECHNOLOGY['{{Layer}Via (VC)}'], hidden = True)
    self.param("m1layer", self.TypeLayer, "M1 Layer", default = TECHNOLOGY['{{Layer}Metal (M1)}'], hidden = True)
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['{{Layer}Text}'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['{{Layer}PinRec}'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['{{Layer}DevRec}'], hidden = True)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Ring_Modulator_DB(R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ",gmon=" + ('%g' % (1000*self.gmon)) + ")"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):

    # This is the main part of the implementation: create the layout
    from math import pi, cos, sin
    from SiEPIC.extend import to_itype
    
    # fetch the parameters
#    TECHNOLOGY = get_technology_by_name('{orig-techname}')
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerSi3N = ly.layer(self.si3layer)
    LayerSiN = ly.layer(self.silayer)
    LayernN = ly.layer(self.nlayer)
    LayernpN = ly.layer(self.nplayer)
    LayerppN = ly.layer(self.pplayer)
    LayernppN = ly.layer(self.npplayer)
    LayerpppN = ly.layer(self.ppplayer)
    LayervcN = ly.layer(self.vclayer)
    Layerm1N = ly.layer(self.m1layer)
    TextLayerN = ly.layer(self.textl)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    # Define variables for the Modulator
    # Variables for the Si waveguide
    w = to_itype(self.w,dbu)
    r = to_itype(self.r,dbu)
    g = to_itype(self.g,dbu)
    gmon = to_itype(self.gmon,dbu)
    
    #Variables for the N layer
    w_1 = 2.0/dbu  #same for N, P, N+, P+ layer
    r_n = to_itype(self.r - 1.0,dbu)
    
    #Variables for the P layer
    r_p = to_itype(self.r + 1.0, dbu)
     
    #Variables for the N+layer
    r_np = to_itype(self.r - 1.5,dbu)
    
    #Variables for the P+layer
    r_pp = to_itype(self.r + 1.5,dbu)

    #Variables for the N++ layer
    w_2 = to_itype(5.5,dbu)  #same for N++, P++ layer
    r_npp = to_itype(self.r - 3.75,dbu)

    #Variables for the P+layer
    r_ppp = to_itype(self.r + 3.75,dbu)

    #Variables for the VC layer
    w_vc = to_itype(4.0,dbu)
    r_vc1 = to_itype(self.r - 3.75,dbu)
    r_vc2 = to_itype(self.r + 3.75,dbu)
   
    #Variables for the M1 layer
    w_m1_in = r_vc1 + w_vc/2.0 + to_itype(0.5,dbu)
    r_m1_in = r_vc1 + w_vc/2.0 + to_itype(0.5,dbu) /2.0
    w_m1_out = to_itype(6.0,dbu)
    r_m1_out = to_itype(self.r + 4.25,dbu)
    
    #Variables for the VL layer
    #r_vl =  w_m1_in/2.0 -  2.1/dbu
    r_vl =  r_vc1 - w_vc/2.0 - to_itype(2.01,dbu)
    if r_vl < to_itype(1.42,dbu):
      r_vl = to_itype(1.42,dbu)
      w_vc = r - to_itype(1.75,dbu) - (r_vl + 2.01)
      r_vc1 = r - to_itype(1.75,dbu) - w_vc/2.0
      r_vc2 = r + to_itype(1.75,dbu) + w_vc/2.0
      w_2 = (r-w/2.0 - to_itype(0.75,dbu)) - (r_vc1 - w_vc/2.0 - 0.75) # same for N++, P++ layer
      r_npp = ((r-w/2.0 - to_itype(0.75,dbu)) + (r_vc1 - w_vc/2.0 - 0.75))/2.0
      r_ppp = 2*r - r_npp
    w_via = to_itype(5.0,dbu)
    h_via = to_itype(5.0,dbu)

    # Variables for the SiEtch2 layer  (Slab)
    w_Si3 = round(w_m1_out + 2*(r_m1_out)+ 0/dbu)
    h_Si3 = w_Si3
    taper_bigend =  to_itype(2,dbu)
    taper_smallend =  to_itype(0.3,dbu)
    taper_length =  to_itype(5,dbu)

    #Variables for the MH layer
    w_mh = to_itype(2.0,dbu)
    r_mh = r
    r_mh_in = r_mh - w_mh/2.0
    
    #Define Ring centre   
    x0 = r + w/2
    y0 = r + g + w 

    ######################
    # Generate the layout:
   
    # Create the ring resonator
    t = pya.Trans(pya.Trans.R0,x0, y0)
    pcell = ly.create_cell("Ring", "{libname}", { "layer": self.silayer, "radius": self.r, "width": self.w } )
    self.cell.insert(pya.CellInstArray(pcell.cell_index(), t))

    
    # Create the two waveguides
    wg1 = pya.Box(x0 - (w_Si3 / 2 + taper_length), -w/2, x0 + (w_Si3 / 2 + taper_length), w/2)
    shapes(LayerSiN).insert(wg1)
    y_offset = 2*r + g + gmon + 2*w
    wg2 = pya.Box(x0 - (w_Si3 / 2 + taper_length), y_offset-w/2, x0 + (w_Si3 / 2 + taper_length), y_offset+w/2)
    shapes(LayerSiN).insert(wg2)

    
    #Create the SiEtch2 (Slab) layer
    boxSi3 = pya.Box(x0-w_Si3/2.0, y0 - h_Si3/2.0, x0+w_Si3/2.0, y0 + h_Si3/2.0)
    shapes(LayerSi3N).insert(boxSi3)
    pin1pts = [pya.Point(x0-w_Si3/2.0, -taper_bigend/2.0),
               pya.Point(x0-w_Si3/2.0-taper_length,-taper_smallend/2.0),
               pya.Point(x0-w_Si3/2.0-taper_length,taper_smallend/2.0),
               pya.Point(x0-w_Si3/2.0, taper_bigend/2.0)]
    pin2pts = [pya.Point(x0+w_Si3/2.0,-taper_bigend/2.0),
               pya.Point(x0+w_Si3/2.0+taper_length,-taper_smallend/2.0),
               pya.Point(x0+w_Si3/2.0+taper_length,taper_smallend/2.0),
               pya.Point(x0+w_Si3/2.0,+taper_bigend/2.0)]
    pin3pts = [pya.Point(x0-w_Si3/2.0,y_offset-taper_bigend/2.0),
               pya.Point(x0-w_Si3/2.0-taper_length,y_offset-taper_smallend/2.0),
               pya.Point(x0-w_Si3/2.0-taper_length,y_offset+taper_smallend/2.0),
               pya.Point(x0-w_Si3/2.0,y_offset+ taper_bigend/2.0)]
    pin4pts = [pya.Point(x0+w_Si3/2.0,y_offset-taper_bigend/2.0),
               pya.Point(x0+w_Si3/2.0+taper_length,y_offset-taper_smallend/2.0),
               pya.Point(x0+w_Si3/2.0+taper_length,y_offset+taper_smallend/2.0),
               pya.Point(x0+w_Si3/2.0,y_offset+taper_bigend/2.0)]
    shapes(LayerSi3N).insert(pya.Polygon(pin1pts))
    shapes(LayerSi3N).insert(pya.Polygon(pin2pts))
    shapes(LayerSi3N).insert(pya.Polygon(pin3pts))
    shapes(LayerSi3N).insert(pya.Polygon(pin4pts))
    
    # arc angles
    # doping:
    angle_min_doping = -35
    angle_max_doping = 215
    # VC contact:
    angle_min_VC = angle_min_doping + 8
    angle_max_VC = angle_max_doping - 8
    # M1:
    angle_min_M1 = angle_min_VC - 4
    angle_max_M1 = angle_max_VC + 4
    # MH:
    angle_min_MH = -75.0
    angle_max_MH = 255

    from SiEPIC.utils import arc

    #Create the N Layer
    self.cell.shapes(LayernN).insert(pya.Path(arc(r_n, angle_min_doping, angle_max_doping), w_1).transformed(t).simple_polygon())
    
    #Create the N+ Layer
    self.cell.shapes(LayernpN).insert(pya.Path(arc(r_np, angle_min_doping, angle_max_doping), w_1).transformed(t).simple_polygon())

    #Create the P+ Layer
    self.cell.shapes(LayerppN).insert(pya.Path(arc(r_pp, angle_min_doping, angle_max_doping), w_1).transformed(t).simple_polygon())
    
    #Create the N++ Layer
    self.cell.shapes(LayernppN).insert(pya.Path(arc(r_npp, angle_min_doping, angle_max_doping), w_2).transformed(t).simple_polygon())

    #Create the P+ +Layer
    poly = pya.Path(arc(r_ppp, angle_min_doping, angle_max_doping), w_2).transformed(t).simple_polygon()
    self.cell.shapes(LayerpppN).insert(pya.Region(poly) - pya.Region(pya.Box(x0-r_ppp-w_2/2, y_offset-w/2 - 0.75/dbu, x0+r_ppp+w/2, y_offset+w/2 + 0.75/dbu)))
    
    #Create the VC Layer
    self.cell.shapes(LayervcN).insert(pya.Path(arc(r_vc1, angle_min_VC, angle_max_VC), w_vc).transformed(t).simple_polygon())

    poly = pya.Path(arc(r_vc2, angle_min_VC, angle_max_VC), w_vc).transformed(t).simple_polygon()
    self.cell.shapes(LayervcN).insert(pya.Region(poly) - pya.Region(pya.Box(x0-r_vc2-w_vc/2, y_offset-w/2 - 1.5/dbu, x0+r_vc2+w_vc/2, y_offset+w/2 + 1.5/dbu)))

        
    #Create the M1 Layer
    self.cell.shapes(Layerm1N).insert(pya.Polygon(arc(w_m1_in, angle_min_doping, angle_max_doping) + [pya.Point(0, 0)]).transformed(t))
    self.cell.shapes(Layerm1N).insert(pya.Polygon(arc(w_m1_in/2.0, 0, 360)).transformed(t))
    self.cell.shapes(Layerm1N).insert(pya.Path(arc(r_m1_out, angle_min_M1, angle_max_M1), w_m1_out).transformed(t).simple_polygon())
    boxM11 = pya.Box(x0-w_via, y0 + r_m1_out + w_m1_out-h_via, x0+w_via, y0 + r_m1_out + w_m1_out+h_via)
    shapes(Layerm1N).insert(boxM11)
    
    #Create the VL Layer, as well as the electrical PinRec geometries
    # centre contact (P, anode):
    self.cell.shapes(LayerPinRecN).insert(pya.Polygon(arc(r_vl, 0, 360)).transformed(t))
    shapes(LayerPinRecN).insert(pya.Text ("elec1a", pya.Trans(pya.Trans.R0,x0,y0))).text_size = 0.5/dbu
    shapes(LayerPinRecN).insert(pya.Box(x0-w_via/2, y0-w_via/2, x0+w_via/2, y0+w_via/2))
    
    # top contact (N, cathode):
    boxVL1 = pya.Box(x0-w_via/2, y0 +  r_vc2 +  w_vc/2 + 2.0/dbu, x0+w_via/2, y0 + r_vc2 +  w_vc/2 + 2.0/dbu+ h_via)
    shapes(LayerPinRecN).insert(boxVL1)
    shapes(LayerPinRecN).insert(pya.Text ("elec1c", pya.Trans(pya.Trans.R0,x0,y0 + r_vc2 +  w_vc/2 + 2.0/dbu+ h_via/2))).text_size = 0.5/dbu
    # heater contacts
    boxVL3 = pya.Box(x0+(r_mh_in)*cos(angle_min_MH/180*pi) + 2.5/dbu, -w/2.0 -  10/dbu, x0 + (r_mh_in)*cos(angle_min_MH/180*pi) + 7.5/dbu, -w/2.0 -  5/dbu)
    shapes(LayerPinRecN).insert(boxVL3)
    shapes(LayerPinRecN).insert(pya.Text ("elec2h2", pya.Trans(pya.Trans.R0,x0+(r_mh_in)*cos(angle_min_MH/180*pi) + 5.0/dbu,-w/2.0 -  7.5/dbu))).text_size = 0.5/dbu
    boxVL4 = pya.Box(x0-(r_mh_in)*cos(angle_min_MH/180*pi)- 7.5/dbu, -w/2.0 -  10/dbu, x0 - (r_mh_in)*cos(angle_min_MH/180*pi) - 2.5/dbu, -w/2.0 -  5/dbu)
    shapes(LayerPinRecN).insert(boxVL4)
    shapes(LayerPinRecN).insert(pya.Text ("elec2h1", pya.Trans(pya.Trans.R0,x0-(r_mh_in)*cos(angle_min_MH/180*pi) - 5.0/dbu,-w/2.0 -  7.5/dbu))).text_size = 0.5/dbu

    #Create the MH Layer
    boxMH1 = pya.Box(x0+(r_mh_in)*cos(angle_min_MH/180*pi), -w/2.0 -  2.5/dbu, x0 + (r_mh_in)*cos(angle_min_MH/180*pi) + w_mh, y0 +(r_mh_in)*sin(angle_min_MH/180*pi))
    boxMH2 = pya.Box(x0-(r_mh_in)*cos(angle_min_MH/180*pi)  - w_mh, -w/2.0 -  2.5/dbu, x0 - (r_mh_in)*cos(angle_min_MH/180*pi), y0 +(r_mh_in)*sin(angle_min_MH/180*pi))
    boxMH3 = pya.Box(x0+(r_mh_in)*cos(angle_min_MH/180*pi), -w/2.0 -  12.5/dbu, x0 + (r_mh_in)*cos(angle_min_MH/180*pi) + 10/dbu, -w/2.0 -  2.5/dbu)
    boxMH4 = pya.Box(x0-(r_mh_in)*cos(angle_min_MH/180*pi)- 10/dbu, -w/2.0 -  12.5/dbu, x0 - (r_mh_in)*cos(angle_min_MH/180*pi), -w/2.0 -  2.5/dbu)
    
    # Create the pins, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length
        
    shapes(LayerPinRecN).insert(pya.Path([pya.Point(x0 - (w_Si3 / 2. + taper_length) + pin_length/2., 0),
                                          pya.Point(x0 - (w_Si3 / 2. + taper_length) - pin_length/2., 0)], w))
    shapes(LayerPinRecN).insert(pya.Text("opt1", pya.Trans(pya.Trans.R0,x0 - (w_Si3 / 2. + taper_length), 0))).text_size = 0.5/dbu

    shapes(LayerPinRecN).insert(pya.Path([pya.Point(x0 + (w_Si3 / 2. + taper_length) - pin_length/2., 0),
                                          pya.Point(x0 + (w_Si3 / 2. + taper_length)           + pin_length/2., 0)], w))
    shapes(LayerPinRecN).insert(pya.Text("opt2", pya.Trans(pya.Trans.R0,x0 + (w_Si3 / 2. + taper_length), 0))).text_size = 0.5/dbu

    shapes(LayerPinRecN).insert(pya.Path([pya.Point(x0 - (w_Si3 / 2. + taper_length) + pin_length/2., y_offset),
                                          pya.Point(x0 - (w_Si3 / 2. + taper_length) - pin_length/2., y_offset)], w))
    shapes(LayerPinRecN).insert(pya.Text("opt3", pya.Trans(pya.Trans.R0,x0 - (w_Si3 / 2. + taper_length), y_offset))).text_size = 0.5/dbu

    shapes(LayerPinRecN).insert(pya.Path([pya.Point(x0 + (w_Si3 / 2. + taper_length) - pin_length/2., y_offset),
                                          pya.Point(x0 + (w_Si3 / 2. + taper_length) + pin_length/2., y_offset)], w))
    shapes(LayerPinRecN).insert(pya.Text("opt4", pya.Trans(pya.Trans.R0,x0 + (w_Si3 / 2. + taper_length), y_offset))).text_size = 0.5/dbu

    # Create the device recognition layer
    shapes(LayerDevRecN).insert(pya.Box(x0 - (w_Si3 / 2 + taper_length), -w/2.0 -  12.5/dbu, x0 + (w_Si3 / 2 + taper_length), y0 + r_m1_out + w_m1_out+h_via ))

    # Compact model information
    shape = shapes(LayerDevRecN).insert(pya.Text('Lumerical_INTERCONNECT_library=Design kits/{orig-techname}', \
      pya.Trans(pya.Trans.R0,0, 0))).text_size = 0.3/dbu
    shapes(LayerDevRecN).insert(pya.Text('Component={cm-name}', \
      pya.Trans(pya.Trans.R0,0, w*2))).text_size = 0.3/dbu
    shapes(LayerDevRecN).insert(pya.Text('Component_ID=%s' % self.component_ID, \
      pya.Trans(pya.Trans.R0,0, w*4))).text_size = 0.3/dbu
    shapes(LayerDevRecN).insert(pya.Text \
      ('Spice_param:radius=%.3fu wg_width=%.3fu gap=%.3fu gap_monitor=%.3fu' %\
      (self.r, self.w, self.g, self.gmon), \
      pya.Trans(pya.Trans.R0,0, -w*2) ) ).text_size = 0.3/dbu
    
    # Add a polygon text description
    from SiEPIC.utils import layout_pgtext
    if self.textpolygon : layout_pgtext(self.cell, self.textl, self.w, self.r+self.w, "%.3f-%g" % ( self.r, self.g), 1)

    # Reference publication:
    shapes(TextLayerN).insert(pya.Text ("Ref: Raphael Dube-Demers, JLT, 2015", pya.Trans(pya.Trans.R0,x0 - (w_Si3 / 2 + taper_length), -w/2.0 -  12.5/dbu+4.0/dbu))).text_size = 0.7/dbu
    shapes(TextLayerN).insert(pya.Text ("http://dx.doi.org/10.1109/JLT.2015.2462804", pya.Trans(pya.Trans.R0,x0 - (w_Si3 / 2 + taper_length), -w/2.0 -  12.5/dbu+1.0/dbu))).text_size = 0.7/dbu

