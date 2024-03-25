#!/usr/bin/env python
# This script creates a file of formation names for geogrid
# The result file is: 'resinsight/input/geogrid_zone_layer_mapping.lyr'

import os
from hfm_fracture_modeling import input_vars
import yaml


geogrid_path = input_vars['geogrid_path']

# find the input file in rms/output/zone/zonation_geo_map.yml
input_file = 'rms/output/zone/zonation_geo_map.yml'
file = os.path.join(geogrid_path.split('share')[0], input_file)

with open(file) as f:
    d = yaml.safe_load(f)
for key, value in d.items():
    lst = value

fname = 'resinsight/input/geogrid_zone_layer_mapping.lyr'
with open(fname, 'w') as f:
    line = f'-- input file is: {file} \n'
    print(line)
    f.write(line)
    for ele in lst:
        for key, value in ele.items():
            line = '\''+key+'\'' + '    ' + str(value[0]) + ' - ' + str(value[1]) + '\n'
            f.write(line)
print(f'File of formation names for geogrid written to: {fname} ')             
