# Import all dependencies and necessary modules
from . import *
from SiEPIC.extend import to_itype
from SiEPIC._globals import PIN_LENGTH as pin_length
import math
try:
  from SiEPIC.utils.layout import layout_waveguide_sbend, layout_taper
except:
  from siepic_tools.utils.layout import layout_waveguide_sbend, layout_taper



class pcell_name(pya.PCellDeclarationHelper):
  """
  Author:   FirstName LastName, Year
            Email
  """

  def __init__(self):

    # Important: initialize the super class, get technology params, get DRC params
    super(pcell_name, self).__init__()
    TECHNOLOGY = get_technology_by_name('techname')
    TECHDRC = DRC(file_location)

    # Declare the design parameters
    self.param("number_of_periods", self.TypeInt, "Number of grating periods", default = 300)     
    self.param("grating_period", self.TypeDouble, "Grating period (microns)", default = 0.317)
    self.param("length", self.TypeDouble, "Length (microns)", default = 0.15)          
 
    # Declare layer parameters ensuring they are set to hidden
    self.param("si", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'], hidden = True)
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'], hidden = True)
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'], hidden = True)
    
    # Declare simulation params
    self.param("sim_accuracy", self.TypeBoolean, "Simulation Accuracy (on = high, off = fast)", default = True)

  def display_text_impl(self):
    # Provide a descriptive text for the cell, enough to distinguish this instance from its siblings
    return "pcell_name(%sN-%.1fnm period" % (self.number_of_periods, self.grating_period*1000)
  
  def coerce_parameters_impl(self):
    # Ensure design parameters fit DRC specs and are coerced to consistent params
    if self.grating_period/2 < self.si_min_feature_size:
        raise Exception("Grating period is too small and violates min feature sizes")
    
    self.length = self.grating_period * self.number_of_periods

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    # Generate layout from set of params. Parameters should not change in this method.
    # This method should execute quickly, parsing large files or creating hefty objects should be avoided.
  
    # Reformat params 
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    LayerSiN = self.si_layer
    LayerPinRecN = self.pinrec_layer
    LayerDevRecN = self.devrec_layer

    # Draw the component clockwise
    box_width = int(round(self.grating_period/2/dbu))
    grating_period = int(round(self.grating_period/dbu))

    N = self.number_of_periods
    pts = [Point(0, box_width/2), Point(self.length, box_width/2), Point(self.length, -box_width/2),
            Point(0, -box_width/2]
    
    shapes(LayerSiN).insert(pts)

    # Create the pins on the waveguides, as short paths
    # NOTE: This is just an illustrative example. Some params are missing as this was taken from the contra-
    #       directional coupler PCell script
    w1 = to_itype(self.box_width,dbu)
    w2 = to_itype(self.box_width,dbu)
    
    t = Trans(Trans.R180, 0,y_offset_top)
    layout_waveguide_sbend(self.cell, LayerSiN, t, w1, sbend_r, sbend_offset, sbend_length)
    t = Trans(Trans.R0, -sbend_length-taper_length,y_offset_top-sbend_offset)
    layout_taper(self.cell, LayerSiN, t,  port_w, w1, taper_length)
    pin = Path([Point(pin_length/2, 0), Point(-pin_length/2, 0)], port_w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = Trans(Trans.R180, 0,vertical_offset)
    layout_taper(self.cell, LayerSiN, t,  w2, w2, sbend_length/2)
    t = Trans(Trans.R180, -sbend_length/2,vertical_offset)
    layout_taper(self.cell, LayerSiN, t,  w2, port_w, taper_length+sbend_length/2)
    t = Trans(Trans.R0, -taper_length-sbend_length,vertical_offset)
    pin = Path([Point(pin_length/2, 0), Point(-pin_length/2, 0)], port_w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = Trans(Trans.R0, length,y_offset_top )
    layout_waveguide_sbend(self.cell, LayerSiN, t, w1, sbend_r, -sbend_offset, sbend_length)
    t = Trans(Trans.R0, length+sbend_length,y_offset_top-sbend_offset)
    layout_taper(self.cell, LayerSiN, t, w1, port_w, taper_length)
    t = Trans(Trans.R0, length+sbend_length+taper_length,y_offset_top-sbend_offset)
    pin = Path([Point(-pin_length/2, 0), Point(pin_length/2, 0)], port_w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin3", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 2
    
    t = Trans(Trans.R0, length, vertical_offset)
    layout_taper(self.cell, LayerSiN, t,  w2, w2, sbend_length/2)
    t = Trans(Trans.R0, length+sbend_length/2, vertical_offset)
    layout_taper(self.cell, LayerSiN, t,  w2, port_w, taper_length+sbend_length/2)
    t = Trans(Trans.R0, length+taper_length+sbend_length,vertical_offset)
    pin = Path([Point(-pin_length/2, 0), Point(pin_length/2, 0)], port_w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin4", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 2

    # Compact model information
    t = Trans(Trans.R0, 10, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/{orig-techname}', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 10, 500)
    text = Text ('Component={cm-name}', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 10, -500)
    text = Text \
      ('Spice_param:number_of_periods=%s grating_period=%.3fu wg1_width=%.3fu wg2_width=%.3fu corrugation_width1=%.3fu corrugation_width2=%.3fu gap=%.3fu apodization_index=%.3f AR=%s sinusoidal=%s accuracy=%s' %\
      (self.number_of_periods, self.grating_period, self.wg1_width, self.wg2_width, self.corrugation_width1, self.corrugation_width2, self.gap, self.apodization_index, int(self.AR), int(self.sinusoidal), int(self.accuracy)), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    box = pya.Box(pya.Point(-taper_length-sbend_length, vertical_offset+3/2*port_w),pya.Point(length+taper_length+sbend_length, y_offset_top-sbend_offset-3/2*port_w))
    shapes(LayerDevRecN).insert(box)
    