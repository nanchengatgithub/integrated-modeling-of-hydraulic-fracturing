#!/usr/bin/env python

import glob
import datetime as dt
from hfm_fracture_modeling import input_vars, wellname

frac_date = input_vars['frac_date']
print(f'\nFracture date: {frac_date}')

control_mode = input_vars['control_mode']
max_oil_rate = input_vars['max_oil_rate']
max_wat_rate = input_vars['max_wat_rate']
max_gas_rate = input_vars['max_gas_rate']
max_liquid_rate = input_vars['max_liquid_rate']
max_resv = input_vars['max_resv']
min_bhp = input_vars['min_bhp']
min_thp = input_vars['min_thp']
vfp_tab_num = input_vars['vfp_tab_num']

frac_year = str(frac_date.year)
frac_month = dt.datetime.strptime(str(frac_date.month), "%m").strftime("%b").upper()
frac_day = str(frac_date.day)
all_sch_files = glob.glob('eclipse/include_pred/schedule/*.sch')
hf_well_sch_files = glob.glob(f'eclipse/include_pred/schedule/{wellname}*.sch')
if len(all_sch_files) - len(hf_well_sch_files) == 1:
    for sch_file in all_sch_files:
        if wellname not in sch_file:
            sch = sch_file
print('Eclipse schedule file for prediction to be edited: ', sch)


cmmnt = f" \n/ \n----------------------------------------------------------------------------------\n"
inc = f"\nINCLUDE \n\'../include_pred/schedule/{wellname}.sch\'  / \n"
wconprod = f"\nWCONPROD   \n{wellname}  OPEN  {control_mode}  {max_oil_rate}  {max_wat_rate}  {max_gas_rate}  {max_liquid_rate}  {max_resv}  {min_bhp}  {min_thp}  {vfp_tab_num}  /  \n/ \n"
wtest = f"\nWTEST   \n{wellname}   30    PEG    / \n/ \n"
wefac = f"\nWEFAC   \n{wellname}   0.9    / \n/ \n"

with open(sch, 'r') as f:
    lines = f.readlines()

with open(sch, 'w') as f:
    for idx, line in enumerate(lines):
        if not line.startswith('--') and len(line.split())>=3:
            day = line.split()[0]
            mnth = line.split()[1]
            yr = line.split()[2]
            if (frac_day == day and frac_month == mnth and frac_year == yr):
                line = line + cmmnt + inc + wconprod + wtest + wefac + cmmnt +'\nDATES\n'
                print('\nAdded data:\n', line)
        f.write(line)       
