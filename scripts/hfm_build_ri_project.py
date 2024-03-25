#!/usr/bin/env python

# This script builds an ResInsight project and sets up StimPlan model template
# Oct-2022
 

import rips
print('\n' + rips.__file__ + '\n')

import os
import sys
import datetime
from hfm_fracture_modeling import wellname, input_vars
import glob
import time
import csv

#### geo-model from RMS
geogrid_path = input_vars['geogrid_path']
geogrid = os.path.join(geogrid_path, 'geogrid.roff')
print(f'\nStatic model grid: {geogrid}')

#### geogrid properties for fracture modeling
props = ['PERMX', 'PERMZ', 'PORO', 'FACIES', 'SWL']
prop_files = []

for file in glob.glob(os.path.join(geogrid_path, 'geogrid--*.roff')):
    for prop in props:
        if prop in file.split('.roff')[0].split('--')[-1]:
            prop_files.append(file)
print(f'\nAvailable properties from geogrid: \n{prop_files}')

well_name_path = input_vars['dev_file']
print(f'\nWell path file: {well_name_path}')

elastic_properties_file_path = input_vars['elastic_file']
print(f'\nElastic properties file: {elastic_properties_file_path}')

facies_properties_file_path = input_vars['facies_file']
print(f'\nFacies properties file: {facies_properties_file_path}')

formation_file = input_vars['formation_file']
print(f'\nFormation file: {formation_file}')

frac_date = input_vars['frac_date']
print(f'\nDate for fracturing (yyyy-mm-dd): {frac_date}')

#### set path for exporting completion data
export_filename = "eclipse/include_pred/schedule/" + wellname + ".sch"
print(f'\nExport well schedule file: {export_filename}')

#### set name and path for saving ResInsight project
project_path = os.path.join("resinsight/model", wellname + ".rsp")
print(f'\nResInsight project file: {project_path}\n')

# launch ResInsight
resinsight = rips.Instance.launch(console=True, launch_port=0)

# load geogrid
geo_model_case = resinsight.project.load_case(geogrid)
view_geo_model_case = geo_model_case.create_view()
view_geo_model_case.apply_cell_result(result_type="INPUT_PROPERTY", result_variable="PORO")
geo_model_case.import_properties(file_names=prop_files)
geo_model_case.import_formation_names(formation_files=[formation_file])

#### check data source for initial pressure and current pressure
print(f'\nCheck data source for initial pressure and current pressure')
pressure_data_source = input_vars['pressure_data_source']

init_pres_simgrid_path = pressure_data_source[0]['init_pres_simgrid_path']
pres_simgrid_path = pressure_data_source[1]['pres_simgrid_path']
pressure_table_file  = pressure_data_source[2]['pressure_table_file']

no_pt_data = all(x == None for d in pressure_data_source for x in d.values())
if no_pt_data == True:
    sys.exit("Error: No source for pressure data found!\n")

if init_pres_simgrid_path == None:
    print(f'Initial pressure data from pressure table is to be used')
    initial_pressure_source = 'pressure_table'
    with open(pressure_table_file, 'r') as f:
        pres_data = f.readlines()
else:
    egrids = glob.glob(os.path.join(init_pres_simgrid_path, '*.EGRID'))
    for egrid in egrids:
        if os.path.islink(egrid) == False:
            init_pres_case_path = egrid
    print(f'Initial pressure case: {init_pres_case_path}')
    initial_pressure_source = 'init_pressure_simgrid'

    # load simgrid for initial pressure
    init_pres_case = resinsight.project.load_case(init_pres_case_path)
    view_init_pres_case = init_pres_case.create_view()

if pres_simgrid_path == None:
    print(f'Pressure data from pressure table is to be used')
    pressure_source = 'pressure_table'
    time_step_num = 0
    with open(pressure_table_file, 'r') as f:
        pres_data = f.readlines()
else:
    egrids = glob.glob(os.path.join(pres_simgrid_path, '*.EGRID'))
    for egrid in egrids:
        if os.path.islink(egrid) == False:
            pres_case_path = egrid
    print(f'Current pressure case: {pres_case_path}')
    pressure_source = 'pressure_simgrid'

    # load simgrid for pressure at frac_date
    current_pres_case = resinsight.project.load_case(pres_case_path)
    view_current_pres_case = current_pres_case.create_view()
        
    #### Find the desired time step
    time_steps = current_pres_case.time_steps()

    # set default timestep number to be for the last report
    default_time_step_num = len(time_steps)-1
    default_date = datetime.date(time_steps[-1].year, time_steps[-1].month, time_steps[-1].day)
    #print(default_date)
    
    for (ts_idx, time_step) in enumerate(time_steps):
        date = datetime.date(time_step.year, time_step.month, time_step.day)
    #    print(f'\nTimestep number: {ts_idx}, timestep: {date}, found in {current_pres_case_path}')
        if date == frac_date:
            time_step_num = ts_idx
            print(f'\nTimestep number for current pressure date of {frac_date} is found to be: {time_step_num}\n')
            break
        elif date == default_date:
            time_step_num = default_time_step_num
            print(f'\nDate for fracturing {frac_date} not found! The last restart report date {default_date} is used instead')
            print(f'Timestep number for current pressure date defaulted to be {default_date}: {time_step_num}\n')

cases = resinsight.project.cases()
for case in cases:
    print(f'Name of the case: {case.name}; ID of the case: {case.id}')

#### Load some wells
well_paths = resinsight.project.import_well_paths(well_path_files=[well_name_path])

#### Create stim plan model template
fmt_collection = resinsight.project.descendants(rips.StimPlanModelTemplateCollection)[0]
stim_plan_model_template = fmt_collection.append_stim_plan_model_template(
    eclipse_case=geo_model_case,
    time_step=time_step_num,
    elastic_properties_file_path=elastic_properties_file_path,
    facies_properties_file_path=facies_properties_file_path,
)

if initial_pressure_source == 'pressure_table' and pressure_source == 'pressure_table':
    initial_pressure_eclipse_case = geo_model_case
    dynamic_eclipse_case = geo_model_case
    use_pressure_table_for_initial_pressure = True
    use_pressure_table_for_pressure = True

    # Add some pressure table items
    pressure_table = stim_plan_model_template.pressure_table()
    for row in pres_data[1:]:
        tvdmsl = float(row.split(',')[0])
        p_init = float(row.split(',')[1])
        p = float(row.split(',')[2])
        pressure_table.add_pressure(depth=tvdmsl, initial_pressure=p_init, pressure=p)
    
    for item in pressure_table.items():
        print(f'TDVMSL [m]: {item.depth}; Initial Pressure: {item.initial_pressure}; Pressure: {item.pressure}')

    stim_plan_model_template.initial_pressure_eclipse_case = initial_pressure_eclipse_case
    stim_plan_model_template.dynamic_eclipse_case = dynamic_eclipse_case
    stim_plan_model_template.use_pressure_table_for_initial_pressure = use_pressure_table_for_initial_pressure
    stim_plan_model_template.use_pressure_table_for_pressure = use_pressure_table_for_pressure
    stim_plan_model_template.update()
elif initial_pressure_source == 'init_pressure_simgrid' and pressure_source == 'pressure_table': 
    initial_pressure_eclipse_case = init_pres_case
    dynamic_eclipse_case = geo_model_case
    use_pressure_table_for_initial_pressure = False
    use_pressure_table_for_pressure = True

    # Add some pressure table items
    pressure_table = stim_plan_model_template.pressure_table()
    for row in pres_data[1:]:
        tvdmsl = float(row.split(',')[0])
        p_init = float(row.split(',')[1])
        p = float(row.split(',')[2])
        pressure_table.add_pressure(depth=tvdmsl, initial_pressure=p_init, pressure=p)
    
    for item in pressure_table.items():
        print(f'TDVMSL [m]: {item.depth}; Initial Pressure: {item.initial_pressure}; Pressure: {item.pressure}')

    stim_plan_model_template.initial_pressure_eclipse_case = initial_pressure_eclipse_case
    stim_plan_model_template.dynamic_eclipse_case = dynamic_eclipse_case
    stim_plan_model_template.use_pressure_table_for_initial_pressure = use_pressure_table_for_initial_pressure
    stim_plan_model_template.use_pressure_table_for_pressure = use_pressure_table_for_pressure
    stim_plan_model_template.update()
elif initial_pressure_source == 'pressure_table' and pressure_source == 'pressure_simgrid': 
    initial_pressure_eclipse_case = geo_model_case
    dynamic_eclipse_case =  current_pres_case
    use_pressure_table_for_initial_pressure = True
    use_pressure_table_for_pressure = False

    # Add some pressure table items
    pressure_table = stim_plan_model_template.pressure_table()
    for row in pres_data[1:]:
        tvdmsl = float(row.split(',')[0])
        p_init = float(row.split(',')[1])
        p = float(row.split(',')[2])
        pressure_table.add_pressure(depth=tvdmsl, initial_pressure=p_init, pressure=p)
    
    for item in pressure_table.items():
        print(f'TDVMSL [m]: {item.depth}; Initial Pressure: {item.initial_pressure}; Pressure: {item.pressure}')

    stim_plan_model_template.initial_pressure_eclipse_case = initial_pressure_eclipse_case
    stim_plan_model_template.dynamic_eclipse_case = dynamic_eclipse_case
    stim_plan_model_template.use_pressure_table_for_initial_pressure = use_pressure_table_for_initial_pressure
    stim_plan_model_template.use_pressure_table_for_pressure = use_pressure_table_for_pressure
    stim_plan_model_template.update()
else:
    initial_pressure_eclipse_case = init_pres_case
    dynamic_eclipse_case = current_pres_case
    use_pressure_table_for_initial_pressure = False
    use_pressure_table_for_pressure = False

    stim_plan_model_template.initial_pressure_eclipse_case = initial_pressure_eclipse_case
    stim_plan_model_template.dynamic_eclipse_case = dynamic_eclipse_case
    stim_plan_model_template.use_pressure_table_for_initial_pressure = use_pressure_table_for_initial_pressure
    stim_plan_model_template.use_pressure_table_for_pressure = use_pressure_table_for_pressure
    stim_plan_model_template.update()

#### reference input data from user
stim_plan_model_template.reference_temperature = input_vars['reference_reservoir_temperature']
stim_plan_model_template.reference_temperature_gradient = input_vars['reference_temperature_gradient']
stim_plan_model_template.reference_temperature_depth = input_vars['reference_temperature_depth']

#### reference input data from user
stim_plan_model_template.vertical_stress = input_vars['reference_vertical_stress']
stim_plan_model_template.vertical_stress_gradient = input_vars['reference_vertical_stress_gradient']
stim_plan_model_template.stress_depth = input_vars['reference_stress_depth']
stim_plan_model_template.update()

#### det undefined facies
stim_plan_model_template.default_facies = input_vars['overburden_facies']

stim_plan_model_template.overburden_formation = input_vars['overburden_formation']
stim_plan_model_template.overburden_facies = input_vars['overburden_facies']
stim_plan_model_template.overburden_height = input_vars['overburden_height']
stim_plan_model_template.overburden_porosity = input_vars['overburden_porosity']

stim_plan_model_template.underburden_formation = input_vars['underburden_formation']
stim_plan_model_template.underburden_facies = input_vars['underburden_facies']
stim_plan_model_template.underburden_height = input_vars['underburden_height']
stim_plan_model_template.underburden_porosity = input_vars['underburden_porosity']
stim_plan_model_template.update()

# Set eclipse result for facies definition
eclipse_result = stim_plan_model_template.facies_properties().facies_definition()
eclipse_result.result_type = input_vars['result_type']
eclipse_result.result_variable = input_vars['result_variable']
eclipse_result.update()

# Set eclipse result for non-net layers
non_net_layers = stim_plan_model_template.non_net_layers()
non_net_layers_result = non_net_layers.facies_definition()
non_net_layers_result.result_type = input_vars['result_type_non_net']
non_net_layers_result.result_variable = input_vars['result_variable_non_net']
non_net_layers_result.update()
non_net_layers.formation = input_vars['formation_non_net']
non_net_layers.facies = input_vars['facies_non_net']
non_net_layers.cutoff = input_vars['cutoff_non_net']
non_net_layers.update()

# set differential degrees of pressure depletion for coarsened simulation model cells 
# where multiple facies are found in the geo-grid model for the same depth interval
print(f'\nSet degrees of pressure depletion for coarsened simulation model cells where multiple facies are found in the geo-grid model for the same depth interval')
confs = stim_plan_model_template.facies_initial_pressure_configs()
for c in confs:
    for setting in input_vars['facies_pressure_settings']:
        for k, v in setting.items():
            #print(k, v)
            if c.facies_name == k:
                c.fraction = v
    print(f"Facies name: {c.facies_name}; Degree of pressure depletion in fraction: {c.fraction}")
    c.is_checked = True
    c.update()

if resinsight.project.has_warnings():
    for warning in resinsight.project.warnings():
        print(warning)


#### Save the project to file
print(f'\nSaving project to: {project_path}')
resinsight.project.save(project_path)

resinsight.exit()

#### to remove core.* files generated by ResInsight due to a bug
#time.sleep(3)
#print(f'Remove core.* files generated by ResInsight due to a bug')
#for filename in glob.glob(f"core.*"):
#    os.remove(filename) 
