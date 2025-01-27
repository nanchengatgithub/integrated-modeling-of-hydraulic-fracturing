#!/usr/bin/env python

# def wpo_setup() --> read a config file and make all variables available to subsequent functions
# def create_well() -- > create a well based on the given well targets; 
#                        possible for multi-lateral wells; 
#                        number of well targets can vary
#                        create an intersection along the well path
#                        save the Resinsight project
# def create_well_log() --> export a well log in .las, containing required parameters for the well at the specified timestep
# def select_perf_location() --> select perforation intervals based a set of defined criteria
# def make_well_perfs() --> add well perforations, export well completion data in .sch and save the ResInsight project
#                           update well group name in WELSPECS in the .sch file
#                           if no perforation interval meets the defined criteria, a dummy connection is exported and it is shut
# 

# nanc@equinor.com
# Feb-2022

import os
import datetime
import glob
import yaml
import lasio
import sys

#### set up Python for ResInsight and ResInsight executable
#ri_py_path = '/project/res/x86_64_RH_7/share/resinsight/jenkins_dev_qt/Python/'    #### for resinsightdev
#ri_exe = '/project/res/bin/resinsightdev'                                          #### for resinsightdev

#ri_py_path = '/project/res/x86_64_RH_7/share/resinsight/jenkins_2021.10.3/Python'  #### for resinsight, before it's available in komodo
#ri_exe = '/project/res/x86_64_RH_7/share/resinsight/jenkins_2021.10.3/ResInsight'  #### for resinsight, before it's available in komodo

ri_py_path = '/prog/ResInsight/current/Python'                                     #### for resinsight that is available in komodo 
ri_exe = '/prog/ResInsight/current/ResInsight'                                     #### for resinsight that is available in komodo  

sys.path.insert(0, ri_py_path)
print(sys.path)
import rips
print(rips.__file__ + '\n')


project_path = '../resinsight/carma_demo.rsp'
export_folder = '../well_log'

def wpo_setup():
    setup_file = 'config.yml'
    print(setup_file)
    with open(setup_file) as f:
        data = yaml.safe_load(f)
    return data


def create_well():
    file_path = input_vars['simgrid_path']

    ## launch ResInsight
    resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True)#False) 
    print("\nResInsight version: " + resinsight.version_string())    
    
    case = resinsight.project.load_case(file_path)
    case.import_formation_names(formation_files=input_vars['formation_file'])    
    view = case.create_view()
    view.apply_cell_result(result_type="DYNAMIC_NATIVE", result_variable="SOIL")
    view.set_time_step(0) # 2

    # Add a new modeled well path
    well_path_coll = resinsight.project.descendants(rips.WellPathCollection)[0]
    well_path = well_path_coll.add_new_object(rips.ModeledWellPath)
    well_path.name = input_vars['wellname']
    print(f'\nWell name: {well_path.name}')
    well_path.update()
    
    # Create well targets
    intersection_points = []
    geometry = well_path.well_path_geometry()
    for i in range(len(input_vars['well_targets'])):
        coord = input_vars['well_targets'][i].split()
        target = geometry.append_well_target(coordinate=coord, absolute=True)#, use_fixed_inclination=True, fixed_inclination_value=90)
        intersection_points.append(coord)
    geometry.update()

#    #### currently only available in resinsightdev
#    intersection_coll = resinsight.project.descendants(rips.IntersectionCollection)[0]
#    # Add a CurveIntersection and set coordinates for the polyline
#    intersection = intersection_coll.add_new_object(rips.CurveIntersection)
#    intersection.points = intersection_points
#    intersection.update()

    # Create a lateral at specified location on parent well
    intersection_points = []
    measured_depth = input_vars['tie-in_measured_depth']
    lateral = well_path.append_lateral(measured_depth)
    geometry = lateral.well_path_geometry()
    for i in range(len(input_vars['well_targets_lateral'])):
        coord = input_vars['well_targets_lateral'][i].split()
        target = geometry.append_well_target(coordinate=coord, absolute=True)#, use_fixed_inclination=True, fixed_inclination_value=90)
        intersection_points.append(coord)
    geometry.update()

#    #### currently only available in resinsightdev
#    intersection_coll = resinsight.project.descendants(rips.IntersectionCollection)[0]
#    # Add a CurveIntersection and set coordinates for the polyline
#    intersection = intersection_coll.add_new_object(rips.CurveIntersection)
#    intersection.points = intersection_points
#    intersection.update()

    #### Save the project to file
    print("Saving project to: ", project_path)
    resinsight.project.save(project_path)
    resinsight.exit()
    return 

def create_well_log():
    ## launch ResInsight
    resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True)#False) 

    # open resinsight project file
    project = resinsight.project.open(path=project_path)
    case = project.cases()[0]

    # find the time step number
    time_steps = case.time_steps()
    for (ts_idx, time_step) in enumerate(time_steps):
        date_simgrid = datetime.date(time_step.year, time_step.month, time_step.day)
        if date_simgrid == input_vars['date']:
            time_step_num = ts_idx
            print(f'\nTimestep number for the specified date of {date_simgrid} is found to be: {time_step_num}')
            break
    
    well_log_plot_collection = resinsight.project.descendants(rips.WellLogPlotCollection)[0]
    
    # Get a list of all wells
    wellnames = []
    well_paths = project.well_paths()
    for well_path in well_paths:
        print(f'\nWell name: {well_path.name}')
        wellnames.append(well_path.name)
        well_log_plot = well_log_plot_collection.new_well_log_plot(case, well_path)    
   
        # Create a track for each dynamic property
        prop_type = "DYNAMIC_NATIVE"
        prop_names = input_vars['dynamic_props']
        time_step = time_step_num
        for prop_name in prop_names:
            print(prop_type, prop_name)
            track = well_log_plot.new_well_log_track("Track: " + prop_name, case, well_path)
            c = track.add_extraction_curve(case, well_path, prop_type, prop_name, time_step)

        # Create a track for each static property
        prop_names = input_vars['static_props']
        for prop_name in prop_names:
            if prop_name == 'Active Formation Names':
                prop_type = "FORMATION_NAMES"
            else:
                prop_type = "STATIC_NATIVE"
            print(prop_type, prop_name)
            track = well_log_plot.new_well_log_track("Track: " + prop_name, case, well_path)
            c = track.add_extraction_curve(case, well_path, prop_type, prop_name, time_step)

        well_log_plot.export_data_as_las(export_folder=export_folder)
    print('\nList of wells: ', wellnames)

    #### Save the project to file
    print("Saving project to: ", project_path)
    resinsight.project.save(project_path)
    resinsight.exit()

    return wellnames

def select_perf_location(well_name):
    ###### read well log file
    las_file = glob.glob(os.path.join(export_folder, well_name.replace(' ', '_')+'*.las'))[0]
    print('\nName of the well log file:', las_file)
    las_data = lasio.read(las_file)
    df = las_data.df().reset_index()
    #print('Directly from las file: \n', df.head())

    well_td = df['DEPTH'].max()
    print(f'Well total measured depth: {well_td}')

    condition_0 = df['ACTIVE_FORMATION_NAMES'].isin(input_vars['formation_id'])
    condition_1 = df['SOIL']>input_vars['min_soil']
    condition_2 = df['SWAT']<input_vars['max_swat']
    condition_3 = df['PRESSURE']>input_vars['min_pressure']
    condition_4 = df['PERMX']>input_vars['min_permx']
    conditions = condition_0 & condition_1 & condition_2 & condition_3 & condition_4

    df_selected = df.loc[conditions]
    df_selected.describe().loc[['min','max']]
    print('\nThe selected intervals that meet the defined conditions : \n', df_selected)
    print(df_selected.describe().loc[['min', 'mean', 'max']])

    return df_selected['DEPTH'],  well_td

def make_well_perfs(well_name):
    ## launch ResInsight
    resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True)#False) 

    # open resinsight project file
    project = resinsight.project.open(path=project_path)
    case = project.cases()[0]

    # Find a well
    well_path = project.well_path_by_name(well_name)
    well_name_part = well_name.replace(" ", "_")
    print('\nWell_name:', well_name_part)

    total_perf_length = 0 
    if  perf_depths.size>0:
        for start, end in zip(perf_depths.iloc[::2], perf_depths.iloc[1::2]):
            print(start, end, round(end-start,2))
            well_path.append_perforation_interval(start_md=start, end_md=end, 
                                                  diameter=input_vars['well_diameter'], 
                                                  skin_factor=input_vars['skin_factor']
                                                 )

            total_perf_length = round(total_perf_length + end-start, 2)
        print(f'\nTotal perforation length is {total_perf_length}')   
 
    else:  # create one dummy connection and shut it thereafter
        well_path.append_perforation_interval(start_md=well_total_depth-1, 
                                              end_md=well_total_depth, 
                                              diameter=input_vars['well_diameter'], 
                                              skin_factor=input_vars['skin_factor']
                                             )
        
    export_filename = '../completions/'+well_name_part+'.sch'
    case.export_well_path_completions(time_step=0, 
                                     well_path_names=[well_path.name], 
                                     file_split="UNIFIED_FILE", 
                                     include_perforations=True,
                                     export_comments=False,
                                     custom_file_name=export_filename,
                                     )

    print(f'\nExporting well complection data to: {export_filename} \n')

    #### edit well group name in WELSPECS in the exported schedule file
    #### this currently is not available in ResInsight Python API 

    well_groupname = input_vars['well_groupname']

    with open(export_filename, 'r') as f:
        lines = f.readlines()
    
    with open(export_filename, 'w') as f:
        for idx, line in enumerate(lines):
            if line.startswith("WELSPECS"):
                lines[idx+1] = lines[idx+1].replace(lines[idx+1].split()[1], well_groupname, 1)
                print(f'\nGroup name for the well is set to: {well_groupname} \n') 

            if line.startswith("COMPDAT") and perf_depths.size==0: 
                new_line = '-- Not found any interval meets the defined perf criteria; create one dummy connection and shut it thereafter \n'
                lines[idx+1] = new_line + lines[idx+1].replace(lines[idx+1].split()[5], 'SHUT')
                print(new_line) 
            f.write(line)        
            
    #### Save the project to file
    print("Saving project to: ", project_path)
    resinsight.project.save(project_path)    
    resinsight.exit()
    return

if __name__ == "__main__":
    input_vars = wpo_setup()
    #print(input_vars)
    create_well()
    wells = create_well_log()
    for well in wells:
        print(f'\n######## select perforation intervals for well: {well} ########')
        perf_depths, well_total_depth = select_perf_location(well)

        print(f'\n######## export perforation data for well: {well} ########')
        make_well_perfs(well)

    print('\nFinished properly\n')
