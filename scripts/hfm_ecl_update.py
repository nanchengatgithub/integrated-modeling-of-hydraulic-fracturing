#!/usr/bin/env python

import glob
from pathlib import Path
import os
from hfm_fracture_modeling import input_vars, wellname

# find the max number of connections per well from the schedule file for the fractured well
sch_file = glob.glob(f'eclipse/include_pred/schedule/{wellname}.sch')[0]
with open(sch_file, 'r') as f:
    lines = f.readlines()

def find_max_conns_per_well():
    for idx, line in enumerate(lines):
        if "Maximum number of connections per well" in line:
            print(lines[idx+4])
            max_conns = lines[idx+4].split()[-1]
    return max_conns
max_conns_per_well = find_max_conns_per_well()
print(f'Max number of connections per well: {max_conns_per_well}')


frac_models = sorted(glob.glob(f'stimplan/model/{wellname}/*'))
print(f'\nStimPlan models: {frac_models}')

frac_id = []
for frac_model in frac_models:
    print (frac_model)
    frac_id.append(frac_model.split('_')[-2].lstrip('0'))

hf_kws = ['WOPRL', 'WOPTL', 'WGPRL', 'WGPTL', 'WWPRL', 'WWPTL']
dir_name = 'eclipse/include_pred/summary'
if not os.path.exists(dir_name):
    os.mkdir(dir_name)
print(dir_name)

filename = 'hydraulic_fractures.inc'

with open(os.path.join(dir_name, filename), 'w') as f:
    for hf_kw in hf_kws:
        line = '\n'+hf_kw
        f.write(line)

        for i in frac_id:
            line = f"\n{wellname} {i}  /"
            f.write(line)
        f.write('\n/ \n')

datafile = glob.glob('eclipse/model/*.DATA')[0]
print(f'\nFile edited: {datafile}')

inc = f"\nINCLUDE \n\'../include_pred/summary/{filename}\'  / \n\n"

with open(datafile, 'r') as f:
    lines = f.readlines()

# find the line number for the beginning of WELLDIMS record
for idx, line in enumerate(lines):
    if line.startswith("WELLDIMS"):
        beginning_welldims = idx
        print(line, beginning_welldims)

# find the line number for the end of WELLDIMS record
for idx, line in enumerate(lines[beginning_welldims:len(lines)]):
    if "/" in line and len(line.strip())>1:
        end_welldims = idx
        line_nr_data_welldims = idx + beginning_welldims
        print(line, line_nr_data_welldims)
        break
    if "/" in line and len(line.strip())==1:
        end_welldims = idx
        line_nr_data_welldims = idx-1 + beginning_welldims
        print(line, line_nr_data_welldims)
        break

# update the Eclipse data file
with open(datafile, 'w') as f:
    for idx, line in enumerate(lines):
        if idx == line_nr_data_welldims:
            line = line.replace(line.split()[1], max_conns_per_well)

        if line.startswith("SUMMARY"):
            lines[idx+1] = lines[idx+1] + inc
            print(lines[idx+1])
        f.write(line)
