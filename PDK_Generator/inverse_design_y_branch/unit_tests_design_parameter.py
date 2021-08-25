#This code checks the validity of the YAML file design parameters

import yaml 
import pandas as pd 

datafile = "y_branch_specifications.yaml"

def parameter_checks():
    """
    Function has various tests to check the validity of YAML design intent file design parameters
    Will print total amount of errors violated

    Returns
    -------
    None.

    """
    
    with open (datafile, 'r') as yaml_datafile: 
            #Load as python object 
            yaml_datafile = yaml.load(yaml_datafile, Loader=yaml.FullLoader)
            #Organize by layers
            df = pd.json_normalize(yaml_datafile)

    comp_df = df.iloc[0]['component']
    comp_df = pd.DataFrame(comp_df)
    comp_df.to_csv('component.csv')

    error_count = 0

    #Check spans in each direction is greater than 0
    for i in range(len(comp_df)):
        if comp_df.loc[i,'x_span']<0:
            print ("ERROR: Component x_span has a value of less than 0")
            error_count+=1
        if comp_df.loc[i,'y_span']<0:
            print ("ERROR: Component y_span has a value of less than 0")
            error_count+=1
        if comp_df.loc[i,'z_span']<0:
            print ("ERROR: Component z_span has a value of less than 0")
            error_count+=1
        
    comp_df = comp_df.set_index('name')
    #check that components need to be mirrored at the y-axis

    x_coord_in = comp_df.loc['input_wg','x']
    x_coord_out = comp_df.loc['output_wg_top','x']

    if x_coord_in >0 or x_coord_out<0:
        print ("ERROR: components are not mirrored on the Y axis")

    #check distance between input and output waveguides in the x direction

    distance_x = (comp_df.loc['output_wg_top','x']-(comp_df.loc['output_wg_top','x_span']/2))-(comp_df.loc['input_wg','x']+(comp_df.loc['input_wg','x_span']/2))
    if distance_x < 0:
        print ("ERROR: distance between input and output waveguides (" +str(distance_x)+") is less than 0, Y-Branch has insufficent spacing to be created")
        error_count+=1

    #check distance between two waveguides is greater than 0 in y axis
    
    distance_y = (comp_df.loc['output_wg_top','y']-(comp_df.loc['output_wg_top','y_span']/2))-(comp_df.loc['output_wg_bottom','y']+(comp_df.loc['output_wg_bottom','y_span']/2))
    if distance_y < 0:
        print ("ERROR: distance between top and bottom waveguides(" +str(distance_y)+") is less than 0, output waveguides need to be separated more")
        error_count+=1

    #check if output waveguides if they're aligned on the same axis

    alignment_output_wg = (comp_df.loc['output_wg_top','x']-(comp_df.loc['output_wg_top','x_span']/2))-(comp_df.loc['output_wg_bottom','x']-(comp_df.loc['output_wg_bottom','x_span']/2))
    if alignment_output_wg != 0:
        print ("ERROR: output waveguides are not aligned along y axis, has an alignment mismatch of "+ str(alignment_output_wg))
        error_count+=1

    if error_count == 0:
        print ("No errors detected, datafile can be used for simulations/optimizations")
    else:
        print ("Please revise YAML file, " + str(error_count) + "errors detected")