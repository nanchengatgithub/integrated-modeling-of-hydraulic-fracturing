#!/usr/bin/env python


# Load ResInsight Processing Server Client Library

from pathlib import Path
import rips
import csv
import sys
import pandas as pd
import json
from hfm_fracture_modeling import wellname, input_vars
import glob


ri_prj=glob.glob('resinsight/model/'+wellname+'.rsp')
if len(ri_prj) ==1:
    prj = ri_prj[0]
elif len(ri_prj) ==0:
   print('\n !!! No ResInsight project file found !!!'+ "\n")
   exit
else:
   print('\n !!! More than one ResInsight project files found !!!'+ "\n")
   exit

# launch ResInsightdev
resinsight = rips.Instance.launch(console=True, launch_port=0) 

# open resinsight project file
project = resinsight.project.open(path=prj)

export_folder = 'stimplan/model/'+wellname
print('\nStimplan models are exported to folder: ', export_folder)

# Find a well
well_path = project.well_path_by_name(wellname)
wellname_part = wellname.replace(" ", "_")
print("well path:", well_path, '\nwell_name:', wellname_part)

stim_plan_model_template_collection = project.descendants(rips.StimPlanModelTemplateCollection)[0]

stim_plan_model_template  = stim_plan_model_template_collection.descendants(rips.StimPlanModelTemplate)[0]
print(stim_plan_model_template)

# Add some scaling factors, read from a file that is created by ERT
df = pd.read_csv('resinsight/input/elastic_scaling_factors.csv')
print('elastic property scaling factors:')
print(df)
elastic_properties = stim_plan_model_template.elastic_properties()
for index, row in df.iterrows():
    print('Add scaling factors: formation =',row['formation'], ', facies =',row['facies'], ', property =',row['property'], ', scale =',row['scale'])
    elastic_properties.add_property_scaling(formation=row['formation'], facies=row['facies'], property=row['property'], scale=row['scale'])

stim_plan_model_collection = project.descendants(rips.StimPlanModelCollection)[0]

# Find the calculated measured depths and zone for fractures
with open('resinsight/input/frac_info.json', 'r') as f:
     data = json.loads(f.read())

# Create a StimPlan model for each depth
for key, value in data.items():
    i = int(key.split('_')[-1])
    measured_depth = value[0]
    zone = value[1].split('.')[0]
    print('\nMeasured depth for StimPlan model #', str(i), 'is:',str(measured_depth), 'm; in zone: ', zone)

    # Create stim plan model at a given measured depth
    stim_plan_model = stim_plan_model_collection.append_stim_plan_model(
        well_path=well_path,
        measured_depth=measured_depth,
        stim_plan_model_template=stim_plan_model_template,
    )

    stim_plan_model.perforation_length = input_vars['perforation_length']
    stim_plan_model.fracture_orientation = input_vars['fracture_orientation']
    stim_plan_model.update()  ### to update the resinsight project file

    stim_plan_model.extraction_offset_top = input_vars['extraction_offset_top']
    stim_plan_model.extraction_offset_bottom = input_vars['extraction_offset_bottom']
    stim_plan_model.name = key + '_' + zone
    stim_plan_model.update()

resinsight.project.save(prj)
resinsight.project.close()

resinsight.project.open(prj)

print(f'\nExport StimPlan models ...')
stim_plan_models = project.descendants(rips.StimPlanModel)
for stim_plan_model in stim_plan_models:
    directory_path = Path(export_folder)/'{}{}'.format(wellname_part+ '_', stim_plan_model.name)
    # Create the folder
    directory_path.mkdir(parents=True, exist_ok=True)

    print(f'\nExporting {stim_plan_model.name} to directory: {directory_path} \n')
    stim_plan_model.export_to_file(directory_path=directory_path.as_posix())


#### this requires GPU (only available on rgs nodes) to function
#    # Create a fracture mode plot
#    stim_plan_model_plot_collection = project.descendants(
#        rips.StimPlanModelPlotCollection
#    )[0]
#    stim_plan_model_plot = stim_plan_model_plot_collection.append_stim_plan_model_plot(
#        stim_plan_model=stim_plan_model
#    )
#
#    print("Exporting fracture model plot to: ", directory_path)
#    stim_plan_model_plot.export_snapshot(export_folder=directory_path.as_posix())

resinsight.project.save(prj)
resinsight.exit()
