#!/usr/bin/env python

import sys
import argparse
import glob
import yaml

ri_py_path = "/prog/ResInsight/current/Python" 
ri_exe = "/prog/ResInsight/current/ResInsight"
sys.path.insert(0, ri_py_path)
#print(sys.path)

import rips
print(f"{rips.__file__}\n")

parser = argparse.ArgumentParser(description="import a grid file and well deviation files and export well connection factors from various completion types")
parser.add_argument("config_filename", type=argparse.FileType('r'))
args = parser.parse_args()

def add_perforation(start_md, end_md, diameter, skin_factor):
    well_path.append_perforation_interval(start_md=start_md, end_md=end_md, diameter=diameter, skin_factor=skin_factor)
    return

def add_fishbones(start_md, end_md, spacing):
    #well_path.append_fishbones_interval(start_md=start_md, end_md=end_md, spacing=spacing)
    return
    
def add_fracture(template, md, orientation, frac_name):
    # Create stim plan template
    fmt_collection = resinsight.project.descendants(rips.FractureTemplateCollection)[0]
    fracture_template = fmt_collection.append_fracture_template(file_path=template)
    fracture_template.orientation = orientation
    fracture_template.update()
            
    # Create stimplan fracture from the stimplan fracture template
    fracture = well_path.add_fracture(measured_depth=md, stim_plan_fracture_template=fracture_template)
    fracture.name = frac_name #template.split('/')[-1].split('.')[0]
    fracture.update()
    return

## launch ResInsight
resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True) 
#resinsight = rips.Instance.launch(console=True) 
print("\nResInsight version: " + resinsight.version_string())

with open(args.config_filename.name, 'r') as f:
    data = yaml.safe_load(f)

grid = data['grid_file_path']+'*.EGRID'
grid = glob.glob(f'{grid}')[0]
print(f'Grid file: {grid}')     
case = resinsight.project.load_case(grid)
view = case.create_view()
view.apply_cell_result(result_type="DYNAMIC_NATIVE", result_variable="SOIL")
view.set_time_step(0)


# iterate over wells in the data dictionary
for well_name, well_data in data['wells'].items():
    print(f"\nWell name: {well_name}")
    
    # iterate over the well attributes
    for key, value in well_data.items():
        if key == 'deviation':
            print(f"\n- Deviation file: {value}")
            well_paths = resinsight.project.import_well_paths(well_path_files=[value])
            well_path = well_paths[-1] 
            print(f"\n\n#### Wellname: {well_path.name} ####")

        elif key.startswith('perf'):
            print(f"- Perforation {key}: {value}")
            add_perforation(value[0], value[1], value[2], value[3])

        elif key.startswith('fishbones'):
            print(f"\n- Fishbones {key}: {value}")
            add_fishbones(value[0], value[1], value[2])

        elif key.startswith('frac'):
            print(f"\n- Fractures {key}: {value}")
            add_fracture(value[0], value[1], value[2], key)
        
    sch_file = data['output_file_path']+well_path.name+'.sch'
    case.export_well_path_completions(time_step=0,
                                         well_path_names=[well_path.name], 
                                         file_split="UNIFIED_FILE",
                                         include_perforations=True,
                                         export_comments=False,
                                         custom_file_name=sch_file
                                         )
    #case.create_lgr_for_completion(time_step=0, well_path_names[well_path.name], refinement_i=3, refinement_j=3, refinement_k=5, split_type="LGR_PER_WELL")
    
    print(f"\nWell complection data exported to: {sch_file}\n")

#### Save the project to file
print(f"\nResInsight project saved to: {data['resinsight_project_file']} \n")
resinsight.project.save(data['resinsight_project_file'])
resinsight.exit()
