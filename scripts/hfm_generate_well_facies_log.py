#!/usr/bin/env python

# Load ResInsight Processing Server Client Library
import rips
import sys
import os
from hfm_fracture_modeling import wellname, input_vars
import glob


formation_file = 'resinsight/input/geogrid_zone_layer_mapping.lyr' #input_vars['formation_file']
print(f'\nFormation file for geogrid is: {formation_file}')

well_dev = input_vars['dev_file']
print(f'Well deviation file is: {well_dev}')

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

export_folder = "resinsight/input"
print(f'Generated well facies log file is exported to folder: {export_folder}\n')


# Dynamic properties, last parameter is time step index
properties_dynamic = [
    ("DYNAMIC_NATIVE", "PRESSURE", 0),
]

properties_static = [
    ("INPUT_PROPERTY", "PORO"),
    ("INPUT_PROPERTY", "PERMX"),
    ("INPUT_PROPERTY", "PERMZ"),
    ("INPUT_PROPERTY", "FACIES"),
    ("STATIC_NATIVE", "INDEX_K"),
    ("FORMATION_NAMES", "Active Formation Names"),
]

# launch ResInsight
resinsight = rips.Instance.launch(console=True, launch_port=0)

# load geogrid
geo_model_case = resinsight.project.load_case(geogrid)
view_geo_model_case = geo_model_case.create_view()
view_geo_model_case.apply_cell_result(result_type="INPUT_PROPERTY", result_variable="PORO")
geo_model_case.import_properties(file_names=prop_files)
geo_model_case.import_formation_names(formation_files=[formation_file])

cases = resinsight.project.cases()
# Assuming the first case is the static case
static_case = cases[0]


# Load some wells
well_paths = resinsight.project.import_well_paths(
    well_path_files=[well_dev]
)

if resinsight.project.has_warnings():
    for warning in resinsight.project.warnings():
        print(warning)

well_log_plot_collection = resinsight.project.descendants(
    rips.WellLogPlotCollection
)[0]

for well_path in well_paths:
    well_log_plot = well_log_plot_collection.new_well_log_plot(static_case, well_path)

    # Create a track for each static property
    for (prop_type, prop_name) in properties_static:
        track = well_log_plot.new_well_log_track(
            "Track: " + prop_name, static_case, well_path
        )

        c = track.add_extraction_curve(
            static_case, well_path, prop_type, prop_name, time_step=0
        )

#    # Create a track for each dynamic property
#    for (prop_type, prop_name, time_step) in properties_dynamic:
#        track = well_log_plot.new_well_log_track(
#            "Track: " + prop_name, dynamic_case, well_path
#        )
#
#        c = track.add_extraction_curve(
#            dynamic_case, well_path, prop_type, prop_name, time_step
#        )
#
    well_log_plot.export_data_as_las(export_folder=export_folder)

resinsight.exit()
