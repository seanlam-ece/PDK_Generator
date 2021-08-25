from xml.dom import minidom
import xml.etree.ElementTree as ET
import platform
import os

def convert_to_macro(macro_dict):
    """Convert dict to KLayout macro
    
    Parameters
    ----------
    macro_dict : dict
        Keys = subelement tags. Values = subelement text. The macro dict contains
        key-value pairs associated to KLayout macro meta data.

    Returns
    -------
    str
        A string representing the KLayout macro.

    Examples
    --------
    The following shows the format of the macro dict and how to use it to print
    the resultant macro string:
        
    >>> mdict = {"text": "# Code in Ruby or Python depending on macro",
                 "description": "Short Description of Macro",
                 "autorun": "false",
                 "autorun-early": "false",
                 "shortcut": "Shift+X",
                 "show-in-menu": "true",
                 "menu-path": "siepic_menu.layout.begin",
                 "interpreter": "python"}
    >>> print(convert_to_macro(mdict))
    
    """
    # Create root
    root = ET.Element("klayout-macro")

    # Create empty dictionary of tags that represent sub elements to root
    subroot_elements = dict.fromkeys(["description", "version", "category","prolog", "epilog",\
                              "doc", "autorun", "autorun-early", "shortcut", "show-in-menu",\
                              "group-name", "menu-path", "interpreter", "dsl-interpreter-name",\
                              "text"])

    # Create sub elements to root
    for tag in subroot_elements.keys():
        subroot_elements[tag] = ET.SubElement(root, tag)
        if macro_dict.get(tag, None) != None:
            subroot_elements[tag].text = macro_dict.get(tag)

    # Prettify the XML then return the raw text
    return prettify(root)

## Returns a pretty-printed XML string for elem
def prettify(root):
    """Convert XML tree to pretty-printed XML string
    
    Parameters
    ----------
    root : xml.etree.ElementTree.Element
        Root element of an XML tree.

    Returns
    -------
    str
        A string representing a pretty-printed XML doc.

    """
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def get_klayout_app_path():
    """Get KLayout application executable path
    
    Searches for KLayout application executable path locally (may take some time)

    Returns
    -------
    string
        Path for KLayout application executable

    """
    print("Finding KLayout application...")
    system = platform.system()
    if system == 'Windows':
        for root, dirs, files in os.walk("C:"+os.sep):
            for file in files:
                if file.endswith(".exe") and "klayout_app" in file:
                    print("KLAYOUT APPLICATION PATH:")
                    print(os.path.join(root, file) + "\n")
                    return os.path.join(root, file)
    elif system == "Darwin":
        location = os.popen("find /Applications -name klayout.app").read()
        if location:
            print("KLAYOUT APPLICATION LOCATION:")
            print(location  + "\n")
            return location
    print("Could not find KLayout app...\n")


def get_klayout_folder_path():
    """Get KLayout folder path
    
    Searches for KLayout folder path locally (may take some time)

    Returns
    -------
    string
        Path for KLayout folder

    """
    print("Finding KLayout folder...")
    system = platform.system()
    if system == 'Windows':
        for root, dirs, files in os.walk("C:"+os.sep+"Users"):
            for file in files:
                if root.split(os.sep)[-1] == "KLayout" and file == "klayoutrc":
                    print("KLAYOUT FOLDER:")
                    print(root + "\n")
                    return root
            
    elif system == "Darwin":
        for root, dirs, files in os.walk("/Users"):
            if root.split(os.sep)[-1] == ".klayout":
                print("KLAYOUT FOLDER:")
                print(root + "\n")
                return root
    print("Could not find KLayout folde'r...\n")  
    
def export_gds(lum_app, filename, top_cell_name, layer_def,
               n_circle = 64, n_ring = 64, n_custom = 64, n_wg = 64,
               round_to_nm = 1, grid = 1e-9, max_objects = 10000):
    """Export layout in Lumerical application to GDS II
    
    Lumerical_GDS_auto_export.lsfx must be present and 
    in the same working directory as the Lumerical application

    Parameters
    ----------
    lum_app : lumapi.FDTD() or lumapi.MODE()
        Lumerical application object from Lumerical's python API
    filename : string
        Name of GDS file (i.e. 'y_branch')
    top_cell_name : string
        Name of top cell in GDS file (i.e. 'model')
    layer_def : list of int
        A list of layer definitions defined as:
            [layer_number0, layer_datatype0, z_min0, z_max0,
            layer_number1, layer_datatype1, z_min1, z_max1,
            layer_number2, layer_datatype2, z_min2, z_max2,
            ...          , ...                    , ...   ]
    n_circle : integer, optional
        number of sides to use for circle approximation. The default is 64.
    n_ring : integer, optional
        number of slices to use for ring approximation. The default is 64.
    n_custom : integer, optional
        number of slices to use for custom approximation. The default is 64.
    n_wg : integer, optional
        number of slices to use for waveguide approximation. The default is 64.
    round_to_nm : integer, optional
        round the z and z span to the nearest integer of nm. The default is 1.
    grid : double, optional
        snap to grid. The default is 1e-9.
    max_objects : integer, optional
        the maximum number of objects within the workspace (Increasing this will increase export time). The default is 10000.

    Returns
    -------
    string
        File path of GDS file generated

    """
    
    print("Exporting from Lumerical application to GDS II...")
    layer_def_str = "layer_def = ["
    for i in range(0,len(layer_def)):
        if i == (len(layer_def) - 1):
            # Insert end bracket and semi-colon at end of array
            layer_def_str = layer_def_str + str(layer_def[i]) + "];"
        elif (i + 1) % 4 == 0:
            # Insert semi-colon after every 4 params
            layer_def_str = layer_def_str + str(layer_def[i]) + ";"
        else:
            layer_def_str = layer_def_str + str(layer_def[i]) + ","
       
    lsf_script = str("gds_filename = '{}.gds';".format(filename) +
                     "top_cell = '{}';".format(top_cell_name) +
                     layer_def_str.format(-220.0e-9/2, 220.0e-9/2) +
                     "n_circle = {};".format(n_circle) +
                     "n_ring = {};".format(n_ring) +
                     "n_custom = {};".format(n_custom) +
                     "n_wg = {};".format(n_wg) +
                     "round_to_nm = {};".format(round_to_nm) +
                     "grid = {};".format(grid) +
                     "max_objects = {};".format(max_objects) +
                     "Lumerical_GDS_auto_export;")
    #return lsf_script
    # Run lsf script to export gds
    lum_app.cd(os.getcwd())
    lum_app.eval(lsf_script)
    return os.path.join(os.getcwd(), filename+".gds")

def open_klayout(klayout_app_path=None, filepath=None):
    """Open KLayout application
    
    If filepath to GDS file is specified, opens the GDS file in KLayout

    Parameters
    ----------
    klayout_app_path : string, optional
        Filepath of the Klayout application. The default is None.
    filepath : string, optional
        Filepath of the GDS file. The default is None.

    Returns
    -------
    None.

    """
    if not klayout_app_path:
        klayout_app_path = get_klayout_app_path()
    
    if filepath:
        print("Opening {} in KLayout...".format(filepath))
        subprocess.Popen([klayout_app_path, filepath])
    else:
        print("Opening KLayout...")
        subprocess.Popen(klayout_app_path)
    print("KLayout opened...")