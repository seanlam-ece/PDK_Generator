'''
################################################################################
Lumerical FDTD Solutions simulation for a component
generate S-Parameters

definitions:
  z: thickness direction
  z=0: centre of the waveguides, so we can use symmetric mesh in z
       which will be better for convergence testing as the mesh won't move
################################################################################
'''
import klayout.db as db
from common.common_methods import get_klayout_folder_path
from lumgeo import generate_lum_geometry
from lumgen import get_process_layer_sources, LayerMappingDialog, get_techname
from common.lumerical_lumapi import lumapi
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox,\
    QDialog, QGridLayout, QLabel, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox, QFileDialog, QHBoxLayout,\
    QLineEdit
from PyQt5.QtGui import QFont
import sys, os
import numpy as np

# XML to Dict parser, from:
# https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary-in-python/10077069
def etree_to_dict(t):
    from collections import defaultdict
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


def angle_vector(u):
    from math import atan2, pi
    return (atan2(u.y, u.x)) / pi * 180

def get_points(self):
    return [db.Point(pt.x, pt.y) for pt in self.each_point()]

db.Path.get_points = get_points


def xml_to_dict(t):
    from xml.etree import cElementTree as ET
    try:
        e = ET.XML(t)
    except:
        raise UserWarning("Error in the XML file.")
    return etree_to_dict(e)

def load_FDTD_settings(process_yaml = ''):

    import os
    import fnmatch
    techname = get_techname(process_yaml)
    dir_path = get_klayout_folder_path()
    search_str = 'FDTD.xml'
    matches = []
    for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
        for filename in fnmatch.filter(filenames, search_str):
            # if tech_name in root:
            if techname in root:
                matches.append(os.path.join(root, filename))
                
    if matches:
        f = matches[0]
        print(f)
        file = open(f, 'r')
        FDTD = xml_to_dict(file.read())
        file.close()

        FDTD = FDTD['FDTD']
        FDTD1 = {}
        for k in FDTD['floats'].keys():
            FDTD1[k] = float(FDTD['floats'][k])
        for k in FDTD['strings'].keys():
            FDTD1[k] = FDTD['strings'][k]
        return FDTD1
    else:
        return None

class GUI_FDTD_component_simulation(QDialog):
  def __init__(self, process_yaml = '', parent = None, verbose=None):
    super(GUI_FDTD_component_simulation, self).__init__()
    self.verbose = verbose

    self.setWindowTitle("FDTD Component Simulation configuration")

    mainLayout = QVBoxLayout(self)
    self.setLayout(mainLayout)

    self.FDTD_settings=load_FDTD_settings(process_yaml)
    if self.verbose:
      print(self.FDTD_settings)

    if not self.FDTD_settings:
      warning = QMessageBox()
      warning.setStandardButtons(QMessageBox.Ok)
      warning.setText("No FDTD simulation configuration file (FDTD.xml) was found for present technology.")
      QMessageBox.StandardButton(warning.exec_())
      self.close()
      return

    paramsLayout = QVBoxLayout(self);
    self.qtext=[]
    self.qlabel=[]
    for t in self.FDTD_settings:
      paramLayout = QHBoxLayout(self);
      self.qlabel.append ( QLabel(t,self) )
      self.qtext.append ( QLineEdit(self) )
      self.qtext[-1].fieldtype = type(self.FDTD_settings[t])
      self.qtext[-1].setText(str(self.FDTD_settings[t]))
      paramLayout.addWidget(self.qlabel[-1])
      paramLayout.addWidget(self.qtext[-1])
      paramsLayout.addLayout(paramLayout)

    buttonsLayout = QHBoxLayout(self);
    ok = QPushButton("OK",self)
    ok.clicked.connect(self.ok)
    cancel = QPushButton("Cancel",self)
    cancel.clicked.connect(self.cancel)
    buttonsLayout.addWidget(cancel)
    buttonsLayout.addWidget(ok)

    mainLayout.addLayout(paramsLayout)
    mainLayout.addLayout(buttonsLayout)

    self.show()

  def cancel(self, val):
    self.close()
    if self.verbose:
      print('closing GUI')

  def ok(self, val):
    self.close()
    FDTD_settings = {}
    for i in range(0,len(self.qlabel)):
      if self.verbose:
        print("%s: %s (%s)" %(self.qlabel[i].text(), self.qtext[i].text(), self.qtext[i].fieldtype))
      if self.qtext[i].fieldtype == float:
        FDTD_settings[self.qlabel[i].text()]=float(self.qtext[i].text())
      else:
        FDTD_settings[self.qlabel[i].text()]=self.qtext[i].text()
    if self.verbose:
      print(FDTD_settings)
      
    if self.verbose:
      print('closing GUI')
      
    self.FDTD_settings = FDTD_settings
    


class Pin():

    def __init__(self, path=None, _type=None, box=None, polygon=None, component=None, net=None, pin_name=None):
        
        self.type = _type           # one of PIN_TYPES, defined in SiEPIC._globals.PINTYPES
        if net:                     # Net for netlist generation
            self.net = net            # which net this pin is connected to
        else:
            self.net = Net()
        self.pin_name = pin_name    # label read from the cell layout (PinRec text)
        self.component = component  # which component index this pin belongs to
        self.path = path            # the pin's Path (Optical)
        self.polygon = polygon      # the pin's polygon (Optical IO)
        if path:
            pts = path.get_points()
            if len(pts) == 2:
              self.center = (pts[0] + pts[1]) * 0.5  # center of the pin: a Point
            else:
              print('SiEPIC-Tools: class Pin():__init__: detected invalid Pin')
              self.rotation = 0
              return
            self.rotation = angle_vector(pts[1] - pts[0])  # direction / angle of the optical pin
        else:
            self.rotation = 0
        self.box = box              # the pin's Box (Electrical)
        if box:
            self.center = box.center()  # center of the pin: a Point
        if polygon:
            self.rotation = 0
            self.center = polygon.bbox().center()  # center of the pin: a Point (relative coordinates, within component)

    def transform(self, trans):
        # Transformation of the pin location
        from .utils import angle_vector
        if self.path:
            self.path = self.path.transformed(trans)
            pts = self.path.get_points()
            self.center = (pts[0] + pts[1]) * 0.5
            self.rotation = angle_vector(pts[1] - pts[0])
        if self.polygon:
            self.polygon = self.polygon.transformed(trans)
            self.center = self.polygon.bbox().center()
            self.rotation = 0
        return self

    def display(self):
        p = self
        print("- pin_name %s: component_idx %s, pin_type %s, rotation: %s, net: %s, (%s), path: %s" %
              (p.pin_name, p.component.idx, p.type, p.rotation, p.net.idx, p.center, p.path))

class Net:

    def __init__(self, idx=None, _type=None, pins=None):
        self.idx = idx           # net number, index, should be unique, 0, 1, 2, ...
        self.type = _type        # one of PIN_TYPES, defined in SiEPIC._globals.PINTYPES
        # for backwards linking (optional)
        self.pins = pins         # pin array, Pin[]

    def display(self):
        print('- net: %s, pins: %s' % (self.idx,
                                       [[p.pin_name, p.center.to_s(), p.component.component, p.component.instance] for p in self.pins]))


# Define an Enumeration type for Python
# TODO: maybe move to standard enum for python3
# https://docs.python.org/3/library/enum.html
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def generate_component_sparam(gds_path, process_file_lbr, process_file_yml, do_simulation = True, addto_CML = True, verbose = False, FDTD_settings = None):
    import os
    
    # Define enumeration for pins
    PIN_TYPES = enum('OPTICALIO', 'OPTICAL', 'ELECTRICAL')
    PIN_LENGTH = 100  # 0.1 micron
    
    # simulation filenames
    component_name = gds_path.split('/')[-1].split('\\')[-1].split('.gds')[0]
    gds_dir = os.path.dirname(gds_path)
    fsp_filename = os.path.join(gds_dir, '%s.fsp' % component_name)
    xml_filename = os.path.join(gds_dir, '%s.xml' % component_name)
    file_sparam = os.path.join(gds_dir, '%s.dat' % component_name)
    svg_filename = os.path.join(gds_dir, "%s.svg" % component_name)
    
    # Instantiate layout
    ly = db.Layout()
    ly.read(gds_path)
    
    # Instantiate flattened and merged shapes layout for layer builder
    ly_f = db.Layout()
    ly_f.read(gds_path)
    
    tc_ind = ly_f.top_cell().cell_index()
    ly_f.flatten(tc_ind, -1, True) # Flatten tc_ind cell, -1 = All levels of heirarchy, True = Prune unused cells
    
    out_cell = ly_f.top_cell()
    
    cell = ly_f.top_cell()
    
    for layer in ly_f.layer_indexes():
        
        region = db.Region(cell.begin_shapes_rec(layer))
        region.merge()
        cell.layout().clear_layer(layer)
        try:
            cell.shapes(layer).insert(region)
        except:
            pass    
    
    
    # h = {}
    
    # for lind in ly_f.layer_indexes():
    #     h[lind] = ly_f.top_cell().begin_shapes_rec(lind)
        
    # for li, shape_arr in h.items():
        
    #     selected = db.Region()
    #     selected.merged_semantics = False
        
    #     # Add to region
    #     while not shape_arr.at_end():
    #         if shape_arr.shape().is_polygon():
    #             selected.insert(shape_arr.shape().polygon)
    #         shape_arr.next()
            
    #     region = selected.merge()
        
    #     # for poly in selected:
    #     #     out_cell.shapes(li).insert(poly)
    #     out_cell.shapes(li).insert(region)
    
    # # Delete shape from layout
    # for li, shape_arr in h.items():
    #     while not shape_arr.at_end():
    #         sh = shape_arr.shape()
    #         if sh.is_valid():
    #             sh.shapes().erase(sh)
    #         shape_arr.next()
            
    # tp = ly_f.top_cell()
    # for lind in ly_f.layer_indexes():
    #     region = db.Region(tp.begin_shapes_rec(lind))
    #     region.merge()
        
    #     tp.layout().clear_layer(lind)
    #     tp.shapes(lind).insert(region)
        
     
    tmp_gds = os.path.join(gds_dir, "tmp.gds")
    ly_f.write(tmp_gds)

    # Map process layer to ports and device boundary
    process_layer_sources = get_process_layer_sources(process_file_yml)
    LayerMapDialog = LayerMappingDialog(['Waveguide', 'Ports', 'Simulation Region'], process_layer_sources)
    LayerMapDialog.exec_()
    
    # Pin Recognition layer
    ly_num = int(LayerMapDialog.layer_mapping['Ports'].split(' - ')[-1].split(':')[0])
    ly_datatype = int(LayerMapDialog.layer_mapping['Ports'].split(' - ')[-1].split(':')[1])
    LayerPinRecN = ly.layer(db.LayerInfo(ly_num,ly_datatype))
    
    # Waveguide layer
    LayerWaveguideName = LayerMapDialog.layer_mapping['Waveguide'].split(' - ')[0]
    
    # Device Recognition layer (FDTD simulation region)
    # ly_num = int(LayerMapDialog.layer_mapping['Simulation Region'].split(' - ')[-1].split(':')[0])
    # ly_datatype = int(LayerMapDialog.layer_mapping['Simulation Region'].split(' - ')[-1].split(':')[1])
    # LayerDevRecN = ly_f.layer(db.LayerInfo(ly_num,ly_datatype))
    
    error_text = ''
    
    # iterate through all the PinRec shapes in the cell
    # array to store Pin objects
    pins = []
    it = ly.top_cell().begin_shapes_rec(LayerPinRecN)
    while not(it.at_end()):
        #    if verbose:
        #      print(it.shape().to_s())
        # Assume a PinRec Path is an optical pin
        if it.shape().is_path():
            if verbose:
                print("Path: %s" % it.shape())
            # get the pin path
            pin_path = it.shape().path.transformed(it.itrans())
            # Find text label (pin name) for this pin by searching inside the Path bounding box
            # Text label must be on DevRec layer
            pin_name = None
            subcell = it.cell()  # cell (component) to which this shape belongs
            iter2 = subcell.begin_shapes_rec_touching(LayerPinRecN, it.shape().bbox())
            while not(iter2.at_end()):
                if iter2.shape().is_text():
                    pin_name = iter2.shape().text.string
                iter2.next()
            if pin_name == None or pin_path.num_points()!=2:
                print("Invalid pin Path detected: %s. Cell: %s" % (pin_path, subcell.name))
                error_text += ("Invalid pin Path detected: %s, in Cell: %s, Optical Pins must have a pin name.\n" %
                               (pin_path, subcell.name))
        #        raise Exception("Invalid pin Path detected: %s, in Cell: %s.\nOptical Pins must have a pin name." % (pin_path, subcell.name))
            else:
              # Store the pin information in the pins array
              pins.append(Pin(path=pin_path, _type=PIN_TYPES.OPTICAL, pin_name=pin_name))
        
        # Assume a PinRec Box is an electrical pin
        # similar to optical pin
        if it.shape().is_simple_polygon():
            pin_box = it.shape().bbox().transformed(it.itrans())
        if it.shape().is_box():
            if verbose:
                print("Box: %s" % it.shape())
            pin_box = it.shape().box.transformed(it.itrans())
        if it.shape().is_simple_polygon() or it.shape().is_box():
            pin_name = None
            subcell = it.cell()  # cell (component) to which this shape belongs
            iter2 = subcell.begin_shapes_rec_touching(LayerPinRecN, it.shape().bbox())
            if verbose:
                print("Box: %s" % it.shape().bbox())
            while not(iter2.at_end()):
                if verbose:
                    print("shape touching: %s" % iter2.shape())
                if iter2.shape().is_text():
                    pin_name = iter2.shape().text.string
                iter2.next()
            if pin_name == None:
                error_text += ("Invalid pin Box detected: %s, Cell: %s, Electrical Pins must have a pin name.\n" %
                               (pin_box, subcell.name))
        #        raise Exception("Invalid pin Box detected: %s.\nElectrical Pins must have a pin name." % pin_box)
            pins.append(Pin(box=pin_box, _type=PIN_TYPES.ELECTRICAL, pin_name=pin_name))
        
        it.next()
    
    # iterate through all the DevRec shapes in the cell
    # find bounding box
    # it = ly.top_cell().begin_shapes_rec(LayerDevRecN)
    # while not(it.at_end()):
    #     if it.shape().is_simple_polygon() or it.shape().is_box():
    #         devrec_box = it.shape().bbox()
    #     it.next()
    devrec_box = ly.top_cell().bbox()
    
    
    # get FDTD settings from XML file if FDTD settings not available
    if not FDTD_settings:
        FDTD_settings=load_FDTD_settings(process_file_yml)
        if FDTD_settings:
            if verbose:
                print(FDTD_settings)
    
    # Configure wavelength and polarization
    # polarization = {'quasi-TE', 'quasi-TM', 'quasi-TE and -TM'}
    mode_selection = FDTD_settings['mode_selection']
    mode_selection_index = []
    if 'fundamental TE mode' in mode_selection or '1' in mode_selection:
        mode_selection_index.append(1)
    if 'fundamental TM mode' in mode_selection or '2' in mode_selection:
        mode_selection_index.append(2)
    if not mode_selection_index:
        error = QMessageBox()
        error.setStandardButtons(QMessageBox.Ok )
        error.setText("Error: Invalid modes requested.")
        response = error.exec_()
        return
    
    # wavelength
    wavelength_start = FDTD_settings['wavelength_start']
    wavelength_stop =  FDTD_settings['wavelength_stop']
    
    # Configure wavelength and polarization
    # polarization = {'quasi-TE', 'quasi-TM', 'quasi-TE and -TM'}
    FDTDzspan=FDTD_settings['Initial_FDTD_Z_span']
    mode_selection = FDTD_settings['mode_selection']
    mode_selection_index = []
    if 'fundamental TE mode' in mode_selection or '1' in mode_selection:
        mode_selection_index.append(1)
    if 'fundamental TM mode' in mode_selection or '2' in mode_selection:
        mode_selection_index.append(2)
    if not mode_selection_index:
        error = db.QMessageBox()
        error.setStandardButtons(db.QMessageBox.Ok )
        error.setText("Error: Invalid modes requested.")
        response = error.exec_()
        return
  
    # Instantiate FDTD simulation object
    fdtd = lumapi.FDTD(hide = False)
    dbum = ly.dbu*1e-6
    
    # Create component geometry in FDTD
    generate_lum_geometry(fdtd, process_file_lbr, tmp_gds)
    
    # create FDTD simulation region (extra large)
    FDTDzspan=FDTD_settings['Initial_FDTD_Z_span']
    FDTDz=fdtd.getlayer(LayerWaveguideName, 'thickness')/2
    if mode_selection_index==1:
        Z_symmetry = 'Symmetric'
    elif mode_selection_index==2:
        Z_symmetry ='Anti-Symmetric'
    else:
        Z_symmetry = FDTD_settings['Initial_Z-Boundary-Conditions']
    FDTDxmin,FDTDxmax,FDTDymin,FDTDymax = (devrec_box.left)*dbum-200e-9, (devrec_box.right)*dbum+200e-9, (devrec_box.bottom)*dbum-200e-9, (devrec_box.top)*dbum+200e-9
    sim_time = max(devrec_box.width(),devrec_box.height())*dbum * 4.5;
    fdtd.eval(" \
      addfdtd; set('x min',%s); set('x max',%s); set('y min',%s); set('y max',%s); set('z', %s); set('z span',%s);\
      set('force symmetric z mesh', 1); set('mesh accuracy',1); \
      set('x min bc','Metal'); set('x max bc','Metal'); \
      set('y min bc','Metal'); set('y max bc','Metal'); \
      set('z min bc','%s'); set('z max bc','%s'); \
      setglobalsource('wavelength start',%s); setglobalsource('wavelength stop', %s); \
      setglobalmonitor('frequency points',%s); set('simulation time', %s/c+1500e-15); \
      addmesh; set('override x mesh',0); set('override y mesh',0); set('override z mesh',1); set('z span', 0); set('dz', %s); set('z', %s); \
      ?'FDTD solver with mesh override added'; " % ( FDTDxmin,FDTDxmax,FDTDymin,FDTDymax,FDTDz,FDTDzspan, \
         Z_symmetry, FDTD_settings['Initial_Z-Boundary-Conditions'], \
         wavelength_start,wavelength_stop, \
         FDTD_settings['frequency_points_monitor'], sim_time, \
         FDTD_settings['thickness_Si']/4, FDTD_settings['thickness_Si']/2) )
    
    
    
    # create FDTD ports
    # configure boundary conditions to be PML where we have ports
    # FDTD_bc = {'y max bc': 'Metal', 'y min bc': 'Metal', 'x max bc': 'Metal', 'x min bc': 'Metal'}
    port_dict = {0.0: 'x max bc', 90.0: 'y max bc', 180.0: 'x min bc', -90.0: 'y min bc'}
    for p in pins:
        if p.rotation in [180.0, 0.0]:
            fdtd.eval(" \
              addport; set('injection axis', 'x-axis'); set('x',%s); set('y',%s); set('y span',%s); set('z', %s); set('z span',%s); \
              " % (p.center.x*dbum, p.center.y*dbum,p.path.width*dbum,FDTDz,FDTDzspan)  )
        if p.rotation in [270.0, 90.0, -90.0]:
            fdtd.eval(" \
              addport; set('injection axis', 'y-axis'); set('x',%s); set('y',%s); set('x span',%s); set('z', %s); set('z span',%s); \
              " % (p.center.x*dbum, p.center.y*dbum,p.path.width*dbum,FDTDz,FDTDzspan)  )
        if p.rotation in [0.0, 90.0]:
            p.direction = 'Backward'
        else:
            p.direction = 'Forward'
        fdtd.eval(" \
          set('name','%s'); set('direction', '%s'); set('number of field profile samples', %s); updateportmodes(%s); \
          select('FDTD'); set('%s','PML'); \
          ?'Added pin: %s, set %s to PML'; " % (p.pin_name, p.direction, FDTD_settings['frequency_points_expansion'], mode_selection_index, \
              port_dict[p.rotation], p.pin_name, port_dict[p.rotation] )  )
    
    # Calculate mode sources
    # Get field profiles, to find |E| = 1e-6 points to find spans
    import sys
    if not 'win' in sys.platform:  # Windows getVar ("E") doesn't work.
        min_z, max_z = 0,0
        for p in [pins[0]]:  # if all pins are the same, only do it once
            for m in mode_selection_index:
                fdtd.eval( " \
                  select('FDTD::ports::%s'); mode_profiles=getresult('FDTD::ports::%s','mode profiles'); E=mode_profiles.E%s; x=mode_profiles.x; y=mode_profiles.y; z=mode_profiles.z; \
                  ?'Selected pin: %s'; " % (p.pin_name, p.pin_name, m, p.pin_name)  )
                E=fdtd.getv( "E")
                x=fdtd.getv( "x")
                y=fdtd.getv( "y")
                z=fdtd.getv( "z")
      
                # remove the wavelength from the array,
                # leaving two dimensions, and 3 field components
                if p.rotation in [180.0, 0.0]:
                  Efield_xyz = np.array(E[0,:,:,0,:])
                else:
                  Efield_xyz = np.array(E[:,0,:,0,:])
                # find the field intensity (|Ex|^2 + |Ey|^2 + |Ez|^2)
                Efield_intensity = np.empty([Efield_xyz.shape[0],Efield_xyz.shape[1]])
                print(Efield_xyz.shape)
                for a in range(0,Efield_xyz.shape[0]):
                  for b in range(0,Efield_xyz.shape[1]):
                    Efield_intensity[a,b] = abs(Efield_xyz[a,b,0])**2+abs(Efield_xyz[a,b,1])**2+abs(Efield_xyz[a,b,2])**2
                # find the max field for each z slice (b is the z axis)
                Efield_intensity_b = np.empty([Efield_xyz.shape[1]])
                for b in range(0,Efield_xyz.shape[1]):
                  Efield_intensity_b[b] = max(Efield_intensity[:,b])
                # find the z thickness where the field has sufficiently decayed
                indexes = np.argwhere ( Efield_intensity_b > FDTD_settings['Efield_intensity_cutoff_eigenmode'] )
                min_index, max_index = int(min(indexes)), int(max(indexes))
                if min_z > z[min_index]:
                  min_z = z[min_index]
                if max_z < z[max_index]:
                  max_z = z[max_index]
                if verbose:
                  print(' Port %s, mode %s field decays at: %s, %s microns' % (p.pin_name, m, z[max_index], z[min_index]) )
    
            if FDTDzspan > max_z-min_z:
                FDTDzspan = float(max_z-min_z)
                if verbose:
                    print(' Updating FDTD Z-span to: %s microns' % (FDTDzspan) )

    # Configure FDTD region, mesh accuracy 1
    # run single simulation
    fdtd.eval( " \
      select('FDTD'); set('z span',%s);\
      save('%s');\
      ?'FDTD Z-span updated to %s'; " % (FDTDzspan, fsp_filename, FDTDzspan) )

    # Calculate, plot, and get the S-Parameters, S21, S31, S41 ...
    # optionally simulate a subset of the S-Parameters
    # assume input on port 1
    # return Sparams: last mode simulated [wavelength, pin out index], and
    #        Sparams_modes: all modes [mode, wavelength, pin out index]
    def FDTD_run_Sparam_simple(pins, in_pin = None, out_pins = None, modes = [1], plots = False):
        if verbose:
            print(' Run simulation S-Param FDTD')
        Sparams_modes = []
        if not in_pin:
            in_pin = pins[0]
        for m in modes:
            fdtd.eval( "\
              switchtolayout; select('FDTD::ports');\
              set('source port','%s');\
              set('source mode','mode %s');\
              run; " % ( in_pin.pin_name, m ) )
            port_pins = [in_pin]+out_pins if out_pins else pins
            for p in port_pins:
                if verbose:
                    print(' port %s expansion' % p.pin_name )
                fdtd.eval( " \
                  P=Port_%s=getresult('FDTD::ports::%s','expansion for port monitor'); \
                   " % (p.pin_name,p.pin_name) )
            fdtd.eval( "wavelengths=c/P.f*1e6;")
            wavelengths = fdtd.getv( "wavelengths")
            Sparams = []
            for p in port_pins[1::]:
                if verbose:
                    print(' S_%s_%s Sparam' % (p.pin_name,in_pin.pin_name) )
                fdtd.eval( " \
                  Sparam=S_%s_%s= Port_%s.%s/Port_%s.%s;  \
                   " % (p.pin_name, in_pin.pin_name, \
                        p.pin_name, 'b' if p.direction=='Forward' else 'a', \
                        in_pin.pin_name, 'a' if in_pin.direction=='Forward' else 'b') )
                Sparams.append(fdtd.getv( "Sparam"))
                if plots:
                    if verbose:
                        print(' Plot S_%s_%s Sparam' % (p.pin_name,in_pin.pin_name) )
                    fdtd.eval( " \
                      plot (wavelengths, 10*log10(abs(Sparam(:,%s))^2),  'Wavelength (um)', 'Transmission (dB)', 'S_%s_%s, mode %s'); \
                       " % (modes.index(m)+1, p.pin_name, in_pin.pin_name, modes.index(m)+1) )
            Sparams_modes.append(Sparams)
        return Sparams, Sparams_modes

    # Run the first FDTD simulation
    in_pin = pins[0]
    Sparams, Sparams_modes = FDTD_run_Sparam_simple(pins, in_pin=in_pin, modes = mode_selection_index, plots = True)

    # find the pin that has the highest Sparam (max over 1-wavelength and 2-modes)
    # use this Sparam for convergence testing
    # use the highest order mode for the convergence testing and reporting IL values.
    Sparam_pin_max_modes = []
    Mean_IL_best_port = [] # one for each mode
    for m in mode_selection_index:
        Sparam_pin_max_modes.append( np.amax(np.absolute(np.array(Sparams)[:,:,mode_selection_index.index(m)]), axis=1).argmax() + 1 )
        Mean_IL_best_port.append( -10*np.log10(np.mean(np.absolute(Sparams)[Sparam_pin_max_modes[-1]-1,:,mode_selection_index.index(m)])**2) )

    print("Sparam_pin_max_modes = %s" % Sparam_pin_max_modes)

    # user verify ok?
    warning = QMessageBox()
    warning.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
    warning.setDefaultButton(QMessageBox.Yes)
    info_text = "First FDTD simulation complete (coarse mesh, lowest accuracy). Highest transmission S-Param: \n"
    for m in mode_selection_index:
        info_text +=  "mode %s, S_%s_%s has %s dB average insertion loss\n" % (m, pins[Sparam_pin_max_modes[mode_selection_index.index(m)]].pin_name, in_pin.pin_name, Mean_IL_best_port[mode_selection_index.index(m)])
    warning.setInformativeText(info_text)
    warning.setText("Do you want to Proceed?")
    if verbose:
        print(info_text)
    else:
        if(QMessageBox.StandardButton(warning.exec_()) == QMessageBox.Cancel):
            return

    # Convergence testing on S-Parameters:
    # convergence test on simulation z-span (assume symmetric increases)
    # loop in Python so we can check if it is good enough
    # use the highest order mode
    mode_convergence = [mode_selection_index[-1]]
    Sparam_pin_max = Sparam_pin_max_modes[-1]
    if FDTD_settings['convergence_tests']:
        test_converged = False
        convergence = []
        Sparams_abs_prev = np.array([np.absolute(Sparams)[Sparam_pin_max-1,:,:]])
        while not test_converged:
            FDTDzspan += FDTD_settings['convergence_test_span_incremement']
            fdtd.eval( " \
              switchtolayout; select('FDTD'); set('z span',%s);\
              " % (FDTDzspan) )
            Sparams, Sparams_modes = FDTD_run_Sparam_simple(pins, in_pin=in_pin, out_pins = [pins[Sparam_pin_max]], modes = mode_convergence, plots = True)
            Sparams_abs = np.array(np.absolute(Sparams))
            rms_error = np.sqrt(np.mean( (Sparams_abs_prev - Sparams_abs)**2 ))
            convergence.append ( [FDTDzspan, rms_error] )
            Sparams_abs_prev = Sparams_abs
            if verbose:
                print (' convergence: span and rms error %s' % convergence[-1] )
            fdtd.eval( " \
              ?'FDTD Z-span: %s, rms error from previous: %s (convergence testing until < %s)'; " % (FDTDzspan, rms_error, FDTD_settings['convergence_test_rms_error_limit']) )
            if rms_error < FDTD_settings['convergence_test_rms_error_limit']:
                test_converged=True
                FDTDzspan += -1*FDTD_settings['convergence_test_span_incremement']
            # check if the last 3 points have reducing rms
            if len(convergence) > 2:
                test_rms = np.polyfit(np.array(convergence)[-3:,0], np.array(convergence)[-3:,1], 1)
                if verbose:
                    print ('  convergence rms trend: %s; fit data: %s' %  (test_rms, np.array(convergence)[:,-3:]) )
                if test_rms[0] > 0:
                    if verbose:
                        print (' convergence problem, not improving rms. terminating convergence test.'  )
                    fdtd.eval( "?'convergence problem, not improving rms. terminating convergence test.'; "  )
                    test_converged=True
                    FDTDzspan += -2*FDTD_settings['convergence_test_span_incremement']
        
        fdtd.putv( 'convergence', convergence)
        fdtd.eval("\
                  sim_span = matrix(length(convergence),1); \
                  rms_error =  matrix(length(convergence),1);\
                  for(i=1:length(convergence)) \
                  {\
                      sim_span(i,1) = convergence{i}{1};\
                      rms_error(i,1) = convergence{i}{2};\
                  } plot(sim_span(:,1), rms_error(:,1), 'Simulation span','RMS error between simulation','Convergence testing');")
            
    # Configure FDTD region, higher mesh accuracy, update FDTD ports mode source frequency points
    fdtd.eval( " \
      switchtolayout; select('FDTD'); set('mesh accuracy',%s);\
      set('z min bc','%s'); set('z max bc','%s'); \
      ?'FDTD mesh accuracy updated %s, Z boundary conditions: %s'; " % (FDTD_settings['mesh_accuracy'], FDTD_settings['Z-Boundary-Conditions'], FDTD_settings['Z-Boundary-Conditions'], FDTD_settings['mesh_accuracy'], FDTD_settings['Z-Boundary-Conditions']) )
    for p in pins:
        fdtd.eval( " \
        select('FDTD::ports::%s'); set('number of field profile samples', %s); \
        ?'updated pin: %s'; " % (p.pin_name, FDTD_settings['frequency_points_expansion'], p.pin_name)  )

    # Run full S-parameters
    # add s-parameter sweep task
    fdtd.eval( " \
      deletesweep('s-parameter sweep'); \
      addsweep(3); NPorts=%s; \
      " % (len(pins))  )
    for p in pins:
        for m in mode_selection_index:
            # add index entries to s-matrix mapping table
            fdtd.eval( " \
              index1 = struct; \
              index1.Port = '%s'; index1.Mode = 'mode %s'; \
              addsweepparameter('s-parameter sweep',index1); \
            " % (p.pin_name, m))

    # filenames for the s-parameter files
    files_sparam = []

    # run s-parameter sweep, collect results, visualize results
    # export S-parameter data to file named xxx.dat to be loaded in INTERCONNECT
    pin_h0, pin_w0 = str(round(FDTD_settings['thickness_Si'],9)), str(round(pins[0].path.width*dbum,9))
    file_sparam = os.path.join(gds_dir, '%s_t=%s_w=%s.dat' % (component_name,pin_h0,pin_w0))
    files_sparam.append(file_sparam)
    fdtd.eval( " \
      runsweep('s-parameter sweep'); \
      S_matrix = getsweepresult('s-parameter sweep','S matrix'); \
      S_parameters = getsweepresult('s-parameter sweep','S parameters'); \
      S_diagnostic = getsweepresult('s-parameter sweep','S diagnostic'); \
      # visualize(S_parameters); \n\
      exportsweep('s-parameter sweep','%s'); \
      " % (file_sparam) )

    os.remove(tmp_gds)
    if verbose:
        print(" S-Parameter file: %s" % file_sparam)

    # Write XML file for INTC scripted compact model
    # height and width are set to the first pin width/height
    xml_out = '\
<?xml version="1.0" encoding="UTF-8"?> \n\
<lumerical_lookup_table version="1.0" name = "index_table"> \n\
<association> \n\
  <design> \n\
      <value name="height" type="double">%s</value> \n\
      <value name="width" type="double">%s</value> \n\
  </design> \n\
  <extracted> \n\
      <value name="sparam" type="string">%s</value> \n\
  </extracted> \n\
</association>\n' % (pin_h0, pin_w0, os.path.basename(file_sparam))
    fh = open(xml_filename, "w")
    fh.writelines(xml_out)

    # Perform final corner analysis, for Monte Carlo simulations
    if FDTD_settings['Perform-final-corner-analysis']:
        fdtd.eval("leg=cell(4*%s); li=0; \n" % (len(mode_selection_index))) # legend for corner plots
        fdtd.select('layer group')
        ly_thickness = fdtd.getlayer(LayerWaveguideName, 'thickness')
        for w in [-FDTD_settings['width_Si_corners'],FDTD_settings['width_Si_corners']]:
            # polygons_w = [p for p in db.Region(polygons).sized(w/2*1e9).each_merged()]
            # send_polygons_to_FDTD(polygons_w)
            fdtd.switchtolayout()
            fdtd.select('layer group')
            fdtd.setlayer(LayerWaveguideName, 'pattern growth delta', w)
            for h in [-FDTD_settings['thickness_Si_corners'],FDTD_settings['thickness_Si_corners']]:
                # lumapi.eval(_globals.FDTD, " \
                #       switchtolayout; selectpartial('polygons::'); set('z span',%s);\
                #       " % (FDTD_settings['thickness_Si']+h) )
                fdtd.select('layer group')
                fdtd.setlayer(LayerWaveguideName, 'thickness', ly_thickness + h)
                # run s-parameter sweep, collect results, visualize results
                # export S-parameter data to file named xxx.dat to be loaded in INTERCONNECT
                pin_h, pin_w = str(round(FDTD_settings['thickness_Si']+h,9)), str(round(pins[0].path.width*dbum+w,9))
                file_sparam = os.path.join(gds_dir, '%s_t=%s_w=%s.dat' % (component_name,pin_h,pin_w))
                files_sparam.append(file_sparam)
                fdtd.eval("  \
                  runsweep('s-parameter sweep'); \
                  S_matrix = getsweepresult('s-parameter sweep','S matrix'); \
                  S_parameters = getsweepresult('s-parameter sweep','S parameters'); \
                  S_diagnostic = getsweepresult('s-parameter sweep','S diagnostic'); \
                  exportsweep('s-parameter sweep','%s'); \
                  # visualize(S_parameters); \n\
                  " % (file_sparam) )
                if verbose:
                    print(" S-Parameter file: %s" % file_sparam)

                #if verbose:
                #  print(' Plot S_%s_%s Sparam' % (p.pin_name,in_pin.pin_name) )

                # plot results of the corner analysis:
                for m in mode_selection_index:
                    fdtd.eval(" \
                      plot(wavelengths, 20*log10(abs(S_parameters.S%s1)), 'Wavelength (um)', 'Transmission (dB)'); holdon; \
                      li = li + 1; \
                      leg{li} = 'S_%s_%s:%s - %s, %s'; \
                        " % ( Sparam_pin_max_modes[mode_selection_index.index(m)]+1, pins[Sparam_pin_max_modes[mode_selection_index.index(m)]].pin_name, in_pin.pin_name, mode_selection_index.index(m)+1, pin_h,pin_w) )

                # Write XML file for INTC scripted compact model
                # height and width are set to the first pin width/height
                xml_out = '\
<association> \n\
  <design> \n\
      <value name="height" type="double">%s</value> \n\
      <value name="width" type="double">%s</value> \n\
  </design> \n\
  <extracted> \n\
      <value name="sparam" type="string">%s</value> \n\
  </extracted> \n\
</association>\n' % (pin_h, pin_w, os.path.basename(file_sparam))
                fh.writelines(xml_out)

        # Add legend to the Corner plots
        fdtd.eval("legend(leg);\n")

    xml_out = '\
</lumerical_lookup_table>'
    fh.writelines(xml_out)
    files_sparam.append(xml_filename)
    fh.close()

    if verbose:
        print(" XML file: %s" % xml_filename)



    if addto_CML:
        # INTC custom library name
        INTC_Lib = 'SiEPIC_user'
        # Run using Python integration:
        interconnect = lumapi.INTERCONNECT(hide = False)
    
        # Create a component
        port_dict2 = {0.0: 'Right', 90.0: 'Top', 180.0: 'Left', -90.0: 'Bottom'}
        t = 'switchtodesign; new; deleteall; \n'
        t+= 'addelement("Optical N Port S-Parameter"); createcompound; select("COMPOUND_1");\n'
        t+= 'component = "%s"; set("name",component); \n' % component_name
        import os
        if os.path.exists(svg_filename):
            t+= 'seticon(component,"%s");\n' %(svg_filename)
        else:
            print(" SiEPIC.lumerical.fdtd.component... missing SVG icon: %s" % svg_filename)
        t+= 'select(component+"::SPAR_1"); set("load from file", true);\n'
        t+= 'set("s parameters filename", "%s");\n' % (files_sparam[0])
        t+= 'set("load from file", false);\n'
        t+= 'set("passivity", "enforce");\n'
        t+= 'set("prefix", component);\n'
        t+= 'set("description", component);\n'
    
        # Add variables for Monte Carlo simulations:
        t+= 'addproperty(component, "MC_uniformity_thickness", "wafer", "Matrix");\n'
        t+= 'addproperty(component, "MC_uniformity_width", "wafer", "Matrix");\n'
        t+= 'addproperty(component, "MC_grid", "wafer", "Number");\n'
        t+= 'addproperty(component, "MC_resolution_x", "wafer", "Number");\n'
        t+= 'addproperty(component, "MC_resolution_y", "wafer", "Number");\n'
        t+= 'addproperty(component, "MC_non_uniform", "wafer", "Number");\n'
    
        t+= 'setposition(component+"::SPAR_1",100,-100);\n'
        count=0
        for p in pins:
            count += 1
            if p.rotation in [0.0, 180.0]:
                location = 1-(p.center.y-devrec_box.bottom+0.)/devrec_box.height()
        #      print(" p.y %s, c.bottom %s, location %s: " % (p.center.y,component.polygon.bbox().bottom, location) )
            else:
                location = (p.center.x-devrec_box.left+0.)/devrec_box.width()
                print(location)
            t+= 'addport(component, "%s", "Bidirectional", "Optical Signal", "%s",%s);\n' %(p.pin_name,port_dict2[p.rotation],location)
            t+= 'connect(component+"::RELAY_%s", "port", component+"::SPAR_1", "pin%s");\n' % (count, count)
        interconnect.eval(t)
    
    
        # for Monte Carlo simulations, copy model files, create the component script
        if FDTD_settings['Perform-final-corner-analysis']:
            # Copy files to the INTC Custom library folder
            interconnect.eval("out=customlibrary;")
            INTC_custom=interconnect.getv("out")
            INTC_files = os.path.join(INTC_custom, INTC_Lib, "source_data", component_name)
            if not(os.path.exists(INTC_files)):
                try:
                    os.makedirs(INTC_files)
                except:
                    pass
            from shutil import copy2
            for f in files_sparam:
                copy2(f, INTC_files)
    
            # Variables for the Monte Carlo component, linked to the top schematic
            t+='setexpression(component,"MC_uniformity_thickness","%MC_uniformity_thickness%");\n'
            t+='setexpression(component,"MC_uniformity_width","%MC_uniformity_width%");\n'
            t+='setexpression(component,"MC_grid","%MC_grid%");\n'
            t+='setexpression(component,"MC_resolution_x","%MC_resolution_x%");\n'
            t+='setexpression(component,"MC_resolution_y","%MC_resolution_y%");\n'
            t+='setexpression(component,"MC_non_uniform","%MC_non_uniform%");\n'
            interconnect.eval(t)
    
            script = ' \
    ############################################### \n\
    # SiEPIC compact model library (CML) \n\
    # custom generated component created by SiEPIC-Tools; script by Zeqin Lu, Xu Wang, Lukas Chrostowski  \n\
    ############################################### \n\
    \n\
    # nominal geometry:  \n\
    waveguide_width = %s; \n\
    waveguide_thickness = %s; \n\
    # S-parameter data file table \n\
    component = "%s"; table = "index_table"; \n\
    filename = %%local path%%+"/source_data/"+component+"/"+component+".xml";   \n\
    if (fileexists(filename)) { \n\
        \n\
        if (MC_non_uniform==1) { \n\
                # location of component on the wafer map \n\
            x=%%x coordinate%%; y=%%y coordinate%%; \n\
            x1_wafer = floor(x/MC_grid); y1_wafer = floor(y/MC_grid);  \n\
        \n\
                # geometry variation: \n\
            devi_width = MC_uniformity_width(MC_resolution_x/2 + x1_wafer, MC_resolution_y/2 + y1_wafer)*1e-9; \n\
            devi_thickness = MC_uniformity_thickness(MC_resolution_x/2 + x1_wafer, MC_resolution_y/2 + y1_wafer)*1e-9; \n\
        \n\
                # geometry for this MC run \n\
            waveguide_width = waveguide_width + devi_width;  # [m] \n\
            waveguide_thickness = waveguide_thickness + devi_thickness; # [m] \n\
        \n\
        } \n\
        \n\
        # design (input parameters) \n\
        design = cell(2); \n\
        design{1} = struct; design{1}.name = "width"; design{1}.value = waveguide_width; \n\
        design{2} = struct; design{2}.name = "height"; design{2}.value = waveguide_thickness;  \n\
        \n\
        # Load (interpolate for MC simulation) the S-Parameters \n\
        M = lookupreadnportsparameter(filename, table, design, "sparam"); \n\
        setvalue("SPAR_1","s parameters",M);   \n\
    } \n\
    ' % (pin_w0, pin_h0, component_name)
    
            # Script for the Monte Carlo component, to load S-Param data:
            interconnect.putv("script", script)
            t+='select(component); set("setup script", script);'
            interconnect.eval(t)
    
    
        # Add to library
        t = 'select(component); addtolibrary("%s",true);\n' % INTC_Lib
        t+= '?"created and added " + component + " to library %s";\n' % INTC_Lib
        interconnect.eval(t)

    print("Done generating s-param compact models...")
    return component_name, file_sparam, [], xml_filename, svg_filename

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gds_path = r"C:\Users\seanl\Downloads\test_dc.gds"
    process_file_lbr = r"C:\Users\seanl\Documents\01_UBC\Academics\Grad School\01_Work\PDK-Generator\Repo\PDK-Generator\yaml_processes\SiEPICfab_Royale.lbr"
    process_file_yml = r"C:\Users\seanl\Documents\01_UBC\Academics\Grad School\01_Work\PDK-Generator\Repo\PDK-Generator\yaml_processes\SiEPICfab-Royale-Process.yaml"
    verbose = True
    
    GUI_FDTD = GUI_FDTD_component_simulation(process_file_yml, parent=app.instance(), verbose=True)
    GUI_FDTD.exec_()
    generate_component_sparam(gds_path, process_file_lbr, process_file_yml, do_simulation = True, addto_CML = True, verbose = True, FDTD_settings = GUI_FDTD.FDTD_settings)
    
    sys.exit(app.exec_())
    