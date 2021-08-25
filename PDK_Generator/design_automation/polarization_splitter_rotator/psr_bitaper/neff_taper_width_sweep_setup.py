#PSR Bitaper Width Sweep Simulation Recipe +  Photonic Components + Adding Layers 

#General Purpose Libraries
import numpy as np
from scipy.constants import c

lam_c = 1.550e-6

#Wafer and Waveguide Structure Variables
thick_Clad = 2.0e-6
thick_Si   = 0.22e-6
thick_BOX  = 2.0e-6    
thick_Slab = 0.09e-6        
width_ridge = 0.45e-6
width_slab = 0.5e-6

#Materials Used
material_Clad = 'SiO2 (Glass) - Palik'              
material_BOX  = "SiO2 (Glass) - Palik"
material_Si   = "Si (Silicon) - Palik"

#Simulation Parameters
wavelength    = 1.55e-6   
meshsize      = 10e-9
modes         = 4           
width_margin  = 2.0e-6	 
height_margin = 1.0e-6  

#Dimensions    
Xmin = -2e-6;  Xmax = 2e-6; 
Zmin = -height_margin;  Zmax = thick_Si + height_margin;
Y_span = 2*width_margin + width_ridge; Ymin = -Y_span/2;  Ymax = -Ymin;

#Class that adds all materials
class material_setup:
    
    def add_material(mode):
         
        matname = "Air (1)";
        if 1:
            newmaterial = mode.addmaterial("Dielectric"); 
        mode.setmaterial(newmaterial,"name",matname);
        mode.setmaterial(matname,"Refractive Index",1);
        #mode.setmaterial(matname,"color",[0.85, 0.85, 0, 1]);
    
        matname = "Si (Silicon) - Dispersive & Lossless";
        newmaterial = mode.addmaterial("Lorentz");
        mode.setmaterial(newmaterial,"name",matname);
        mode.setmaterial(matname,"Permittivity",7.98737492);
        mode.setmaterial(matname,"Lorentz Linewidth",1e8);
        mode.setmaterial(matname,"Lorentz Permittivity",3.68799143);
        #mode.setmaterial(matname,"color",[0.85, 0, 0, 1]); # red

        matname = "SiO2 (Glass) - Dispersive & Lossless";
        newmaterial = mode.addmaterial("Lorentz");
        mode.setmaterial(newmaterial,"name",matname);
        mode.setmaterial(matname,"Permittivity",2.119881);
        mode.setmaterial(matname,"Lorentz Linewidth",1e10);
        mode.setmaterial(matname,"Lorentz Resonance",3.309238e+13);
        mode.setmaterial(matname,"Lorentz Permittivity", 49.43721);
        #mode.setmaterial(matname,"color",[0.5, 0.5, 0.5, 1]); # grey

        matname = "SiO2 (Glass) - Const";
        newmaterial = mode.addmaterial("Dielectric");
        mode.setmaterial(newmaterial,"name",matname);
        mode.setmaterial(matname,"Permittivity",1.444*1.444);
        #mode.setmaterial(matname,"color",[0.5, 0.5, 0.5, 1]); # grey

        matname = "SWG_strip";
        if 1: 
            newmaterial = mode.addmaterial("Dielectric"); 
        mode.setmaterial(newmaterial,"name",matname);
        mode.setmaterial(matname,"Refractive Index",2.73); 
        #mode.setmaterial(matname,"color",[0.85, 0.5, 0, 1]);
        mode.switchtolayout()
    

#Class that draws the photonic components and sets up FDE sweep    
class width_sweep_setup:
    
    #Adding mesh and FDE regions
    def wg_2D_func(mode):
    
        #Adding mesh regions
        mode.addmesh(); 
        mode.set("name", 'mesh1'); 
        #set("solver type", "2D X normal");
        mode.set("x max", Xmax);        
        mode.set("x min", Xmin);
        mode.set("y", 0);         
        mode.set("y span", width_ridge);
        mode.set("z min", -0.02e-6);  
        mode.set("z max", thick_Si+0.02e-6); 
        mode.set("dx", meshsize); 
        mode.set("dy", meshsize*0.5);
        mode.set("dz", meshsize*0.5);
    
        mode.addmesh();  
        mode.set("name", 'mesh2');
        #set("solver type", "2D X normal");
        mode.set("x max", Xmax);         
        mode.set("x min", Xmin);
        mode.set("y", 0);         
        mode.set("y span", width_slab);
        mode.set("z min", -0.02e-6);  
        mode.set("z max", thick_Slab+0.02e-6); 
        mode.set("dx", meshsize); 
        mode.set("dy", meshsize*0.5);
        mode.set("dz", meshsize*0.5);
        # add 2D mode solver (waveguide cross-section)
        
        #Adding FDE solver
        mode.addfde();  
        mode.set("solver type", "2D X normal");
        mode.set("x", 0);  
        mode.set("y", 0);         
        mode.set("y span", Y_span);
        mode.set("z max", Zmax);  
        mode.set("z min", Zmin);
        mode.set("wavelength", wavelength);   
        mode.set("solver type","2D X normal");
        mode.set("define y mesh by","maximum mesh step"); 
        mode.set("dy", meshsize);
        mode.set("define z mesh by","maximum mesh step"); 
        mode.set("dz", meshsize);
        mode.set("number of trial modes",modes);

    #Adding Photonic Compoents
    def wg_2D_draw(mode):
        
        #Adding cladding
        mode.addrect(); 
        mode.set("name","Clad");  
        mode.set("y", 0);              
        mode.set("y span", Y_span+1e-6);
        mode.set("z min", 0);          
        mode.set("z max", thick_Clad);
        mode.set("x min", Xmin);       
        mode.set("x max", Xmax);
        mode.set("override mesh order from material database",1);
        mode.set("mesh order",3); 
        mode.set("alpha", 0.2);
        mode.set('material', material_Clad);

        #Adding Buried Oxide
        mode.addrect(); 
        mode.set("name", "BOX"); 
        mode.set("material", material_BOX);
        mode.set("x min", Xmin);       
        mode.set("x max", Xmax);
        mode.set("z min", -thick_BOX);
        mode.set("z max", 0);
        mode.set("y", 0);              
        mode.set("y span", Y_span+1e-6);
        mode.set("alpha", 0.1);
    
        #Adding Silicon Wafer
        mode.addrect(); 
        mode.set("name", "Wafer"); 
        mode.set("material", material_Si);
        mode.set("x min", Xmin);       
        mode.set("x max", Xmax);
        mode.set("z max", -thick_BOX); 
        mode.set("z min", -thick_BOX-2e-6);
        mode.set("y", 0);              
        mode.set("y span", Y_span+1e-6);
        mode.set("alpha", 0.1);

        #Adding Waveguide
        mode.addrect(); 
        mode.set("name", "waveguide"); 
        mode.set("material",material_Si);
        #set("index",3.2);
        mode.set("y", 0);        
        mode.set("y span", width_ridge);
        mode.set("z min", 0);    
        mode.set("z max", thick_Si);
        mode.set("x min", Xmin); 
        mode.set("x max", Xmax);

        #Adding Slab Waveguide 
        mode.addrect(); 
        mode.set("name", "slab"); 
        mode.set("material",material_Si);
        if thick_Slab==0:
            mode.set("y min", 0);     
            mode.set("y max", 0);
        else:  
            mode.set("y", 0);         
            mode.set("y span", width_slab);
        mode.set("z min", 0);      
        mode.set("z max", thick_Slab);
        mode.set("x min", Xmin);   
        mode.set("x max", Xmax);
        mode.set("alpha", 0.8);
        

        

