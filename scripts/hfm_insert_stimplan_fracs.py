#!/usr/bin/env python
# Load ResInsight Processing Server Client Library
# Oct-2021

import json
import os
import sys
import rips
from hfm_fracture_modeling import wellname, input_vars
import glob

well_groupname = input_vars['well_groupname']
fracture_orientation = input_vars['fracture_orientation']
export_filename = 'eclipse/include_pred/schedule/'+ wellname+'.sch'

ri_prj=glob.glob(os.path.join('resinsight/model', wellname+'.rsp'))

if len(ri_prj) == 1:
    prj = ri_prj[0]
    print('\nResInsight project file: ', prj)
elif len(ri_prj) == 0:
    print('\n !!! No ResInsight project file found !!!'+ "\n")
else:
    print('\n !!! more than one ResInsight project files found !!!'+ "\n")
    exit

# launch ResInsight
resinsight = rips.Instance.launch(console=True, launch_port=0) 

# open resinsight project file
project = resinsight.project.open(path=prj)

# Find a well
well_path = project.well_path_by_name(wellname)
wellname_part = wellname.replace(" ", "_")
print("\nWell path:", well_path, '\nwellname:', wellname_part)

# Find cases in the project
cases = resinsight.project.cases()
if len(cases) == 1:     # only geo-grid exists in the ResInsight project; import a simulation grid
    # load a simgrid for exporting well connections
    sim_grid = glob.glob(f'eclipse/model/*.EGRID')[0]
    print(f'Well connections will be exported for the grid: {sim_grid}')
    case_sim_grid = project.load_case(sim_grid)
    view_sim_grid = case_sim_grid.create_view()

for case in resinsight.project.cases():
    print(f'Grid name: {case.name}')

# set the active case to the simgrid for pressure on fracturing date 
case = resinsight.project.cases()[-1]
print('\nSimulation grid name:', case.name)

# Find the calculated measured depths for fractures
with open('resinsight/input/frac_info.json', 'r') as f:
    d = json.load(f)

xmls = glob.glob(f'resinsight/input/{wellname}*.xml')
xmls = sorted(xmls, key=lambda xml: xml.split('_')[-2])
print('\nList of StimPlan fracture templates in the folder of resinsight/input/:\n', xmls)


# Create stim plan template
fmt_collection = project.descendants(rips.FractureTemplateCollection)[0]

#### add StimPlan fracture templates and create fractures
for xml in xmls:
    for key, value in d.items():
        if key in xml.split('.xml')[0]:
            print('\nCurrent model: ', xml) 
            measured_depth = value[0]
    
            print('Placing fracture at Measured depth (m):', str(measured_depth)+';', 'Fracture template is:', xml)
    
            # Create stimplan fracture template
            fracture_template = fmt_collection.append_fracture_template(file_path=xml)
            fracture_template.orientation = fracture_orientation
            fracture_template.update()
        
            # Create stimplan fracture from the stimplan fracture template
            fracture = well_path.add_fracture(
                measured_depth=measured_depth,
                stim_plan_fracture_template=fracture_template,
            )
            fracture.name = xml.split('.xml')[0].split('/')[-1].replace(wellname+'_', 'Fracture from ')
            fracture.update()

#### export completion data to the output folder
print('\nExporting well complection data to:', export_filename, '\n')
case.export_well_path_completions(time_step=0, 
                                      well_path_names=[wellname_part], 
                                      file_split="UNIFIED_FILE", 
                                      include_perforations=True,
                                      export_comments=True,
                                      custom_file_name=export_filename,
                                  )

# save the project
resinsight.project.save(prj)
resinsight.exit()

#### edit well group name in WELSPECS in the exported schedule file
#### this is currently not available in ResInsight Python API 
with open(export_filename, 'r') as f:
    lines = f.readlines()

with open(export_filename, 'w') as f:
    for idx, line in enumerate(lines):
        if line.startswith("WELSPECS"):
            lines[idx+1] = lines[idx+1].replace(lines[idx+1].split()[1], well_groupname, 1)
        f.write(line)        

#### add keyworkd COMPLUMP - one completion number per fracture
print('Add Eclipse keyword COMPLUMP - one lumped completion number per fracture')
with open(export_filename, 'a') as f:
    f.write('\n-- WELL                              COMPLETION\n')
    f.write('-- NAME        I    J    K1    K2    NUMBER')
    f.write('\nCOMPLUMP\n')

    #### if two or more fracs overlay, connections in the overlain area are lumped into the last frac 
    for idx, line in enumerate(lines):
        if line.startswith("-- Fracture"):
            if lines[idx+1].strip().split()[0] == wellname:
                lines[idx+1] = lines[idx+1].split('OPEN')[0] + line.split('_')[-2].lstrip('0') + '   /\n'
                f.write(line)
                f.write(lines[idx+1])
            else:
                f.write(line)                
    f.write('   /')      

