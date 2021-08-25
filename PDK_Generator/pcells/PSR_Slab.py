import pya

# Import DRC Parser
from parse_tech.drc_parser import DRC, drc_yaml_file_location
fabDRC = DRC(drc_yaml_file_location)
print(fabDRC.get_layer_min_spacing('Si'))

class PSR_Slab(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip waveguide taper.
    """

    def __init__(self):

        # Important: initialize the super class
        super(PSR_Slab, self).__init__()
        TECHNOLOGY = get_technology_by_name('SiEPICfab-Grouse')

        # declare layer params
        self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['Si'])
        self.param("siplayer", self.TypeLayer, "Si Partial Layer", default = TECHNOLOGY['Si_Partial'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
        
        # declare taper params
        self.param("w_tin", self.TypeDouble, "Taper: Width - Waveguide Input", default = 0.45)
        self.param("w_twmid", self.TypeDouble, "Taper: Width - Waveguide Mid", default = 0.55)
        self.param("w_tc", self.TypeDouble, "Taper: Width - Waveguide Output", default = 0.85)
        self.param("w_tsmid", self.TypeDouble, "Taper: Width - Slab Mid", default = 1.55)
        
        self.param("la", self.TypeDouble, "Taper: Length - Input to Mid", default = 35.0)
        self.param("lb", self.TypeDouble, "Taper: Length - Mid to Output", default = 30.0)
        
        # declare coupler params
        self.param("w_out", self.TypeDouble, "Coupler: Output Width", default = 0.45)
        self.param("lc", self.TypeDouble, "Coupler: Length", default = 100.0)
        self.param("g", self.TypeDouble, "Coupler: Gap", default = 0.1)
        
        # declare SWG params
        self.param("w_swg_in", self.TypeDouble, "SWG: Input Width", default = 0.2)
        self.param("w_swg_mid", self.TypeDouble, "SWG: Mid Width", readonly = True)
        self.param("l_swg_out", self.TypeDouble, "SWG: Output Taper Length", default = 10.0)
        self.param("period", self.TypeDouble, "SWG: Period", default = 0.2)
        self.param("ff", self.TypeDouble, "SWG: Fill Factor", default = 0.6)
    
        # hidden parameters, can be used to query this component:
        self.param("p1", self.TypeShape, "DPoint location of pin1", default = Point(-10000, 0), hidden = True, readonly = True)
        self.param("p2", self.TypeShape, "DPoint location of pin2", default = Point(0, 10000), hidden = True, readonly = True)
        self.param("p3", self.TypeShape, "DPoint location of pin3", default = Point(0, -10000), hidden = True, readonly = True)
    
    def coerce_parameters_impl(self):
        self.w_swg_mid = (self.w_tc+self.w_swg_in) - self.w_out
        n_periods = int(self.lc/self.period)
        self.lc = self.period*n_periods
    
    def display_text_impl(self):
        # Provide a descriptive text for the cell
        psr_params = ('%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f' % 
                      (self.w_tin,self.w_twmid,self.w_tsmid, self.w_tc,
                       self.la, self.lb, self.w_out, self.lc, self.g,
                       self.w_swg_in, self.w_swg_mid, self.l_swg_out,
                       self.period, self.ff) )
        return "PSR_Slab(" + psr_params + ")"

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
        
        LayerSi = ly.layer(self.silayer)
        LayerSip = ly.layer(self.siplayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        
        # Top PSR Wdiths
        w1 = int(round(self.w_tin/dbu))
        w2 = int(round(self.w_twmid/dbu))
        w7 = int(round(self.w_tsmid/dbu))
        w3 = int(round(self.w_tc/dbu))
        w4 = int(round(self.w_out/dbu))
        
        # SWG Widths
        self.w_swg_mid = (self.w_tc+self.w_swg_in) - self.w_out
        
        w5 = int(round(self.w_swg_in/dbu))
        w6 = int(round(self.w_swg_mid/dbu))
        
        la = int(round(self.la/dbu))
        lb = int(round(self.lb/dbu))
        
        n_periods = int(self.lc/self.period)
        self.lc = self.period*n_periods
        lc = int(round(self.lc/dbu))
        ld = int(round(self.l_swg_out/dbu))
        
        g = int(round(self.g/dbu))
        period = int(round(self.period/dbu))
        ff = int(round(self.ff/dbu))
        
        ############# PSR TOP #############
        # Create a list of coordinates to draw for the top waveguide portion of PSR
        coords_PSR_top_wg = [[0,w1/2], [la, w2/2], [la+lb, w3/2], [la+lb+lc, w4/2], 
                          [la+lb+lc, -w4/2], [la+lb, -w3/2], [la, -w2/2], [0, -w1/2]]
        
        # Draw the top waveguide portion of the PSR
        pts = []
        for xy in coords_PSR_top_wg:
            pts.append(Point(xy[0], xy[1]))
        shapes(LayerSi).insert(Polygon(pts))
        
        # Create list of coordinates for slab waveguide
        coords_PSR_top_slab = [[0,w1/2], [la, w7/2], [la+lb, w3/2],
                               [la+lb, -w3/2], [la, -w7/2], [0, -w1/2]]
        
        # Draw the slab waveguide portion of the PSR
        pts = []
        for xy in coords_PSR_top_slab:
            pts.append(Point(xy[0], xy[1]))
        shapes(LayerSip).insert(Polygon(pts))
        
        ############# PSR BOTTOM #############
        slope_coupling = (self.w_swg_mid/2 - self.w_swg_in/2)/self.lc
        
        # Create list of coordinates to draw for the SWG coupler
        coords_swg = []
        for i in range(0, n_periods+1):
            # Create top portion of SWG
            x = self.la + self.lb + i*self.period
            y1 = -self.w_tc/2 - self.g + i*self.period*slope_coupling
            y2 = -self.w_tc/2 - self.g
            coords_swg.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg.append([int(round(x/dbu)),int(round(y2/dbu))])
            
            if i < n_periods:
                x = self.la + self.lb + (i*self.period) + self.period*(1-self.ff)
                y1 = -self.w_tc/2 - self.g
                y2 = y1 + ((i*self.period) + self.period*(1-self.ff))*slope_coupling
                coords_swg.append([int(round(x/dbu)),int(round(y1/dbu))])
                coords_swg.append([int(round(x/dbu)),int(round(y2/dbu))])
        
        # Create sloping out SWG into single waveguide
        slope_swg_out = (self.w_swg_mid/2 - self.w_out/2) / self.l_swg_out
        slope_wg_out = (self.w_out/2 - self.w_swg_in/2) / self.l_swg_out
        i = 0
        while i < int(round(self.l_swg_out / self.period)):
            x = self.la + self.lb + self.lc + (i*self.period) + self.period*(1-self.ff)
            y1 = -self.w_tc/2 - self.g + ((i*self.period) + self.period*(1-self.ff))*slope_wg_out
            y2 = -self.w_out/2 - self.g - ((i*self.period) + self.period*(1-self.ff))*slope_swg_out
            coords_swg.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg.append([int(round(x/dbu)),int(round(y2/dbu))])
            
            x = self.la + self.lb + self.lc + (i+1)*self.period
            y1 = -self.w_out/2 - self.g - (i+1)*self.period*slope_swg_out
            y2 = -self.w_tc/2 - self.g + (i+1)*self.period*slope_wg_out
            coords_swg.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg.append([int(round(x/dbu)),int(round(y2/dbu))])

            i = i+1
        
         
        coords_swg_bot = []
        for i in range(0, n_periods+1):
            # Create bottom portion of SWG
            x = self.la + self.lb + i*self.period
            y1 = -self.w_tc/2 - self.g - self.w_swg_in - i*self.period*slope_coupling
            y2 = -self.w_tc/2 - self.g - self.w_swg_in
            coords_swg_bot.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg_bot.append([int(round(x/dbu)),int(round(y2/dbu))])
            
            if i < n_periods:
                x = self.la + self.lb + (i*self.period) + self.period*(1-self.ff)
                y1 = -self.w_tc/2 - self.g - self.w_swg_in
                y2 = y1 - ((i*self.period) + self.period*(1-self.ff))*slope_coupling
                coords_swg_bot.append([int(round(x/dbu)),int(round(y1/dbu))])
                coords_swg_bot.append([int(round(x/dbu)),int(round(y2/dbu))])
        
        i = 0
        while i < int(round(self.l_swg_out / self.period)):
            x = self.la + self.lb + self.lc + (i*self.period) + self.period*(1-self.ff)
            y1 = -self.w_tc/2 - self.g - self.w_swg_in - ((i*self.period) + self.period*(1-self.ff))*slope_wg_out
            y2 = -self.w_out/2 - self.g - self.w_swg_mid + ((i*self.period) + self.period*(1-self.ff))*slope_swg_out
            coords_swg_bot.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg_bot.append([int(round(x/dbu)),int(round(y2/dbu))])
            
            x = self.la + self.lb + self.lc + (i+1)*self.period
            y1 = -self.w_out/2 - self.g - self.w_swg_mid + (i+1)*self.period*slope_swg_out
            y2 = -self.w_tc/2 - self.g - self.w_swg_in - (i+1)*self.period*slope_wg_out
            coords_swg_bot.append([int(round(x/dbu)),int(round(y1/dbu))])
            coords_swg_bot.append([int(round(x/dbu)),int(round(y2/dbu))])

            i = i+1
        
        # Append bottom portion of SWG from end
        coords_swg_bot.reverse()
        for coord in coords_swg_bot:
            coords_swg.append(coord)
        
        # Draw bottom portion of PSR
        pts = []
        for xy in coords_swg:
            pts.append(Point(xy[0], xy[1]))
        shapes(LayerSi).insert(Polygon(pts))
        
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
    
        # Pin on the top right side:
        p2 = [Point(la+lb+lc-pin_length/2, 0), Point(la+lb+lc+pin_length/2, 0)]
        p2c = Point(la+lb+lc, 0)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w4)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, la+lb+lc, 0)
        text = Text ("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4/dbu
        shape.text_halign = 2
        
        # Pin on the bottom right side:
        p3 = [Point(la+lb+lc+ld-pin_length/2, -w4/2-g-w6/2), Point(la+lb+lc+ld+pin_length/2,-w4/2-g-w6/2)]
        p3c = Point(la+lb+lc+ld, -w4/2-g-w6/2)
        self.set_p3 = p3c
        self.p3 = p3c
        pin = Path(p3, w4)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, la+lb+lc+ld, -w4/2-g-w6/2)
        text = Text ("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4/dbu
        shape.text_halign = 2
    
        # Create the device recognition layer
        # First find the bounds of the device
        upper_bound = coords_PSR_top_wg[0][1]
        for coord in coords_PSR_top_wg:
            if coord[1] > upper_bound:
                upper_bound = coord[1]
        for coord in coords_PSR_top_slab:
            if coord[1] > upper_bound:
                upper_bound = coord[1]
                
        lower_bound = coords_swg[0][1]
        for coord in coords_swg:
            if coord[1] < lower_bound:
                lower_bound = coord[1]
        right_bound = la+lb+lc+ld
        left_bound = 0
        
        devrec_box = Box(Point(left_bound, lower_bound), Point(right_bound, upper_bound))
        shapes(LayerDevRecN).insert(devrec_box)
        
        psr_params = ('%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f-%.3f' % 
                      (self.w_tin,self.w_twmid,self.w_tsmid, self.w_tc,
                       self.la, self.lb, self.w_out, self.lc, self.g,
                       self.w_swg_in, self.w_swg_mid, self.l_swg_out,
                       self.period, self.ff) )
        
        return "PSR_Slab(" + psr_params + ")"
