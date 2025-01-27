#!/usr/bin/env python

import sys, os
import argparse
import glob
import yaml

ri_py_path = "/prog/ResInsight/current/Python" 
ri_exe = "/prog/ResInsight/current/ResInsight"
#sys.path.insert(0, ri_py_path)
#print(sys.path)


import rips
print(f"{rips.__file__}\n")

parser = argparse.ArgumentParser(description="""Import a grid file and 
                                                well deviation files and 
                                                export well connection factors from various completion types
                                                of all the wells.""")
parser.add_argument("config_filename", type=argparse.FileType('r'))
args = parser.parse_args()

def add_perforation(start_md, end_md, diameter, skin_factor):
    well_path.append_perforation_interval(start_md=start_md, end_md=end_md, diameter=diameter, skin_factor=skin_factor)
    return

def add_fracture(template, md, orientation, angle, frac_name):
    # Create stim plan template
    fmt_collection = resinsight.project.descendants(rips.FractureTemplateCollection)[0]
    fracture_template = fmt_collection.append_fracture_template(file_path=template)
    fracture_template.orientation = orientation
    if fracture_template.orientation == "Azimuth":
        fracture_template.azimuth_angle = angle
    fracture_template.update()
            
    # Create stimplan fracture from the stimplan fracture template
    fracture = well_path.add_fracture(measured_depth=md, stim_plan_fracture_template=fracture_template)
    fracture.name = frac_name
    fracture.update()
    return

def find_num_fracs(file):
    well_and_num_frac = {}
    with open(file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith('WELL') and line.split()[0].endswith('FRAC'):
                num = line.split()[-1]
                well_name = line.split()[0].split('FRAC')[0]
                well_name = well_name.replace('WELL', 'WELL_')
#                print(f'Well: {well_name}; Number of fractures: {num}')
                well_and_num_frac[well_name] = int(num)
    return well_and_num_frac


with open(args.config_filename.name, 'r') as f:
    data = yaml.safe_load(f)
print(data)


## launch ResInsight
resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True)
#resinsight = rips.Instance.launch(console=True) 
if resinsight is not None: 
    print("\nResInsight version: " + resinsight.version_string())
    egrid = glob.glob(f'eclipse/model/*.EGRID')[0]
    case = resinsight.project.load_case(egrid)
    view = case.create_view()
    view.apply_cell_result(result_type="DYNAMIC_NATIVE", result_variable="SGAS")
    view.set_time_step(0)

    # iterate over wells in the data dictionary
    for well_name, well_data in data['wells'].items():
        
        # iterate over the well attributes
        well_diameter = well_data['diameter']
        perforation_skin = well_data['perforation_skin']
        well_dev = well_data['deviation']
        frac_tmpl = well_data['frac_tmpl']
        frac_inverval = well_data['frac_interval']
        start_md = well_data['frac_interval'][0]
        end_md = well_data['frac_interval'][1]
        orientation_data = list(well_data['orientation'])[0]
        orientation = list(orientation_data.keys())[0]
        azimuth_angle =  list(orientation_data.values())[0]
        
        print(well_dev, frac_inverval, start_md, end_md, azimuth_angle, orientation)#, angle)    
        
        well_paths = resinsight.project.import_well_paths(well_path_files=[well_dev])
        well_path = well_paths[-1]
        well_name = well_path.name
        print(f"\n\n################################ Wellname: {well_name} #################################")
        print(f"- Deviation file: {well_dev}")

        num_fracs = find_num_fracs(data['parameters_file'])[well_name]
        #print(num_fracs)
            
        if num_fracs==1:
            md_frac = (end_md - start_md)/2
            add_fracture(frac_tmpl, md_frac, orientation, azimuth_angle, 'Frac1')
            print(f'\n#### Well name:  {well_path.name}; Fracture ID: frac1; Fracture MD: {md_frac}; Fracture orientation and Azimuth angle: {orientation}, {azimuth_angle}; Number of fractures: {num_fracs}\n')
        else:    
            for i in range(num_fracs):
                frac_spacing = (end_md - start_md)/(num_fracs-1)
                md_frac = (end_md-i*frac_spacing)
                add_fracture(frac_tmpl, md_frac, orientation, azimuth_angle, 'Frac'+str(i+1))
                print(f'\n#### Well name:  {well_path.name}; Fracture ID: Frac{str(i+1)}; Fracture MD: {md_frac}; Fracture orientation and Azimuth angle: {orientation}, {azimuth_angle}; Number of fractures: {num_fracs}\n')

        add_perforation(start_md, end_md, well_diameter, perforation_skin)
    
        sch_file = f'eclipse/include/schedule/{well_path.name}.sch'
        case.export_well_path_completions(time_step=0, 
                                                 well_path_names=[well_path.name], 
                                                 file_split="UNIFIED_FILE", 
                                                 include_perforations=True,
                                                 export_comments=True,#False,
                                                 custom_file_name=sch_file
                                                 )
        print(f"Well complection data exported to: {sch_file}\n")
    
    #### Save the project to file
    ri_proj = 'resinsight/model/peik.rsp'
    print(f"\nResInsight project saved to: {ri_proj}\n")
    resinsight.project.save(ri_proj)
    resinsight.exit()

