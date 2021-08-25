import io, sys, os
import xml.dom.minidom
import xml.etree.ElementTree as ET
from datetime import date

def create_cml_xml(cml_name, directory, element_list = [], version = ""):
    #### CREATION OF TEST XML file
    if not version:
        version = str(date.today())
    
    root = ET.Element("foundry_data")
    ET.SubElement(root,"foundry_name").text = cml_name
    ET.SubElement(root,"version_suffix").text = version # optional suffix
    # ET.SubElement(root,"process_prefix").text = "" # optional prefix for models
    # ET.SubElement(root,"NumOfChannel").text = "2" # number of channels for veriloga models
    elements = ET.SubElement(root,"element_list")

    # elements list
    el_list = element_list
    
        # elements without statistical data
        ### waveguides
        # ["wg_strip_straight_c","waveguide_simple",".lsf"],
        # ["wg_strip_arc_c","waveguide_simple",".lsf"],
        # ["wg_strip_sbend_c","waveguide_simple",".lsf"],
        # ["wg_strip_straight_parameterized","wg_parameterized",".lsf"],
        # ["wg_strip_arc_parameterized","wg_parameterized",".lsf"],
        # ["wg_strip_sbend_parameterized","wg_parameterized",".lsf"],
        # ["wg_bend_90","wg_parameterized",".lsf"],
        # ["wg_back_annotation","waveguide_back_annotation",".lsf"],
    
        ### passives
        # ["mmi_1x2_strip_te_c","spar_fixed",".lsf"],
        # ["mmi_1x2_strip_te_c_thermal","sparsweep_pcell",".lsf"],
        # ["gc_strip_te_c","spar_fixed",".lsf"],
        # ["gc_fitted_te_c","grating_coupler",".lsf"],
        # ["dc_strip_te_c","spar_fixed",".lsf"],
        # ["pdc_strip_c","directional_coupler_parameterized",".lsf"],
        # ["ptaper_strip_c","sparsweep_pcell",".lsf"],
    
        ### actives
        # ["pd_c","photodetector_simple",".lsf"],
        # ["ps_pn_te_c","phase_shifter_electrical",".lsf"],
        # ["ps_pn_tw_te_c","phase_shifter_electrical",".lsf"],
        # ["ps_thermal_te_c", "phase_shifter_thermal", ".lsf"],
        # ["rm_strip_te_c", "ring_modulator", ".lsf"],
        # ['mzm_unbalanced_te_c', 'mach_zehnder_modulator', '.lsf'],
        # ['mzm_unbalanced_tw_te_c', 'mach_zehnder_modulator', '.lsf'],
        # ['eam_te_c', 'electro_absorption_modulator', '.lsf'],
    
        ### advanced models
        # ['scripted_wg', 'scripted_element', '.lsf'],
        # ["container_element_child1","phase_shifter_electrical",'.lsf'],
        # ["container_element_child2","phase_shifter_thermal",'.lsf'],
        # ["container_example","container_element",'.lsf'],
    
        # elements with statistical data
        # ['wg_stat_strip_straight_c','waveguide_simple', '.lsf'],
        # ['mmi_1x2_stat_strip_te_c','sparsweep_pcell', '.lsf'],
        # ["gc_fitted_stat_te_c","grating_coupler",".lsf"],
        # ['rm_stat_strip_te_c','ring_modulator', '.lsf'],
        # ['rm_stat_fom_strip_te_c','ring_modulator', '.lsf'],
        # ['mzm_stat_unbalanced_te_c','mach_zehnder_modulator', '.lsf'],
        # ['mzm_stat_fom_unbalanced_te_c','mach_zehnder_modulator', '.lsf'],
        # ["ps_pn_stat_te_c","phase_shifter_electrical",".lsf"],
        # ["ps_thermal_stat_te_c", "phase_shifter_thermal", ".lsf"],
        # ["pd_stat_c","photodetector_simple",".lsf"]
    
    # extra information for container elements. List of sub-elements, and the Lumerical script code required to select them
    ce_info = { #"container_example" :
    #                 [ ["container_element_child1", "set('phase_shifter_type','pn');" ],
    #                   ["container_element_child2", "set('phase_shifter_type','thermal');" ]]
               }
    
    ce_info_remove_elements = { #"container_example" : True,
                               }
    # Reporting tuned parameters in actives (optional)
    #report_tuning = ET.SubElement(root,"report_tuned_data")
    #ET.SubElement(report_tuning,"password").text = "!Passcode101" # any alphanumeric password except "NULL" 
                               

    # statistical data
    stat_data = ET.SubElement(root,"statistical_data")
    ET.SubElement(stat_data,"statistical_parameter_status").text = "open" # options: "open", "hidden", "protected"
    ET.SubElement(stat_data,"nominal_value_type").text = "mode" # options: "mean", "mode"
    # LOTGROUP list  ['name','distribution','sigma','gamma1','beta2']  'gamma1' and 'beta2' are needed for pearson4 distribution type only
    lotgroup_list = [
        # ['lot_delta_width','normal','1'],
        # ['lot_delta_height','normal','1'],
        # ['lot_delta_ridge_height','normal','1']
    ]
    corner_list = [
        # 'corner_1',
        # 'corner_2'
        ] # list all corners
    
    # do not modify
    for e in el_list:
        el = ET.SubElement(elements,"element")
        ET.SubElement(el,"name").text = e[0]
        ET.SubElement(el,"photonic_model").text = e[1]
        ET.SubElement(el,"svg_filename").text = "source/"+e[0]+"/"+e[0]+".svg"
        ET.SubElement(el,"parameter_filename").text = "source/"+e[0]+"/"+e[0]+e[2]
        ET.SubElement(el,"datafile_directory").text = "source/"+e[0]
        if e[0] in ce_info.keys():
            if e[0] in ce_info_remove_elements:
                ET.SubElement(el,"remove_sub_elements").text = str(ce_info_remove_elements[e[0]]);
            sub_elements = ET.SubElement(el,"sub_element_list")
            for c in ce_info[e[0]]:
                ce = ET.SubElement(sub_elements,"sub_element")
                ET.SubElement(ce,"name").text = c[0]
                ET.SubElement(ce,"selection_code").text = c[1]
    if lotgroup_list:
        lg_list = ET.SubElement(stat_data,"LOTGROUP_list")
        for lg in lotgroup_list:
            lotgroup = ET.SubElement(lg_list,"LOTGROUP")
            ET.SubElement(lotgroup,"name").text = lg[0]
            ET.SubElement(lotgroup,"distribution").text = lg[1]
            ET.SubElement(lotgroup,"sigma").text = lg[2]
            if lg[1]=='pearson4':
                ET.SubElement(lotgroup,"gamma1").text = lg[3]
                ET.SubElement(lotgroup,"beta2").text = lg[4]
    if corner_list:
        cn_list = ET.SubElement(stat_data,"corner_list")
        for cn in corner_list:
            ET.SubElement(cn_list,"corner").text = cn
    
    rough_string = ET.tostring(root)
    reparsed = xml.dom.minidom.parseString(rough_string)
    print(reparsed.toprettyxml(indent="    "))
    with open(os.path.join(directory, cml_name+".xml"),"w") as f:
        f.write(reparsed.toprettyxml(indent="    "))
