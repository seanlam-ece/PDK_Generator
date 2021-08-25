from . import *

#import numpy as n
MODULE_NUMPY = False

def pin(w,pin_text, trans, LayerPinRecN, dbu, cell):
  """
  w: Waveguide Width, e.g., 500 (in dbu)
  pin_text: Pin Text, e.g., "pin1"
  trans: e.g., trans =  Trans(0, False, 0, 0)  - first number is 0, 1, 2, or 3.
  pinrec: PinRec Layer, e.g., layout.layer(TECHNOLOGY['PinRec']))
  devrec: DevRec Layer, e.g., layout.layer(TECHNOLOGY['DevRec']))
  """
  
  # Create the pin, as short paths:
  pin = trans*Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], w)
  cell.shapes(LayerPinRecN).insert(pin)
  text = Text (pin_text, trans)
  shape = cell.shapes(LayerPinRecN).insert(text)
  shape.text_size = w*0.8

  print("Done drawing the layout for - pin" )


def linspace_without_numpy(low, up, length):
    step = ((up-low) * 1.0 / length)
    return [low+i*step for i in range(length)]

def layout_waveguide_rel(cell, layer, start_point, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # start_point: starting vertex for the waveguide
    # points: array of vertices, relative to start_point
    # w: waveguide width
    
    # example usage:
    # cell = Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_rel(cell, LayerSi, [0,0], points, 0.5, 10)

    
    print("* layout_waveguide_rel(%s, %s, %s, %s)" % (cell.name, layer, w, radius) )

    ly = cell.layout() 
    dbu = cell.layout().dbu

    start_point=[start_point[0]/dbu, start_point[1]/dbu]

    a1 = []
    for p in points:
      a1.append (DPoint(float(p[0]), float(p[1])))
  
    wg_path = DPath(a1, w)

    npoints = points_per_circle(radius/dbu)
    param = { "npoints": npoints, "radius": float(radius), "path": wg_path, "layer": layer }

    pcell = ly.create_cell("ROUND_PATH", "Basic", param )

    # Configure the cell location
    trans = Trans(Point(start_point[0], start_point[1]))

    # Place the PCell
    cell.insert(CellInstArray(pcell.cell_index(), trans))


def layout_waveguide_abs(cell, layer, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # points: array of vertices, absolute coordinates on the current cell
    # w: waveguide width
    
    # example usage:
    # cell = Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_abs(cell, LayerSi, points, 0.5, 10)

    if MODULE_NUMPY:  
      # numpy version
      points=n.array(points)  
      start_point=points[0]
      points = points - start_point  
    else:  
      # without numpy:
      start_point=[]
      start_point.append(points[0][0])
      start_point.append(points[0][1]) 
      for i in range(0,2):
        for j in range(0,len(points)):
          points[j][i] -= start_point[i]
    
    layout_waveguide_rel(cell, layer, start_point, points, w, radius)

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