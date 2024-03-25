#!/usr/bin/env python
# This script creates a file for facies name and corresponding value in .roff format, if no facies name file is found

import os
from hfm_fracture_modeling import input_vars
import glob
import xtgeo


def make_facies_name_file(grid_path, output_file):
    # find the facies file in binary roff format
    file = os.path.join(geogrid_path, 'geogrid--facies.roff')
    print('\nread facies file from: ', file)
    
    # load the file in binary roff format into xtgeo
    grd = xtgeo.gridproperty_from_file(file, fformat="roff")
    
    grd.to_file(fname, fformat="roff_ascii")
    
    with open(fname, 'r') as f:
        lines = f.readlines()
    
    with open(fname, 'w') as f:
        for line in lines:
            if "FACIES" in line:
                line = 'char name "composite"\n'
            if 'array int data' in line:
                break
            f.write(line)
        f.write("endtag\n")
            
    print(f'File for facies name and corresponding value written to: {fname}')             
    return


geogrid_path = input_vars['geogrid_path']
fname = input_vars['facies_file']

if os.path.isfile(fname):
    print(f"\nFacies name file found: {fname}\n")   
else:
    print(f"\nFacies name file not found and trying to make one based on the facies parameter in RMS model")   
    fname = 'resinsight/input/facies_names.roff'
    make_facies_name_file(geogrid_path, fname)
    print(f"\nA facies name file is made: {fname} ")
