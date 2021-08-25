#PSR Bitaper Length Sweep Simulation Recipe +  Photonic Components + Adding Layers 

#General Purpose Libraries
try:
    import matplotlib.pyplot as plt
except:
    import pip
    pip.main(['install', 'matplotlib'])
    import matplotlib.pyplot as plt


#Defining wafer and waveguide structure
Clad_thickness = 4.0e-6; 
BOX_thickness  = 2.0e-6;
LA=35e-6;
taper_length=1e-6;
slab_thickness=0.09e-6;
wg_thickness=0.22e-6;
wg_width=0.5e-6;
slab_ws = 0.5e-6;
Xmin = -20e-6;  

#Bitaper length sweep setup 
class bitaper_length_sweep:
    
    #EME Solver Setup
    def eme_solver(mode):
        
        mode.addeme();
        mode.set("x min",0);
        mode.set("y", 0.2e-6);        
        mode.set("y span", 8e-6);
        mode.set("z",0.11e-6);
        mode.set("z span",0.66e-6);
        mode.set("number of cell groups",3);
        mode.eval("set('group spans',[1e-06;55e-06;1e-06]);")
        mode.eval("set('cells',[1;50;1]);")
        mode.eval("set('subcell method',[0;1;0]);")
        
        #EME Solver: Port 1
        mode.select("EME::Ports::port_1");
        mode.set("use full simulation span",1);
        mode.set("y",0);
        mode.set("y span",5.5e-6);
        mode.set("z",0);
        mode.set("z span",7e-6);
        mode.set("mode selection","fundamental TM mode");
        
        #EME Solver: Port 2
        mode.select("EME::Ports::port_2");
        mode.set("use full simulation span",1);
        mode.set("y",0);
        mode.set("y span",5.5e-6);
        mode.set("z",0);
        mode.set("z span",7e-6)
        mode.set("mode selection","user select");
        mode.seteigensolver("number of trial modes",5)
        mode.updateportmodes(2)
        
        #Adding Mesh Region
        mode.addmesh();  
        mode.set("name", 'mesh1');
        mode.set("x", 47.5e-06);         
        mode.set("x span", 95e-06);
        mode.set("y", 0.2e-06);         
        mode.set("y span",8e-06);
        mode.set("z", 0.11e-6);  
        mode.set("z span", 0.66e-6); 
        mode.set("dx", 0.02e-06); 
        mode.set("dy", 0.01e-06); 
        mode.set("dz", 0.01e-06); 
        
    #Run EME Solver 
    @staticmethod
    def run_eme(mode,x):
        
        #Saving File 
        mode.save("automated_eme_transmission_sweep");
        
        #Run
        mode.run();
        mode.setemeanalysis("propagation sweep",1);
        mode.setemeanalysis("parameter","group span 2");
        mode.setemeanalysis("start",10e-06);
        mode.setemeanalysis("stop",55e-06);
        mode.setemeanalysis("number of points", 50);
        
        #Run sweep 
        mode.emesweep();
        
        #Obtain Propagation Sweep Result
        S = mode.getemesweep('S');
        
        #Plot s21 vs group span
        s21 = S['s21'];
        group_span = S['group_span_2']*10e5;
        plt.plot(group_span,abs(s21)**2, label = "LB = " + str(x*10e5) + "um");
        plt.title('LA/LB Length Sweep');
        plt.xlabel('LA (um)');
        plt.ylabel("Mode Transmission Efficiency (%)");
        plt.legend();
        
        #Optimizations and Simulations for LA 
        max_efficiency = 0
        best_LA = 0
        difference = 1
        prev_val = 0
        for x, y in zip(group_span, abs(s21)**2):
            if y > max_efficiency:
                difference = y - prev_val
                max_efficiency = y
                if y - prev_val>0.0003:
                    best_LA = x
            prev_val = y
            
        return [best_LA, max_efficiency]

    #Draws the photonic components     
    def setup_polygons(mode, LB, width_sweep):
        
        #Adding Cladding
        mode.addrect();
        mode.set("name", "Clad");
        mode.set("material","SiO2 (Glass) - Palik");
        mode.set("x min", Xmin); 
        mode.set("x max", LA+LB+20e-6);
        mode.set("z min", 0);          
        mode.set("z max", Clad_thickness);
        mode.set("y min", -8e-6); 
        mode.set("y max", 8e-6);
        mode.set("override mesh order from material database",1);
        mode.set("mesh order",3); 
        mode.set("alpha", 0.2);

        #Adding Buried Oxide
        mode.addrect(); 
        mode.set("name", "BOX"); 
        mode.set("material", "SiO2 (Glass) - Palik");
        mode.set("x min", Xmin);       
        mode.set("x max", LA+LB+20e-6);
        mode.set("z min", -BOX_thickness); 
        mode.set("z max", 0);
        mode.set("y min", -8e-6);              
        mode.set("y max", 8e-6);
        mode.set("alpha", 0.2);

        #Adding Silicon Wafer
        mode.addrect();
        mode.set("name", "Wafer"); 
        mode.set("material", "Si (Silicon) - Palik");
        mode.set("x min", Xmin);       
        mode.set("x max", LA+LB+20e-6);
        mode.set("z max", -BOX_thickness); 
        mode.set("z min", -BOX_thickness-2e-6);
        mode.set("y min", -8e-6);              
        mode.set("y max", 8e-6);
        mode.set("alpha", 0.2);

        #Adding Input Waveguide
        mode.addrect();
        mode.set("name", "Input_wg");
        mode.set("material","Si (Silicon) - Palik");
        mode.set("x min", -2e-6); 
        mode.set("x max", 0);
        mode.set("z min", 0); 
        mode.set("z max", wg_thickness);
        mode.set("y min", 0); 
        mode.set("y max", width_sweep[0]);
        
        #Adding Output Waveguide 
        mode.addrect();
        mode.set("name", "Output_wg");
        mode.set("material","Si (Silicon) - Palik");
        mode.set("x min", LA+LB); 
        mode.set("x max", LA+LB+2e-6);
        mode.set("z min", 0); 
        mode.set("z max", wg_thickness);
        mode.set("y min", (width_sweep[0]-width_sweep[2])/2); 
        mode.set("y max", (width_sweep[2]-width_sweep[0])/2+width_sweep[0]);

        #Adding Bitaper (Strip)
        mode.eval("M=matrix(6,2);")
        mode.eval("M(1,1:2)=[0,0];")
        mode.eval("M(2,1:2)=["+str(LA)+","+str((width_sweep[0]-width_sweep[1])/2)+"];")
        mode.eval("M(3,1:2)=["+str(LA+LB)+"," + str((width_sweep[0]-width_sweep[2])/2)+"];")
        mode.eval("M(4,1:2)=["+str(LA+LB)+","+str((width_sweep[2]-width_sweep[0])/2+width_sweep[0])+"];")
        mode.eval("M(5,1:2)=["+str(LA)+","+str((width_sweep[1]-width_sweep[0])/2+width_sweep[0])+"];")
        mode.eval("M(6,1:2)=[0,"+str(width_sweep[0])+"];")
        
        mode.addpoly();
        mode.set("name", "Taper_strip");
        mode.set("x",0);
        mode.set("y",0);
        mode.set("z min", 0); 
        mode.set("z max", wg_thickness);
        mode.eval("set('vertices',M);")
        mode.set("material","Si (Silicon) - Palik");

        #Adding Bitaper (slab)
        mode.eval("V=matrix(6,2);")
        mode.eval("V(1,1:2)=[0,0];")
        mode.eval("V(2,1:2)=["+str(LA)+","+str((width_sweep[0]-width_sweep[1])/2-slab_ws)+"];")
        mode.eval("V(3,1:2)=["+str(LA+LB)+","+str((width_sweep[0]-width_sweep[2])/2)+"];")
        mode.eval("V(4,1:2)=["+str(LA+LB)+","+str((width_sweep[2]-width_sweep[0])/2+width_sweep[0])+"];")
        mode.eval("V(5,1:2)=["+str(LA)+","+str((width_sweep[1]-width_sweep[0])/2+width_sweep[0]+slab_ws)+"];")
        mode.eval("V(6,1:2)=[0,"+str(width_sweep[0])+"];")
        
        mode.addpoly();
        mode.set("name", "Taper_slab");
        mode.set("x",0);
        mode.set("y",0);
        mode.set("z min", 0); 
        mode.set("z max", slab_thickness);
        mode.eval("set('vertices',V);")
        mode.set("material","Si (Silicon) - Palik");


