#Adds Materials + Creates Adiabatic Coupler Geometry for Adiabatic Coupler Sweep 

#General Purpose Libraries
import numpy as np

ac_geo = {
                "gap": 180e-9,
                "length":150e-6,

                "strip-wg":
                {
                    "material": "Si (Silicon) - Palik",
                    "input-width": 850e-9,
                    "output-width": 450e-9
                },
                
                "swg-wg":
                {
                    "material": "SWG_strip",
                    "input-width": 150e-9,
                    "output-width": 550e-9
                }

              }

materials = {
                "Si (Silicon) - Dispersive & Lossless":
                {
                    "type": "Lorentz",
                    "permittivity": 7.98737492,
                    "lorentz-linewidth": 1e8,
                    "lorentz-permittivity": 3.68799143,
                    "color": [0.85, 0, 0, 1] # Red
                },
                
                "Air (1)":
                {
                    "type": "Dielectric",
                    "refractive-index": 1,
                    "color": [0.85, 0.85, 0, 1]
                },
                
                "SiO2 (Glass) - Dispersive & Lossless":
                {
                    "type": "Lorentz",
                    "permittivity": 2.119881,
                    "lorentz-linewidth": 1e10,
                    "lorentz-resonance": 3.309238e13,
                    "lorentz-permittivity": 49.43721,
                    "color": [0.5, 0.5, 0.5, 1] # Grey
                },
                
                "SiO2 (Glass) - Const":
                {
                    "type": "Dielectric",
                    "permittivity": 1.444**2,
                    "color": [0.5, 0.5, 0.5, 1] # Grey
                },
                
                "SWG_strip":
                {
                    "type": "Dielectric",
                    "refractive-index": 2.73,
                    "color": [0.85, 0.5, 0, 1] # Red
                }
            }

L_io_wg = 5e-6 # Length of input/output waveguides
thick_Si = 0.22e-6
thick_Clad = 5e-6
thick_BOX = 5e-6
material_Clad  = "SiO2 (Glass) - Palik";
material_BOX  = "SiO2 (Glass) - Palik";

#Adding Materials into MODE/FDTD
def set_ac_materials(mode):
    for material, properties in materials.items():
        mode.setmaterial(mode.addmaterial(properties['type']), "name", material)
        #print(material)
        for prop, value in properties.items():
            #print("Setting {} to {}".format(prop, value))
            if prop == "permittivity":
                mode.setmaterial(material, "Permittivity", value)
            elif prop == "lorentz-linewidth":
                mode.setmaterial(material, "Lorentz Linewidth", value)
            elif prop == "lorentz-permittivity":
                mode.setmaterial(material, "Lorentz Permittivity", value)
            elif prop == "refractive-index":
                mode.setmaterial(material, "Refractive Index", value)
            elif prop == "color":
                mode.setmaterial(material, "color", np.array(value))
            elif prop == "type":
                pass
            #else:
                #print("Error: Cannot add {}...".format(prop))

#Set geometries for simulations 
def set_ac_geometry(mode, w6):
    
    #Adding BOX
    mode.addrect()
    mode.set("name", "BOX")
    mode.set("material", material_BOX)
    mode.set("x min", -L_io_wg - ac_geo['length']/2 - 10e-6)
    mode.set("x max", ac_geo['length']/2 + 20e-6)
    mode.set("y", 0)
    mode.set("y span", 40e-6)
    mode.set("z min", -thick_BOX)
    mode.set("z max", 0)
    mode.set("alpha", 0.2)
    
    #Adding cladding
    mode.addrect()
    mode.set('name','Cladding')
    mode.set("material",material_Clad)
    mode.set('x min', -L_io_wg - ac_geo['length']/2 - 10e-6)
    mode.set('x max', ac_geo['length']/2 + 20e-6)
    mode.set('y', 0)
    mode.set('y span',40e-6)
    mode.set('z min',0)
    mode.set('z max', thick_Clad)
    mode.set("override mesh order from material database", 1)
    mode.set("mesh order",3)  # similar to "send to back", put the cladding as a background.
    mode.set("alpha", 0.2)
    
    #Adding Slab Waveguide Taper
    mode.eval("V_Top=matrix(4,2);")
    mode.eval("V_Top=[-{L_SWG}/2, {WGtop_width1}/2; {L_SWG}/2, {WGtop_width2}/2; {L_SWG}/2,"\
              "-{WGtop_width2}/2; -{L_SWG}/2,-{WGtop_width1}/2];".format(L_SWG=ac_geo['length'],
                                                                         WGtop_width1=ac_geo['strip-wg']['input-width'],
                                                                         WGtop_width2=ac_geo['strip-wg']['output-width']))
    mode.addpoly()
    mode.set('name','SWG_Bus_taper')
    mode.set("material", ac_geo['strip-wg']['material'])
    mode.set('x', 0)
    mode.set('y',0)
    mode.set('z min',0)
    mode.set('z max',thick_Si)
    mode.eval("set('vertices',V_Top);")
    
    mode.eval("V_Bottom=matrix(4,2);")
    mode.eval("V_Bottom=[-{L_SWG}/2,-{WGtop_width1}/2-{gap}; {L_SWG}/2,-{WGtop_width2}/2-{gap};"\
              "{L_SWG}/2,-{WGtop_width2}/2-{gap}-{WGbottom_width2}; -{L_SWG}/2,"\
              "-{WGtop_width1}/2-{gap}-{WGbottom_width1}];".format(L_SWG=ac_geo['length'],
                                                                   WGtop_width1=ac_geo['strip-wg']['input-width'],
                                                                   WGtop_width2=ac_geo['strip-wg']['output-width'],
                                                                   WGbottom_width1=ac_geo['swg-wg']['input-width'],
                                                                   WGbottom_width2=w6,
                                                                   gap=ac_geo['gap']))
    #Adding Slab Waveguide Coupling Taper
    mode.addpoly()
    mode.set('name','SWG_Coupling_taper')
    mode.set("material", ac_geo['swg-wg']['material'])
    mode.set('x', 0)
    mode.set('y',0)
    mode.set('z min',0)
    mode.set('z max',thick_Si)
    mode.eval("set('vertices',V_Bottom);")
    
    #Adding Input Waveguide
    mode.addrect()
    mode.set('name','Input_WG1'); 
    mode.set("material", ac_geo['strip-wg']['material']);
    mode.set('x min',-L_io_wg-ac_geo['length']/2);
    mode.set('x max',-ac_geo['length']/2);
    mode.set('y',0);
    mode.set('y span',ac_geo['strip-wg']['input-width']);
    mode.set('z min',0); 
    mode.set('z max',thick_Si);
    
    #Adding Output Waveguide
    mode.addrect()
    mode.set('name','Output_WG1'); 
    mode.set("material", ac_geo['strip-wg']['material']);
    mode.set('x min', ac_geo['length']/2);
    mode.set('x max', L_io_wg+ac_geo['length']/2);
    mode.set('y',0);
    mode.set('y span',ac_geo['strip-wg']['output-width']);
    mode.set('z min',0); 
    mode.set('z max',thick_Si);
    
    mode.addrect()
    mode.set('name','Output_WG2'); 
    mode.set("material", ac_geo['swg-wg']['material']);
    mode.set('x min', ac_geo['length']/2);
    mode.set('x max', L_io_wg+ac_geo['length']/2);
    mode.set('y',-ac_geo['gap']-ac_geo['strip-wg']['output-width']/2-w6/2);
    mode.set('y span',w6);
    mode.set('z min',0); 
    mode.set('z max',thick_Si);
    
    #Adding EME solver 
    mode.addeme();
    mode.set("x min",-77.5e-6);
    mode.set("y", 0);        
    mode.set("y span", 40e-6);
    mode.set("z",0.1e-6);
    mode.set("z span",1.2e-6);
    mode.set("number of cell groups",3);
    mode.eval("set('group spans',[2.5e-6;150e-6;2.5e-6]);")
    mode.eval("set('cells',[1;10;1]);")
    mode.eval("set('subcell method',[0;1;0]);")

    #EME Solver: Port 1
    mode.select("EME::Ports::port_1");
    mode.set("use full simulation span",1);
    mode.set("y",0);
    mode.set("y span",5.5e-6);
    mode.set("z",0);
    mode.set("z span",7e-6);
    #mode.set("mode selection","fundamental TE and TM mode");
    mode.set("mode selection","user select");
    mode.seteigensolver("use max index",1)
    mode.seteigensolver("number of trial modes",5)
    mode.eval("updateportmodes([1,2]);")

    #EME Solver: Port 2
    mode.select("EME::Ports::port_2");
    mode.set("use full simulation span",1);
    mode.set("y",0);
    mode.set("y span",5.5e-6);
    mode.set("z",0);
    mode.set("z span",7e-6)
    mode.set("mode selection","user select");
    mode.seteigensolver("use max index",1)
    mode.seteigensolver("number of trial modes",5)
    mode.eval("updateportmodes([1,2]);")
    
    #Adding mesh region
    mode.addmesh();  
    mode.set("name", 'mesh');
    mode.set("x", 0);         
    mode.set("x span", 155e-06);
    mode.set("y", 0e-06);         
    mode.set("y span",14e-06);
    mode.set("z", 0.1e-6);  
    mode.set("z span", 0.8e-6); 
    mode.set("dx", 0.05e-06); 
    mode.set("dy", 0.02e-06); 
    mode.set("dz", 0.02e-06); 
    mode.save("adiabatic_mode_sweep")
    
    #Run EME
    mode.run()

def set_sweep(mode):  
    #Run and create s parameter sweep 
    mode.addsweep(3)
    mode.setsweep("s-parameter sweep", "name", "s-parameter sweep")
    mode.setsweep("s-parameter sweep", "Number of points", 1)
    mode.runsweep("s-parameter sweep")
    S = mode.getsweepresult("s-parameter sweep","user s matrix")
    s31 = S['user s matrix'][0][2][0]
    s42 = S['user s matrix'][1][3][0]
    return [abs(s31)**2, abs(s42)**2]