#!/usr/bin/env python

import sys
import argparse


ri_py_path = "/prog/ResInsight/current/Python" 
ri_exe = "/prog/ResInsight/current/ResInsight"

sys.path.insert(0, ri_py_path)
#print(sys.path)

import rips
print(f"{rips.__file__}\n")


parser = argparse.ArgumentParser(description="import a grid file and a well deviation file and export well connection factors")
print(f"Python script: {parser.prog}")

parser.add_argument("grid_file", 
                    help="grid file with its full path, must exist!",
                   )

parser.add_argument("deviation_file", 
                    help="well deviation file with its full path, must exist!",
                    )

parser.add_argument("output_file", 
                    help="file name with its full path for exported well connection data"
                   )

parser.add_argument("-r", "--ri_file", 
                    help="file name with its full path if the ResInsight project is to be saved"
                   )
args = parser.parse_args()
print(f"{args} \n")


file_path = args.grid_file
print(f"Grid file: {file_path}")
well_name_path =args.deviation_file
print(f"Well deviation file: {well_name_path} \n")

start_md = 2600
end_md = 3800
rw = 0.216
skin = 0 

project_path = args.ri_file    #"../resinsight/cf_export.rsp"
export_filename = args.output_file    #"../completions/cf.sch"


## launch ResInsight
resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True) 
#resinsight = rips.Instance.launch(console=True) 
print("\nResInsight version: " + resinsight.version_string())     
case = resinsight.project.load_case(file_path)
view = case.create_view()
view.apply_cell_result(result_type="DYNAMIC_NATIVE", result_variable="SOIL")
view.set_time_step(2)

#### Load some wells
well_paths = resinsight.project.import_well_paths(well_path_files=[well_name_path])
well_path = well_paths[0]


well_path.append_perforation_interval(start_md=start_md, end_md=end_md, diameter=rw, skin_factor=skin)
    
case.export_well_path_completions(time_step=0, 
                                     well_path_names=[well_path.name], 
                                     file_split="UNIFIED_FILE", 
                                     include_perforations=True,
                                     export_comments=False,
                                     custom_file_name=export_filename,
                                     )

print(f"\nWell complection data exported to: {export_filename}")

#### Save the project to file
if project_path:
    print(f"ResInsight project saved to: {project_path} \n")
    resinsight.project.save(project_path)
else:
    print(f"ResInsight project not saved \n")
        
resinsight.exit()
