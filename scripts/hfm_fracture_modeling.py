#!/usr/bin/env python
# 2021-12-17

import yaml
import glob


def fm_setup():
    setup_file = glob.glob('resinsight/input/*.yml')
    print(setup_file)
    if len(setup_file) == 1:
        print('\nFracture modeling setup file in .yml found:', setup_file[0])
        with open(setup_file[0]) as f:
            data = yaml.safe_load(f)
    elif len(setup_file) == 0:
        print('\nFracture modeling setup file in .yml not found!')
    else:
        print('\nMore than one fracture modeling setup files in .yml found!')
    return data
input_vars=fm_setup()
print(input_vars)

def well(dev):
    with open(dev, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if 'WELLNAME' in line:
            wellname = line.split()[-1].strip().strip("'")
        if 'Name' in line:
            wellname = line.split()[-1]
    return wellname

wellname = well(input_vars['dev_file'])
print('\nWell name:', wellname)


