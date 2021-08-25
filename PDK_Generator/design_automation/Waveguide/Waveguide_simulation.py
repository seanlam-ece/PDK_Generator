from Waveguide_geometry import WaveguideStripGeometry
from math import log10, pi
from scipy.interpolate import make_interp_spline
from datetime import datetime
from shutil import copyfile
try:
    from lumgen.lumgeo import generate_lum_geometry
except:
    from lumgeo import generate_lum_geometry
from common.common_methods import prettify
import xml.etree.ElementTree as ET
import numpy as np
import yaml
import matplotlib.pyplot as plt
import csv
import os


class WaveguideStripSimulation():
    
    def __init__(self, design_file, process_file, mode = None, fdtd = None):
        self.design_file = design_file
        self.process_file = process_file
        self.mode = mode
        self.fdtd = fdtd
        self.interpolation_points = 10000
        
        self.width_margin = 2e-6 # distance from edge of wg to edge of sim region (m)
        self.height_margin = 1e-6 # distance from edge of wg to edge of sim region (m)
        
        self.boundary_size = 150e-6 # Max size of waveguide pcell (m)
        self.boundary_margin = 2e-6 # distance from edge of waveguide pcell to fdtd region (m)
        self.bend_buffer_distance = 1e-6 # distance from bend to power monitor (m)
        self.mode_expansion_to_power_monitor = 0.1e-6 # distance from power monitor to mode expansion monitor (m)
        
        self.bend_to_straight_margin = 10.0e-6 # Distance from edge of bent waveguide to edge of straight waveguide
        
        # Set thesholds
        self.mode_guided_percentage= 0.1 # tolerance for indicating when a mode is considered guided
        self.mode_guided_neff_diff = 0.05 # minimum neff diff for indicating when a mode is considered guided
        self.TE_polarization_thres = 0.6 # threshold above which the mode is considered TE
        self.TM_polarization_thres = 0.4 # threshold below which the mode is considered TM
        
        # Set scaling to ensure SI units. Assume all distance units are in um.
        self.scale_factor = 1e-6
        
        self.get_design_params()
        self.get_process_params()
        self.create_data_dirs()
        
        # Compact model mapping
        self.compact_model_mapping = {}
        
        
    def get_design_params(self):
        try:
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        except FileNotFoundError:
            print("YAML file does not exist... Cannot obtain design file... Passing...")
            return
        except yaml.YAMLError:
            print("Error in YAML file... Cannot obtain design file... Passing...")
            return
        except TypeError:
            if type(self.design_file) == tuple:
                self.design_file = self.design_file[0]
            with open(self.design_file) as f:
                data = yaml.load(f, Loader=yaml.FullLoader)
        
        self.design_data = data
        self.sim_params = data['simulation-params']
        self.design_intent = data['design-intent']
        self.component_name = data['name']
        
        self.techname = data.get('techname','EBeam')
        
        # Save compact model params
        self.compact_model_data = data['compact-model']
        self.compact_model_name = data['compact-model']['name']
        self.photonic_model = data['compact-model']['photonic-model']
        
        # Save design intent
        self.TEM = data['design-intent']['polarization']
        self.mode_num = data['design-intent']['mode-num'] + 1 # Define mode to start at 0
        
        # Save simulation params
        self.modes_to_monitor = data['simulation-params']['modes-to-monitor']
        self.modes_to_test = self.modes_to_monitor + 2
        self.wavelength = data['simulation-params']['wavelength']*self.scale_factor
        self.mesh_size = data['simulation-params']['mesh-size']*self.scale_factor
        self.mesh_accuracy = data['simulation-params']['mesh-accuracy']
        self.mode_selection = 'user select'
        self.frequency_points = data['simulation-params']['frequency-points']
              
    def get_process_params(self):
        # Get layer thicknesses and names
        self.layer_thickness = {}
        self.layer_names = {}
        tree = ET.parse(self.process_file)
        for layer_xml in tree.findall('.//layer'):
            for layer, layer_map in self.design_data['layers'].items():
                self.layer_names[layer] = layer_map.split(' - ')[0]
                if layer_map.split(' - ')[0] == layer_xml.attrib['name']:
                    self.layer_thickness[layer] = float(layer_xml.attrib['thickness'])
                    
        
        
    def setup_sim_region_from_width(self, width):
        self.mode.addfde() 
        self.mode.set("solver type", "2D Y normal");
        self.mode.set("x", width/2*self.scale_factor); 
        self.mode.set("x span", 2*self.width_margin + width*self.scale_factor);
        self.mode.set("y", 0);         
        self.mode.set("z", self.layer_thickness['Waveguide']/2);  
        self.mode.set("z span", self.layer_thickness['Waveguide'] + 2*self.height_margin);
        self.mode.set("wavelength", self.wavelength);   
        self.mode.set("define x mesh by","maximum mesh step"); 
        self.mode.set("dx", self.mesh_size);
        self.mode.set("define z mesh by","maximum mesh step"); 
        self.mode.set("dz", self.mesh_size);
        self.mode.set("number of trial modes", self.modes_to_test);
        
    def setup_sim_region_from_radius(self, radius, width):
        
        x_input = self.bend_to_straight_margin - self.bend_buffer_distance
        y_output = radius*self.scale_factor + self.bend_buffer_distance
        
        self.fdtd.addfdtd()
        self.fdtd.set('x min', x_input - 2*self.boundary_margin)
        # self.fdtd.set('x max', self.boundary_size + width*self.scale_factor/2 + self.width_margin);
        self.fdtd.set('x max', self.bend_to_straight_margin + radius*self.scale_factor + width*self.scale_factor/2 + self.width_margin);
        self.fdtd.set('y min', -self.width_margin - width*self.scale_factor/2); 
        self.fdtd.set('y max', y_output + self.boundary_margin);
        self.fdtd.set('z min', -self.layer_thickness['Waveguide']/2 - self.height_margin); 
        self.fdtd.set('z max', self.layer_thickness['Waveguide']/2 + self.height_margin);
        self.fdtd.set('mesh accuracy', self.mesh_accuracy);
        
        self.fdtd.addmode();
        self.fdtd.set('injection axis', 'x-axis');
        self.fdtd.set('direction', 'forward');
        self.fdtd.set('y', 0); 
        self.fdtd.set('x', x_input - self.boundary_margin); 
        self.fdtd.set('y span', width*self.scale_factor + 2*self.width_margin);
        self.fdtd.set('z', self.layer_thickness['Waveguide']/2); 
        self.fdtd.set('z span', self.layer_thickness['Waveguide'] + 2*self.height_margin);
        self.fdtd.set('set wavelength',1);
        self.fdtd.set('wavelength start', self.wavelength); 
        self.fdtd.set('wavelength stop', self.wavelength); 
        self.fdtd.set('mode selection', self.mode_selection);
        if self.mode_selection == "user select":
            self.fdtd.set('selected mode number', self.mode_selection_num)
            self.fdtd.updatesourcemode(self.mode_selection_num); 
        else:
            self.fdtd.updatesourcemode()

        self.fdtd.addpower();   # Power monitor, output
        self.fdtd.set('name', 'transmission');
        self.fdtd.set('monitor type', '2D Y-normal');
        self.fdtd.set('x', self.bend_to_straight_margin + radius*self.scale_factor); 
        self.fdtd.set('x span', width*self.scale_factor + 2*self.width_margin);
        self.fdtd.set('z min', -self.layer_thickness['Waveguide']/2 - self.height_margin); 
        self.fdtd.set('z max', self.layer_thickness['Waveguide']/2 + self.height_margin);
        self.fdtd.set('y', y_output);

        self.fdtd.addmodeexpansion();
        self.fdtd.set('name', 'expansion');
        self.fdtd.set('monitor type', '2D Y-normal');
        self.fdtd.set('x', self.bend_to_straight_margin + radius*self.scale_factor); 
        self.fdtd.set('x span', width*self.scale_factor + 2*self.width_margin);
        self.fdtd.set('z min', -self.layer_thickness['Waveguide']/2 - self.height_margin); 
        self.fdtd.set('z max', self.layer_thickness['Waveguide']/2 + self.height_margin);
        self.fdtd.set('y', y_output + self.mode_expansion_to_power_monitor);
        self.fdtd.set('frequency points', self.frequency_points);
        self.fdtd.set('mode selection', self.mode_selection);
        if self.mode_selection == "user select":
            self.fdtd.set('selected mode numbers', self.mode_selection_num)
            self.fdtd.updatemodes(self.mode_selection_num); 
        else:
            self.fdtd.updatemodes()
        self.fdtd.setexpansion('T','transmission');
        
        self.fdtd.addpower();   # Power monitor, input
        self.fdtd.set('name', 'input');
        self.fdtd.set('monitor type', '2D X-normal');
        self.fdtd.set('y', 0);  
        self.fdtd.set('y span', width*self.scale_factor + 2*self.width_margin);
        self.fdtd.set('x', x_input);
        self.fdtd.set('z min', -self.layer_thickness['Waveguide']/2 - self.height_margin); 
        self.fdtd.set('z max', self.layer_thickness['Waveguide']/2 + self.height_margin);


    def neff_sweep_width_2D(self, width_sweep_mapping, plot = False):
        # Create empty 2D array for mode data where first column is width sweep (um)
        self.neff_vs_width = [[0]*len(width_sweep_mapping) for i in range(0,self.modes_to_monitor+1)]
        self.pol_vs_width = [[0]*len(width_sweep_mapping) for i in range(0,self.modes_to_monitor+1)]
        
        # Populate first column with width sweep
        i = 0
        for width in width_sweep_mapping.values():
            self.neff_vs_width[0][i] = width
            self.pol_vs_width[0][i] = width
            i = i + 1
            
        # Get neff and TE polarization data
        for gds_file, width in width_sweep_mapping.items():
               
            # Set up geometry
            self.mode.switchtolayout()
            generate_lum_geometry(self.mode, self.process_file, gds_file)
            
            # Set up simulation region
            self.setup_sim_region_from_width(width)
            
            # Get mode data
            self.mode.findmodes()
            for m in range(0, self.modes_to_monitor):
                neff = self.mode.getdata('FDE::data::mode'+str(m+1),'neff')
                pol = self.mode.getdata('FDE::data::mode'+str(m+1), 'TE polarization fraction')
                # populate subsequent columns with neff and polarization
                self.neff_vs_width[m+1][self.neff_vs_width[0].index(width)] = abs(neff[0][0])
                self.pol_vs_width[m+1][self.pol_vs_width[0].index(width)] = pol
        
        # Save neff vs width to file
        now = datetime.now()
        with open(os.path.join(self.results_dir, now.strftime("%Y-%m-%d-%H%M-") + "neff_vs_width.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Create headers for data
            header = []
            for i in range(0, len(self.neff_vs_width)):
                if i == 0:
                    header.append('width (um)')
                else:
                    header.append('neff - mode'+str(i))
                    header.append('TE pol fraction - mode'+str(i))
            writer.writerow(header)
            
            # Insert data as columns
            for j in range(0,len(self.neff_vs_width[0])):
                row = []
                for i in range(0, len(self.neff_vs_width)):
                    row.append(self.neff_vs_width[i][j])
                    if i > 0:
                        row.append(self.pol_vs_width[i][j])
                writer.writerow(row)
            
        if plot:
            fig = plt.figure()
            # Plot original simulation data
            for i in range(0, self.modes_to_monitor):    
                plt.plot(self.neff_vs_width[0], self.neff_vs_width[i+1], 'x', label="mode"+str(i+1))
                
            # Interpolate and plot
            width_new = np.linspace(min(self.neff_vs_width[0]), max(self.neff_vs_width[0]), self.interpolation_points)  
            for i in range(0,self.modes_to_monitor):
                neff_smooth = make_interp_spline(self.neff_vs_width[0], self.neff_vs_width[i+1])( width_new)
                plt.plot(width_new, neff_smooth, label="mode"+str(i+1))
            
            fig.suptitle('')
            plt.xlabel('Width (um)')
            plt.ylabel('neff')
            plt.legend()
            plt.show()
            fig.savefig(os.path.join(self.plots_dir, now.strftime("%Y-%m-%d-%H%M-") + "neff_vs_width.png"))
            
    def loss_sweep_bend_radii(self, radius_sweep_mapping, width, plot = False):
        # Remove radius values that are larger than simulation boundaries
        for file, radius in radius_sweep_mapping.items():
            if radius*self.scale_factor > self.boundary_size:
                radius_sweep_mapping.pop(file)
                print("{}um radius is larger than simulation region... Removing...".format(radius))
                
        
        # Create 2D array for data where first column is radius sweep (um)
        transmission_spectrums = 3
        self.loss_vs_radius = [[0]*len(radius_sweep_mapping) for i in range(0,transmission_spectrums+1)]
        
        # Populate first column with radius sweep
        i = 0
        for radius in radius_sweep_mapping.values():
            self.loss_vs_radius[0][i] = radius
            i = i + 1
          
        # Get loss data
        for gds_file, radius in radius_sweep_mapping.items():
            
            # Set up files
            self.fdtd.newproject(); self.fdtd.switchtolayout(); self.fdtd.redrawoff(); 
            self.fdtd.selectall(); self.fdtd.delete();
        	
            # Set up geometry
            generate_lum_geometry(self.fdtd, self.process_file, gds_file)
            
            # Set up simulation region
            self.fdtd.save(os.path.join(self.sim_dir, 'bend_radius_' + str(int(radius*1000)) + "nm"))
            self.setup_sim_region_from_radius(radius, width)
            
            # Get transmission data
            self.fdtd.run()
        
            T_fund = self.fdtd.getresult('expansion', 'expansion for T');
            T_forward = T_fund['T_forward'];
            
            try:
                self.loss_vs_radius[1][self.loss_vs_radius[0].index(radius)] = -10*log10(abs(T_forward[0][0]/self.fdtd.transmission('input'))); # transmission in chosen mode
                self.loss_vs_radius[2][self.loss_vs_radius[0].index(radius)] = -10*log10(abs(self.fdtd.transmission('transmission')/self.fdtd.transmission('input')));  # total output power in WG
                self.loss_vs_radius[3][self.loss_vs_radius[0].index(radius)] = self.fdtd.transmission('input');  # input power in chosen mode
            except ValueError:
                print("Can't convert to dB... Numbers too close to zero... Passing data point...")
                
        # Save loss vs radius to file
        now = datetime.now()
        with open(os.path.join(self.results_dir,now.strftime("%Y-%m-%d-%H%M-") + "loss_vs_radius.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Create headers for data
            writer.writerow(['Radius (um)', 'Loss (dB) - {} mode (Mesh {})'.format(self.TEM+str(self.mode_num - 1),self.mesh_accuracy),
                             'Loss (dB) - Total Output Power (Mesh {})'.format(self.mesh_accuracy), 'Input Power (W)'])
            
            # Write data
            for j in range(0, len(self.loss_vs_radius[0])):
                row = []
                for i in range(0, len(self.loss_vs_radius)):
                    row.append(self.loss_vs_radius[i][j])
                writer.writerow(row)

        if plot:
            fig = plt.figure()
            # Plot original simulation data
            plt.plot(self.loss_vs_radius[0], self.loss_vs_radius[1], 'x', label="Simulated {} Mode - Output Power (Mesh {})".format(self.TEM+str(self.mode_num-1), self.mesh_accuracy))
            plt.plot(self.loss_vs_radius[0], self.loss_vs_radius[2], 'x', label="Simulated Total Output Power (Mesh {})".format(self.mesh_accuracy))

            # Need more than 3 data points for interpolation
            if len(self.loss_vs_radius[0]) > 3:
                radius_new = list(np.linspace(min(self.loss_vs_radius[0]), max(self.loss_vs_radius[0]), self.interpolation_points)) 
                
                loss_smooth_fund_output_power = make_interp_spline(self.loss_vs_radius[0], self.loss_vs_radius[1])( radius_new)
                loss_smooth_total_output_power = make_interp_spline(self.loss_vs_radius[0], self.loss_vs_radius[2])( radius_new)
                input_power = make_interp_spline(self.loss_vs_radius[0], self.loss_vs_radius[3])( radius_new)
            else:
                radius_new = self.loss_vs_radius[0]
                loss_smooth_fund_output_power = self.loss_vs_radius[1]
                loss_smooth_total_output_power = self.loss_vs_radius[2]
                input_power = self.loss_vs_radius[3]
                    
            plt.plot(radius_new, loss_smooth_fund_output_power, label="Interpolated {} Mode - Output Power".format(self.TEM+str(self.mode_num-1)))
            plt.plot(radius_new, loss_smooth_total_output_power, label="Interpolated Total Output Power")
            
            fig.suptitle('')
            plt.xlabel('Radius (um)')
            plt.ylabel('Loss (dB)')
            plt.legend()
            plt.show()
            fig.savefig(os.path.join(self.plots_dir, now.strftime("%Y-%m-%d-%H%M-") + "loss_vs_radius.png"))
            
    def loss_sweep_bezier(self, bezier_sweep_mapping, radius, width, plot = False):
        # Return if radius values are larger than simulation boundaries
        if radius*self.scale_factor > self.boundary_size:
            print("{}um radius is larger than simulation region... Returning...".format(radius))
            return

        
        # Create 2D array for data where first column is bezier sweep (um)
        transmission_spectrums = 3
        self.loss_vs_bezier = [[0]*len(bezier_sweep_mapping) for i in range(0,transmission_spectrums+1)]
        
        # Populate first column with radius sweep
        i = 0
        for b in bezier_sweep_mapping.values():
            self.loss_vs_bezier[0][i] = b
            i = i + 1
          
        # Get loss data
        for gds_file, b in bezier_sweep_mapping.items():
            
            # Set up files
            self.fdtd.newproject(); self.fdtd.switchtolayout(); self.fdtd.redrawoff(); 
            self.fdtd.selectall(); self.fdtd.delete();
        	
            # Set up geometry
            generate_lum_geometry(self.fdtd, self.process_file, gds_file)
            
            # Set up simulation region
            self.setup_sim_region_from_radius(radius, width)
            
            # Get transmission data
            self.fdtd.save(os.path.join(self.sim_dir, 'bezier_param_' + str(b).replace('.','_')))
            self.fdtd.run()
        
            T_fund = self.fdtd.getresult('expansion', 'expansion for T');
            T_forward = T_fund['T_forward'];
            
            self.loss_vs_bezier[1][self.loss_vs_bezier[0].index(b)] = -10*log10(abs(T_forward[0][0]/self.fdtd.transmission('input'))); # transmission in chosen mode
            self.loss_vs_bezier[2][self.loss_vs_bezier[0].index(b)] = -10*log10(abs(self.fdtd.transmission('transmission')/self.fdtd.transmission('input')));  # total output power in WG
            self.loss_vs_bezier[3][self.loss_vs_bezier[0].index(b)] = self.fdtd.transmission('input');  # input power in chosen mode
        
        # Save loss vs bezier to file
        now = datetime.now()
        with open(os.path.join(self.results_dir ,now.strftime("%Y-%m-%d-%H%M-") + "loss_vs_bezier.csv"), 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Create headers for data
            writer.writerow(['Bezier', 'Loss (dB) - {} Mode (Mesh {})'.format(self.TEM+str(self.mode_num-1), self.mesh_accuracy),
                             'Loss (dB) - Total Output Power (Mesh {})'.format(self.mesh_accuracy), 'Input Power (W)'])
            
            # Write data
            for j in range(0, len(self.loss_vs_bezier[0])):
                row = []
                for i in range(0, len(self.loss_vs_bezier)):
                    row.append(self.loss_vs_bezier[i][j])
                writer.writerow(row)    
        
        if plot:
            fig = plt.figure()
            # Plot original simulation data
            # Convert to dB
            plt.plot(self.loss_vs_bezier[0], self.loss_vs_bezier[1], 'x', label="Simulated {} Mode - Output Power (Mesh {})".format(self.TEM+str(self.mode_num-1), self.mesh_accuracy))
            plt.plot(self.loss_vs_bezier[0], self.loss_vs_bezier[2], 'x', label="Simulated Total Output Power (Mesh {})".format(self.mesh_accuracy))
        
            # Need more than 3 data points for interpolation
            if len(self.loss_vs_bezier[0]) > 3:
                bezier_new = list(np.linspace(min(self.loss_vs_bezier[0]), max(self.loss_vs_bezier[0]), self.interpolation_points)) 
                
                loss_smooth_fund_output_power = make_interp_spline(self.loss_vs_bezier[0], self.loss_vs_bezier[1])( bezier_new)
                loss_smooth_total_output_power = make_interp_spline(self.loss_vs_bezier[0], self.loss_vs_bezier[2])( bezier_new)
                input_power = make_interp_spline(self.loss_vs_bezier[0], self.loss_vs_bezier[3])( bezier_new)
            else:
                bezier_new = self.loss_vs_bezier[0]
                loss_smooth_fund_output_power = self.loss_vs_bezier[1]
                loss_smooth_total_output_power = self.loss_vs_bezier[2]
                input_power = self.loss_vs_bezier[3]
            
            plt.plot(bezier_new, loss_smooth_fund_output_power, label="Interpolated {} Mode - Output Power".format(self.TEM+str(self.mode_num-1)))
            plt.plot(bezier_new, loss_smooth_total_output_power, label="Interpolated Total Output Power")
            
            fig.suptitle('')
            plt.xlabel('Bezier')
            plt.ylabel('Loss (dB)')
            plt.legend()
            plt.show()
            fig.savefig(os.path.join(self.plots_dir, now.strftime("%Y-%m-%d-%H%M-") + "loss_vs_bezier.png"))

    def loss_sweep_bezier_radius(self, bezier_radius_sweep_mapping, width, plot = False):
        for radius, bezier_sweep_mapping in bezier_radius_sweep_mapping.items():
            self.loss_sweep_bezier(bezier_sweep_mapping, radius, width, plot = True)
            
    def generate_compact_model_file(self, width, radius, bezier):
        
        ## Straight waveguide geometry
        straight_wg_geo = WaveguideStripGeometry(self.design_file, self.process_file, self.mode)
        straight_wg_gds = straight_wg_geo.generate_gds_from_width(width)
        
        # Set up geometry
        self.mode.switchtolayout()
        generate_lum_geometry(self.mode, self.process_file, straight_wg_gds)
        
        # Set up simulation region
        self.setup_sim_region_from_width(width)
        
        # Get mode data
        self.mode.findmodes()
        TE_modes = 0
        TM_modes = 0
        for m in range(0, self.modes_to_monitor):
            pol = self.mode.getdata('FDE::data::mode'+str(m+1), 'TE polarization fraction')
            if pol > self.TE_polarization_thres:
                TE_modes += 1
            elif pol < self.TM_polarization_thres:
                TM_modes += 1
                
            if (self.TEM == "TE" and TE_modes == self.mode_num)\
                    or (self.TEM == "TM" and TM_modes == self.mode_num):
                self.mode_selection_num = m+1
                break;
        self.mode.selectmode(self.mode_selection_num);
        self.mode.setanalysis("track selected mode", 1);
        self.mode.setanalysis("wavelength", self.wavelength);
        self.mode.setanalysis("stop wavelength", self.wavelength);
        self.mode.setanalysis("number of points", self.frequency_points);
        self.mode.setanalysis("number of test modes", self.modes_to_test);
        self.mode.setanalysis("detailed dispersion calculation",1);
        self.mode.frequencysweep();
            
        # Get neff, ng, dispersion, loss data
        self.neff = abs((self.mode.getdata("FDE::data::frequencysweep", "neff")))[0][0]
        self.ng = self.mode.c()/self.mode.getdata("FDE::data::frequencysweep","vg")
        self.D = self.mode.getdata("FDE::data::frequencysweep","D")
        
        # Generate compact model file for straight waveguide assuming:
        # 300dB/m loss and 0.00018 dneff/dT as defaults
        self.straight_loss = self.compact_model_data.get('straight-loss', 3.0)*100 # Convert to dB/m
        self.dneff_dT = self.compact_model_data.get('dneff-dT', 0.00018)
        self.temperature_data = self.compact_model_data.get('temperature-data', 300)
        
        default_wg_length = 10e-6 # m
        wg_length_max = 1 # m
        wg_length_min = 0 # m
        
        self.mode.eval("clear;")
        self.mode.putv('D', self.D)
        self.mode.putv('ng', self.ng)
        self.mode.putv('neff', self.neff)
        self.mode.putv('dneff_dT', self.dneff_dT)
        self.mode.putv('loss', self.straight_loss)
        if self.TEM == "TE":
            self.mode.putv('mode_data', [{"ID": 1, "name": self.TEM}])
        elif self.TEM == "TM":
            self.mode.putv('mode_data', [{"ID": 2, "name": self.TEM}])
        self.mode.putv('temperature_data', self.temperature_data)   
        self.mode.putv('wavelength_data', self.wavelength)
        self.mode.putv('wg_length', default_wg_length)
        self.mode.putv('wg_length_max', wg_length_max)
        self.mode.putv('wg_length_min', wg_length_min)
        
        now = datetime.now()
        wg_straight_datafile = now.strftime("%Y-%m-%d-%H%M-") + self.compact_model_name +".json"
        wg_straight_json_file = os.path.join(self.compact_mod_dir,wg_straight_datafile)
        self.mode.eval("jsonsave('{}');".format(wg_straight_json_file))
        print("Created compact model file for straight waveguide:\n{}\n".format(wg_straight_json_file))
        
        # Get template file and replace params
        template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_wg_strip_straight.lsf")
        with open(template_file, 'r') as f:
            wg_straight_lsf = f.read()
            
        model_name = self.compact_model_name
        wg_straight_lsf = wg_straight_lsf.replace('{model_name}', model_name)
        wg_straight_lsf = wg_straight_lsf.replace('{techname}', self.techname)
        wg_straight_lsf = wg_straight_lsf.replace('{TEM_mode}', self.TEM+str(self.mode_num-1))
        wg_straight_lsf = wg_straight_lsf.replace('{wavelength}', str(self.wavelength))
        wg_straight_lsf = wg_straight_lsf.replace('{datafile}', wg_straight_datafile)
        
        # Create directory for compact model files
        wg_straight_dir = os.path.join(self.compact_mod_dir, model_name)
        if not os.path.isdir(wg_straight_dir):
            os.mkdir(wg_straight_dir)
        
        with open(os.path.join(wg_straight_dir, model_name+".lsf"), 'w') as f:
            f.write(wg_straight_lsf)
        
        # Remove existing json files in compact model
        json_files = [os.path.join(wg_straight_dir, file) for file in os.listdir(wg_straight_dir) if os.path.isfile(os.path.join(wg_straight_dir,file)) and file.endswith(".json")]
        for json_file in json_files:
            os.remove(json_file)
        
        copyfile(wg_straight_json_file, os.path.join(wg_straight_dir,wg_straight_datafile))
        
        svg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_wg_strip_straight.svg")
        copyfile(svg_file, os.path.join(wg_straight_dir,model_name+".svg"))
        
        self.compact_model_mapping[wg_straight_dir] = self.photonic_model
        
        skip_bend_loss_sim = input("Skip bend loss simulation? y/n\n")
        if skip_bend_loss_sim == 'n':

            ## Bent waveguide geometry
            bent_wg_geo = WaveguideStripGeometry(self.design_file, self.process_file, self.fdtd)
            bent_wg_gds = bent_wg_geo.generate_gds_from_params(width,radius,bezier)
            
            # Return if radius values are larger than simulation boundaries
            if radius*self.scale_factor > self.boundary_size:
                print("{}um radius is larger than simulation region... Returning...".format(radius))
                return
            
            # Set up files
            self.fdtd.newproject(); self.fdtd.switchtolayout(); self.fdtd.redrawoff(); 
            self.fdtd.selectall(); self.fdtd.delete();
            # Create geometry in Lumerical
            generate_lum_geometry(self.fdtd, self.process_file, bent_wg_gds)
            # Set up simulation region
            self.setup_sim_region_from_radius(radius, width)
            
            # Get transmission data
            now = datetime.now()
            self.fdtd.save(os.path.join(self.sim_dir, now.strftime("%Y-%m-%d-%H%M-") + 'wg_bend_cml'))
            self.fdtd.run()
        
            T_fund = self.fdtd.getresult('expansion', 'expansion for T');
            T_forward = T_fund['T_forward'];
        
            # Get bend loss in dB/m
            self.bend_loss = self.compact_model_data.get('bend-loss',
                -10*log10(abs(T_forward[0][0]/self.fdtd.transmission('input')))/(pi*radius*self.scale_factor/2)/100)*100
        else:
            self.bend_loss = self.compact_model_data.get('bend-loss', 300) # Assume 3dB/cm if bend loss value not available
        
        # Generate compact model for bent waveguide 
        self.fdtd.eval("clear;")
        self.fdtd.putv('D', self.D)
        self.fdtd.putv('ng', self.ng)
        self.fdtd.putv('neff', self.neff)
        self.fdtd.putv('dneff_dT', self.dneff_dT)
        self.fdtd.putv('loss', self.bend_loss)
        if self.TEM == "TE":
            self.fdtd.putv('mode_data', [{"ID": 1, "name": self.TEM}])
        elif self.TEM == "TM":
            self.fdtd.putv('mode_data', [{"ID": 2, "name": self.TEM}])
        self.fdtd.putv('temperature_data', self.temperature_data)   
        self.fdtd.putv('wavelength_data', self.wavelength)
        self.fdtd.putv('radius', radius*self.scale_factor)
        self.fdtd.putv('theta', pi/2)
        
        now = datetime.now()
        wg_arc_datafile = now.strftime("%Y-%m-%d-%H%M-") + "wg_strip_arc.json"
        wg_arc_json_file = os.path.join(self.compact_mod_dir,wg_arc_datafile)
        self.fdtd.eval("jsonsave('{}');".format(wg_arc_json_file))
        print("Created compact model file for arc waveguide:\n{}\n".format(wg_arc_json_file))
        
         # Get template file and replace params
        template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_wg_strip_arc.lsf")
        with open(template_file, 'r') as f:
            wg_arc_lsf = f.read()
          
        model_name = "wg_arc_"+self.TEM+str(self.mode_num-1)+"_"+str(int(self.wavelength/self.scale_factor*1e3))
        wg_arc_lsf = wg_arc_lsf.replace('{model_name}', model_name)
        wg_arc_lsf = wg_arc_lsf.replace('{techname}', self.techname)
        wg_arc_lsf = wg_arc_lsf.replace('{TEM_mode}', self.TEM+str(self.mode_num-1))
        wg_arc_lsf = wg_arc_lsf.replace('{wavelength}', str(self.wavelength))
        wg_arc_lsf = wg_arc_lsf.replace('{datafile}', wg_arc_datafile)
        
        # Create directory for compact model files
        wg_arc_dir = os.path.join(self.compact_mod_dir, model_name)
        if not os.path.isdir(wg_arc_dir):
            os.mkdir(wg_arc_dir)
        
        with open(os.path.join(wg_arc_dir, model_name+".lsf"), 'w') as f:
            f.write(wg_arc_lsf)
        
        # Remove existing json files in compact model
        json_files = [os.path.join(wg_arc_dir, file) for file in os.listdir(wg_arc_dir) if os.path.isfile(os.path.join(wg_arc_dir,file)) and file.endswith(".json")]
        for json_file in json_files:
            os.remove(json_file)
        
        copyfile(wg_arc_json_file, os.path.join(wg_arc_dir,wg_arc_datafile))
        
        svg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_wg_strip_arc.svg")
        copyfile(svg_file, os.path.join(wg_arc_dir,model_name+".svg"))
        
        self.compact_model_mapping[wg_arc_dir] = self.photonic_model
        
        ## Create WAVEGUIDES.xml
        waveguides = ET.Element("waveguides")
        waveguide = ET.SubElement(waveguides, "waveguide")
        
        ET.SubElement(waveguide, "name").text = self.component_name
        ET.SubElement(waveguide, "CML").text = self.techname
        ET.SubElement(waveguide, "model").text = self.compact_model_name
        ET.SubElement(waveguide, "bezier").text = str(bezier)
        ET.SubElement(waveguide, "radius").text = str(radius)
        ET.SubElement(waveguide, "width").text = str(width)
        component1 = ET.SubElement(waveguide, "component")
        ET.SubElement(component1, "layer").text = self.layer_names['Waveguide']
        ET.SubElement(component1, "width").text = str(width)
        ET.SubElement(component1, "offset").text = "0.0"
        component2 = ET.SubElement(waveguide, "component")
        ET.SubElement(component2, "layer").text = "DevRec"
        ET.SubElement(component2, "width").text = str(width + 1.0)
        ET.SubElement(component2, "offset").text = "0.0"
        
        waveguides_xml = prettify(waveguides)
        now = datetime.now()
        raw_xml_path = os.path.join(self.compact_mod_dir, "WAVEGUIDES.xml")
        tracked_xml_path = os.path.join(self.compact_mod_dir, now.strftime("%Y-%m-%d-%H%M-") + "WAVEGUIDES.xml")
        with open(raw_xml_path, 'w') as f:
            f.write(waveguides_xml)
        
        copyfile(raw_xml_path, tracked_xml_path)
        
     
    def optimize_width(self, neff_vs_width_csv = ""):
        ''' Optimize width for specified mode
        
        Supports TE and TM modes (not TEM) given mode numbers starting from 1

        Parameters
        ----------
        neff_vs_width_csv : str, optional
            Absolute path to csv file with neff, width, and TE polarization fraction
            data. csv file contains widths in column 0, then neff and polarization fraction
            in subsequent columns. The default is "".

        Returns
        -------
        float
            Optimal width (um) for specified mode

        '''
        
        if neff_vs_width_csv:
            with open(neff_vs_width_csv, 'r') as f:
                reader = csv.reader(f)
                # Create 2D array of data
                arr = []
                for row in reader:
                    arr.append(row)
                
                # Create neff vs width array and TE pol fraction vs width array
                # first col = width, subsequent cols = neff
                # first col = width, subsequent cols = TE pol fraction
                neff_vs_width_arr = []
                TE_pol_vs_width_arr = []
                
                for j in range(0,len(arr[0])):
                    data1 = []
                    data2 = []
                    for i in range(1,len(arr)):
                        if j == 0:
                            # append width vals
                            data1.append(float(arr[i][j]))
                        elif j % 2 == 1:
                            # append odd indexed columns or neff vals
                            data1.append(float(arr[i][j]))
                            
                        if j % 2 == 0:
                            # append width and TE pol vals
                            data2.append(float(arr[i][j]))
                    
                    if data1:
                        neff_vs_width_arr.append(data1)
                    if data2:
                        TE_pol_vs_width_arr.append(data2)
                        
        elif self.neff_vs_width and self.pol_vs_width:
            neff_vs_width_arr = self.neff_vs_width
            TE_pol_vs_width_arr = self.pol_vs_width
        else:
            print("No neff vs width data... Returning...")
            return
            
        # Create baseline neff for modes
        neff_base_list = [neff_vs_width_arr[i][0] for i in range(1, len(neff_vs_width_arr))]
        neff_base = sum(neff_base_list)/len(neff_base_list)
        
        ### Iterate through neff and TE polarization fractions for every width
        # Select optimal width if meets both neff and polarization conditions
        # Condition 1: Specified mode supported (i.e. TE1, TM1, TE2, TM2)
        # Condition 2: neff of the next mode after the specified mode (i.e. if TE1
        # is the specified mode, the next mode is TE2. Same if TM1 then next is TM2)
        # minus neff_base is less than neff of specified mode minus neff_base by percentage
        for width_ind in range(0, len(neff_vs_width_arr[0])):
            # Count TE and TM modes and save indices of those modes
            TE_modes = 0
            TE_ind = []
            TM_modes = 0
            TM_ind = []
            for i in range(1, len(TE_pol_vs_width_arr)):
                if TE_pol_vs_width_arr[i][width_ind] > self.TE_polarization_thres:
                    TE_modes += 1
                    TE_ind.append(i)
                    if TE_modes == self.mode_num and self.TEM == "TE":
                        self.mode_selection_num = i
                elif TE_pol_vs_width_arr[i][width_ind] < self.TM_polarization_thres:
                    TM_modes += 1
                    TM_ind.append(i)
                    if TM_modes == self.mode_num and self.TEM == "TM":
                        self.mode_selection_num = i
            
            # Check if this mode is supported (Condition 1)
            if self.TEM == "TE" and TE_modes > self.mode_num:
                # Check if neff is supported (Condition 2)
                neff_spec = neff_vs_width_arr[TE_ind[self.mode_num-1]][width_ind]
                neff_next = neff_vs_width_arr[TE_ind[self.mode_num]][width_ind]
                
                if (neff_next - neff_base )/(neff_spec - neff_base) > self.mode_guided_percentage\
                        and (neff_next - neff_base ) > self.mode_guided_neff_diff\
                        and (neff_spec - neff_base) > self.mode_guided_neff_diff:
                    print("Optimal width to support {} mode is {}um".format(self.TEM+str(self.mode_num-1), neff_vs_width_arr[0][width_ind]))
                    return neff_vs_width_arr[0][width_ind]

            elif self.TEM == "TM" and TM_modes > self.mode_num:
                # Check if neff is supported (Condition 2)
                neff_spec = neff_vs_width_arr[TM_ind[self.mode_num-1]][width_ind]
                neff_next = neff_vs_width_arr[TM_ind[self.mode_num]][width_ind]
                
                if (neff_next - neff_base )/(neff_spec - neff_base) > self.mode_guided_percentage\
                        and (neff_next - neff_base ) > self.mode_guided_neff_diff\
                        and (neff_spec - neff_base) > self.mode_guided_neff_diff:
                    print("Optimal width to support {} mode is {}um".format(self.TEM+str(self.mode_num-1), neff_vs_width_arr[0][width_ind]))
                    return neff_vs_width_arr[0][width_ind]
    
    def optimize_radius(self, loss, loss_vs_radius_csv = ""):
        
        if loss_vs_radius_csv:
            with open(loss_vs_radius_csv, 'r') as f:
                reader = csv.reader(f)
                # Create 2D array of data
                arr = []
                for row in reader:
                    arr.append(row)
                
            radius = [float(arr[i][0]) for i in range(1,len(arr))]
            loss_fund = [float(arr[i][1]) for i in range(1,len(arr))]        
            loss_total = [float(arr[i][2]) for i in range(1,len(arr))]
    
    def optimize_bezier(self, loss_vs_bezier_csv = ""):
        if loss_vs_bezier_csv:
            with open(loss_vs_bezier_csv, 'r') as f:
                reader = csv.reader(f)
                # Create 2D array of data
                arr = []
                for row in reader:
                    arr.append(row)
                
            bezier = [float(arr[i][0]) for i in range(1,len(arr))]
            loss_fund = [float(arr[i][1]) for i in range(1,len(arr))]        
            loss_total = [float(arr[i][2]) for i in range(1,len(arr))]
            
        elif self.loss_vs_bezier:
            bezier = self.loss_vs_bezier[0]
            loss_fund = self.loss_vs_bezier[1]      
            loss_total = self.loss_vs_bezier[2] 
        else:
            print("No loss vs bezier data... Returning...")
            return
        
        # Interpolate
        bezier_new = list(np.linspace(min(bezier), max(bezier), self.interpolation_points)) 
        
        loss_smooth_fund_output_power = list(make_interp_spline(bezier, loss_fund)( bezier_new))
        loss_smooth_total_output_power = list(make_interp_spline(bezier, loss_total)( bezier_new))
        
        # Find minimum loss
        optimal_bezier = bezier_new[loss_smooth_fund_output_power.index(min(loss_smooth_fund_output_power))]
        print("Optimal bezier is {}".format(optimal_bezier))
        return optimal_bezier
            
    def create_data_dirs(self):
        # define directories
        self.results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
        self.sim_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulations")
        self.plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
        self.compact_mod_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "compact_models")
        
        # create dirs if not available
        if not os.path.isdir(self.results_dir):
            os.mkdir(self.results_dir)
        if not os.path.isdir(self.sim_dir):
            os.mkdir(self.sim_dir)
        if not os.path.isdir(self.plots_dir):
            os.mkdir(self.plots_dir)
        if not os.path.isdir(self.compact_mod_dir):
            os.mkdir(self.compact_mod_dir)
        

# design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
# process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),r"yaml_processes\SiEPICfab-Grouse-Base.lbr")
# csv_file = r"C:\Users\seanl\Documents\01_UBC\Academics\Grad School\01_Work\PDK-Generator\Repo\PDK-Generator\python\design_automation\Waveguide\2021-06-26-1303-neff_vs_width.csv"

# WGSS = WaveguideStripSimulation(design_file, process_file)
# WGSS.optimize_width("TM", 2, csv_file)

# design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
# process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),r"yaml_processes\SiEPICfab-Grouse-Base.lbr")
# csv_file = r"C:\Users\seanl\Documents\01_UBC\Academics\Grad School\01_Work\PDK-Generator\Repo\PDK-Generator\python\design_automation\Waveguide\2021-06-27-1711-loss_vs_bezier.csv"

# WGSS = WaveguideStripSimulation(design_file, process_file)
# WGSS.optimize_bezier(csv_file)


if __name__ == "__main__":
    # Test 1: Sweep neff vs width
    # gds_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),r"design_automation\Waveguide\Waveguide_w=100nm.gds")
    # design_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),r"design_automation\Waveguide\Waveguide_design.yml")
    # process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),r"yaml_processes\SiEPICfab-Grouse-Base.lbr")
    # mode = lumapi.MODE(hide = False)
    # WGSG = WaveguideStripGeometry(design_file, process_file, mode)
    # mapping = WGSG.sweep_width([0.1, 0.8], 0.01)
    
    # WGSS = WaveguideStripSimulation(design_file, process_file,mode)
    # WGSS.neff_sweep_width_2D(mapping, True)
    
    
    # Test 2: Sweep radius
    gds_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_r=1000nm.gds")
    design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
    process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),"yaml_processes","SiEPICfab_Royale.lbr")
    csv_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "2021-07-23-1751-neff_vs_width.csv")
    
    fdtd = lumapi.FDTD(hide = False)
    WGSG = WaveguideStripGeometry(design_file, process_file, fdtd)
    mapping = WGSG.sweep_radius(0.5,[1, 10], 1)
    
    WGSS = WaveguideStripSimulation(design_file, process_file,fdtd=fdtd)
    WGSS.optimize_width(csv_file)
    WGSS.loss_sweep_bend_radii(mapping, 0.5, True)
    
    # Test 3: Sweep bezier
    # gds_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_r=1000nm.gds")
    # design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
    # process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),"yaml_processes","SiEPICfab-Grouse-Base.lbr")
        
    # fdtd = lumapi.FDTD(hide = False)
    # WGSG = WaveguideStripGeometry(design_file, process_file, fdtd)
    # mapping = WGSG.sweep_bezier(0.5, 5, [0.1, 0.6], 0.1)
    
    # WGSS = WaveguideStripSimulation(design_file, process_file,fdtd=fdtd)
    # WGSS.loss_sweep_bezier(mapping, 5, 0.5, True)
    
    # Test 4: Generate compact model ready parameters
    # gds_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_w=100nm.gds")
    # design_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),"Waveguide_design.yml")
    # process_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),r"yaml_processes\SiEPICfab-Grouse-Base.lbr")
    # mode = lumapi.MODE(hide = False)
    # fdtd = lumapi.FDTD(hide = False)
    
    # WGSS = WaveguideStripSimulation(design_file, process_file,mode, fdtd)
    # WGSS.generate_compact_model_params(0.5, 5, 0.225)
