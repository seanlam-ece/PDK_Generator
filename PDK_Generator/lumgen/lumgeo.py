from common.common_methods import get_klayout_app_path
import klayout.db as db

import os
import subprocess

def generate_lum_geometry(lum_app, process_file, gds_file):
    ''' Generate geometry in lumerical
    
    Lumerical's Layer Builder is used to generate the geometry.
    
    Parameters
    ----------
    lum_app : lumapi
        Lumerical application object (MODE, FDTD, etc.)
    process_file : str
        Absolute path to Lumerical .lbr process file
    gds_file : str
        Absolute path of GDS file
    
    Returns
    -------
    None.
    
    '''
    buffer = 6e-6
    
    lum_app.deleteall()
    lum_app.addlayerbuilder()
    
    ly = db.Layout()
    ly.read(gds_file)
    
    width = ly.top_cell().bbox().width()*1e-9
    height = ly.top_cell().bbox().height()*1e-9
    
    lum_app.set("x span", width*2 + buffer)
    lum_app.set("y span", height*2 + buffer)
    
    lum_app.loadprocessfile(process_file)
    lum_app.loadgdsfile(gds_file)  

def generate_gds_from_pcell(gds_path, techname, libname, pcellname, params = {}):
    if not hasattr(generate_gds_from_pcell, "klayout_app_path"):
        generate_gds_from_pcell.klayout_app_path = get_klayout_app_path()
    if not hasattr(generate_gds_from_pcell, "create_gds_klayout_script"):
        generate_gds_from_pcell.create_gds_klayout_script = os.path.join(os.path.dirname(os.path.abspath(__file__)),"create_gds_klayout.py")
        
    klayout_app_path = generate_gds_from_pcell.klayout_app_path
    create_gds_klayout_script = generate_gds_from_pcell.create_gds_klayout_script
    
    # Create params string
    params_str = "params={"
    for param, val in params.items():
        params_str += "\""+param+"\": "+str(val)+"," 
    params_str = params_str[:-1] + "}" # remove last comma
    
    command = ["{}".format(klayout_app_path),
               "-r", "{}".format(create_gds_klayout_script), # Run script
               "-rd", "techname={}".format(techname), 
               "-rd", "libname={}".format(libname),
               "-rd", "pcellname={}".format(pcellname),
               "-rd", "out_dir={}".format(gds_path),
               "-rd", params_str]
    cmd_str = ""
    for cmd in command:
        cmd_str = cmd_str + cmd + " "
    subprocess.run(command, shell=True)
    print(cmd_str + "\n")
    
    return gds_path

def clear_all_gds(directory):
    ''' Clear directory of GDS files
    

    Returns
    -------
    None.

    '''
    for file in os.listdir(directory):
        if file.endswith('.gds'):
            os.remove(file)
    print("Removed all GDS files in %s" % directory)