#!/usr/bin/env python
# coding=utf-8

# This script is to update the LASTDATA files with input from ERT-generated 'stimplan/lastdata/stimplan_dfl_cw.csv'
# Nov-2021

import glob
import csv


stimplan_dfl_cw_file = 'stimplan/input/stimplan_dfl_cw.csv'

def dfl_cw(file):
    with open(file, 'r') as f:
        data = f.readlines()
        cw = data[0]
    return cw

def lastdata_mod(file):
    with open(file, 'r', errors='ignore') as f:
        lines = f.readlines()

    with open(file, 'w') as f:
        for index, line in enumerate(lines):
            if line.startswith("fl_cw"):
                print('\nData section modified: ', line)
                print('Before replacement: ', lines[index+8])
                lines[index+8] = lines[index+8].replace(lines[index+8], dfl_cw(stimplan_dfl_cw_file))
                print('After replacement: ', lines[index+8])
            f.write(line)
    return
 
for lastdata_file in glob.glob('stimplan/input/*.FRK'):
    lastdata_mod(lastdata_file)
    print(lastdata_file)




