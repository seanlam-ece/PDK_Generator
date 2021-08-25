from common.lumerical_lumapi import lumapi
from Waveguide_geometry import WaveguideStripGeometry
from Waveguide_simulation import WaveguideStripSimulation
from drc_checks import DRCCheck
from lumgeo import generate_gds_from_pcell

import os

design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
# process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),r"yaml_processes\SiEPICfab-Grouse-Base.lbr")

def create_compact_model(process_file, hide = False):
    mode = lumapi.MODE(hide = hide)
    fdtd = lumapi.FDTD(hide = hide)
    WGSG = WaveguideStripGeometry(design_file, process_file)
    WGSS = WaveguideStripSimulation(design_file, process_file, mode=mode, fdtd=fdtd)
    
    width = WGSG.width
    radius = WGSG.radius   
    bezier = WGSG.bezier
    
    WGSS.generate_compact_model_file(width, radius, bezier)
    print("Done creating compact model...")
    
    mode.close()
    fdtd.close()
    
    return WGSS.compact_model_mapping
    
def run_design_process(process_file, hide = False):
    mode = lumapi.MODE(hide = hide)
    fdtd = lumapi.FDTD(hide = hide)
    decision = False
    
    while(decision == False):
        print("Design Process\n" +\
              "--------------\n" +\
              "1. Sweep neff and width\n" +\
              "2. Optimize width and neff for designed mode\n"+\
              "3. Given width, sweep bend loss and radius\n"+\
              "4. Select acceptable radius\n"+\
              "5. Given width and radius, sweep bend loss and bezier paramter\n"+\
              "6. Optimize bezier parameter for minimal bend loss\n"+\
              "7. Generate compact model files\n")
        
        print("SWEEP NEFF VS WIDTH")
        csv_file = input("neff vs width CSV File Path (Optional, skip if not available):\n")
        WGSG1 = WaveguideStripGeometry(design_file, process_file, mode)
        WGSS = WaveguideStripSimulation(design_file, process_file,mode=mode, fdtd=fdtd)
        if not csv_file:
            start_width = float(input("Start Width (um): "))
            end_width = float(input("End Width (um): "))
            width_step = float(input("Width Step (um): "))
        
            mapping = WGSG1.sweep_width([start_width, end_width], width_step)
            
            WGSS.neff_sweep_width_2D(mapping, True)
            opt_width = WGSS.optimize_width()
        else:
            opt_width = WGSS.optimize_width(csv_file)
        
        
        print("SWEEP BEND LOSS VS RADIUS")
        skip_sweep = input("Skip Radius Sweep? y/n\n ")
        WGSG2 = WaveguideStripGeometry(design_file, process_file, fdtd)
        if skip_sweep == 'n':
            start_radius = float(input("Start Radius (um): "))
            end_radius = float(input("End Radius (um): "))
            radius_step = float(input("Radius Step (um): "))
        
            mapping = WGSG2.sweep_radius(opt_width,[start_radius, end_radius], radius_step)
        
            WGSS.loss_sweep_bend_radii(mapping, opt_width, True)
            
        opt_radius = float(input("Optimal Radius (um): "))

        
        print("SWEEP BEZIER")
        csv_file = input("loss vs bezier CSV File Path (Optional, skip if not available):\n")
        if not csv_file:
            bezier_start = float(input("Start Bezier: "))
            bezier_end = float(input("End Bezier: "))
            bezier_step = float(input("Bezier Step: "))
            mapping = WGSG2.sweep_bezier(opt_width, opt_radius, [bezier_start, bezier_end], bezier_step)
        
            WGSS.loss_sweep_bezier(mapping, opt_radius, opt_width, True)
            opt_bezier = WGSS.optimize_bezier()
        else:
            opt_bezier = WGSS.optimize_bezier(csv_file)
        
        print("OPTIMAL PARAMETERS:\n")
        print("Width (um): {}".format(opt_width))
        print("Radius (um): {}".format(opt_radius))
        print("Bezier: {}".format(opt_bezier))
        
        print("CHECK DESIGN AND DRC")
        component_name = "Waveguide_w={}_r={}_b={}.gds".format(opt_width, opt_radius, opt_bezier)
        gds_path = os.path.join(WGSG2.gds_dir,component_name)
        generate_gds_from_pcell(gds_path, WGSG2.techname, WGSG2.libname, WGSG2.pcellname,
                                {"width": opt_width, "radius": opt_radius, "bezier": opt_bezier,
                                 "adiab": 1})
        
        DRC = DRCCheck()
        drc_decision = DRC.run_drc(WGSG2.techname, gds_path, component_name)
        
        if drc_decision == False:
            proceed = input("Proceed to compact model generation anyways? y/n\n")
            if proceed == 'y':
                decision = True
            else:
                decision = False
        else:
            design_goal_check = input("Check design goals. Proceed to compact model generation? y/n\n")
            if design_goal_check == 'y':
                decision = True
            elif design_goal_check == 'n':
                decision = False

    print("CREATE COMPACT MODEL FILES")
    WGSS.generate_compact_model_file(opt_width, opt_radius, opt_bezier)
    
    print("Done designing waveguide...")
    
    mode.close()
    fdtd.close()
    
    return WGSS.compact_model_mapping
