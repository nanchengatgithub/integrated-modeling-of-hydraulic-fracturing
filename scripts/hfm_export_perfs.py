#!/usr/bin/env python

# Connect to ResInsight instance using the environment variable RESINSIGHT_EXECUTABLE
# Can be started directly from ResInsight in GUI
# Use command line parameters to import a case


import rips
import os
from hfm_fracture_modeling import wellname, input_vars
import glob

dev_file = input_vars['dev_file']
formation_file = 'resinsight/input/geogrid_zone_layer_mapping.lyr' #input_vars['formation_file']
init_pres_simgrid_path = input_vars['init_pres_simgrid_path']

well_groupname = input_vars['well_groupname']
start_md = input_vars['start_md']
end_md = input_vars['end_md']
well_diameter = input_vars['well_diameter']
skin_factor = input_vars['skin_factor']

export_filename = 'eclipse/include_pred/schedule/'+wellname+'.sch'
project_path = os.path.join('resinsight/model', wellname+'.rsp')

dynamic_case_path_name = glob.glob(os.path.join(init_pres_simgrid_path, '*.EGRID'))[0]
#print(dynamic_case_path_name)

resinsight = rips.Instance.launch(console=True, launch_port=0, command_line_parameters=['--case', dynamic_case_path_name])
case = resinsight.project.cases()[0]
print('\nName of the case: ', case.name)

#### Load some wells
well_paths = resinsight.project.import_well_paths(well_path_files=[dev_file])

if resinsight.project.has_warnings():
    for warning in resinsight.project.warnings():
        print(warning)

for well_path in well_paths:
    well_path.append_perforation_interval(start_md=start_md, end_md=end_md, diameter=well_diameter, skin_factor=skin_factor)
    
    print('\nExporting well complection data to:', export_filename, '\n')
    case.export_well_path_completions(time_step=0, 
                                      well_path_names=[well_path.name], 
                                      file_split="UNIFIED_FILE", 
                                      include_perforations=True,
                                      export_comments=False,
                                      custom_file_name=export_filename,
                                      )
#### Save the project to file
print("Saving project to: ", project_path)
resinsight.project.save(project_path)

resinsight.exit()

#### edit well group name in WELSPECS in the exported schedule file
#### this current is not available in ResInsight Python API 
with open(export_filename, 'r') as f:
    lines = f.readlines()

with open(export_filename, 'w') as f:
    for idx, line in enumerate(lines):
        if line.startswith("WELSPECS"):
            lines[idx+1] = lines[idx+1].replace(lines[idx+1].split()[1], well_groupname, 1)
        f.write(line)        


#### edit wellname in Eclispe date file to keep wellname consistent,
#### allowing for different wells to be studied
#### 
#ecl = glob.glob('eclipse/model/*.DATA')[0]
#print('Eclipse datafile to be edited: ', ecl)
#
#with open(ecl, 'r') as f:
#    lines = f.readlines()
#
#with open(ecl, 'w') as f:
#    for idx, line in enumerate(lines):
#        if "new_well" in line:
#            print('Before replacement: ', line)
#            line = line.replace('new_well', wellname)
#            print('After replacement: ', line)
#        f.write(line)        
