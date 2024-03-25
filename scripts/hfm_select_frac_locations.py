#!/usr/bin/env python
# This script is to:  
# 1) find fracture locations within non-shale facies for the well
# 2) update the ResInsight project file with the selected fracture locations
# 3) a plot showing relative locations
# input data: well log (.las from ResInsight), facies file (.roff), formation definition file(.lyr),
#             number of fractures, min fracture spacing and offset distance, formations for fracturing
# output data: locations for the fractures, ResInsight project file with the fracture locations and a plot and a dataframe for non-shale intervals
# Sept-2021

import lasio
import matplotlib.pyplot as plt
import pandas as pd
import math
import xml.etree.ElementTree as ET
import numpy as np
import json
import csv
from pathlib import Path
from hfm_fracture_modeling import wellname, input_vars
import glob


dev_file = input_vars['dev_file']
formation_file = 'resinsight/input/geogrid_zone_layer_mapping.lyr' #input_vars['formation_file']
facies_name = 'resinsight/input/facies_names.roff' #input_vars['facies_file']

formations_for_frac = input_vars['formations_for_frac']
facies_for_frac_initiation = input_vars['facies_for_frac_initiation']

k_index_for_frac_start = input_vars['k_index_for_frac_start']
k_index_for_frac_end = input_vars['k_index_for_frac_end']

min_frac_spacing = input_vars['min_frac_spacing']
default_num_fracs = input_vars['default_num_fracs']
rathole = input_vars['rathole']

las_files = glob.glob(f'resinsight/input/{wellname}*.las')
for las in las_files:
    if wellname in las:
        print(f'LAS file found for well {wellname}: {las}')
        las_file = las
    else:
        print(f'LAS file found for well {wellname} not found')

def num_fractures(num_frac_json):
    with open(num_frac_json, 'r') as f:
        data = json.load(f)
    num_frac = data["num_frac"]
    print('\nThe actual number of fractures directly generated from Everest (not an integer, weakness of Everest itself):', num_frac)
    num_frac = int(math.ceil(num_frac))
    return num_frac

def num_fractures_ert(csv):
    with open(csv, 'r') as f:
        data = f.readlines()
    num_frac = int(data[0])
    #print('\nThe actual number of fractures directly generated from ERT :', num_frac)
    return num_frac

#### specify the number of fracs & minimum fracture spacing
## for Everest
if Path("num_frac.json").is_file() and Path("num_frac.json").stat().st_size > 0:
    number_of_fracs = num_fractures('num_frac.json')
    print('\nNumber of fractures defined by Everest: ', number_of_fracs)
## for ERT
elif Path("resinsight/input/num_fracs.csv").is_file() and Path("resinsight/input/num_fracs.csv").stat().st_size > 0:
    number_of_fracs = num_fractures_ert('resinsight/input/num_fracs.csv')
    print('\nNumber of fractures defined by ERT: ', number_of_fracs)
else:
    number_of_fracs = default_num_fracs
    print('\nNumber of fractures defaulted to : ', number_of_fracs)



###### read formation definition file and find the correspondence between formation name and its numerical ID
with open(formation_file, 'r') as f:
    lines = f.readlines()
formations = {}
index = 0
for line in lines:
    if not line.startswith('--'):
        line = line.replace("'", ' ').strip(' ')
        formations[line.split(' ')[0]] = index
        index = index+1
print('\nFormation names and corresponding IDs: ', formations)


###### read facies definition file and find the correspondence between facies name and its numerical ID
with open(facies_name, 'r') as f:
    lines = f.readlines()
facies = {}
facies_name = []
facies_id = []

for index, line in enumerate(lines):
    if 'array char codeNames' in line:
        number_of_facies = int(line.split()[-1])
        print('\nNumber of facies names found: ', number_of_facies)
        for i in range(number_of_facies):
            facies_name.append(lines[index+i+1].replace('\"', '').strip(' ').replace('\n', ''))
        print('List of facies: ', facies_name)
    if 'array int codeValues' in line:
        number_of_facies_id = int(line.split()[-1])
        print('\nNumber of facies IDs found: ', number_of_facies_id)
        for i in range(number_of_facies_id):
            facies_id.append(lines[index+i+1].replace('\"', '').strip(' ').replace('\n', ''))
        print('List of facies IDs: ', facies_id)

for name, id in zip(facies_name, facies_id):
    facies[name] = int(id)
print('\nFacies names and corresponding IDs: ', facies)

###### read well log file
print('\nName of the well log file:',las_file)
las_data = lasio.read(las_file)
df = las_data.df().reset_index()
print('Directly from las file: \n', df.head())
df = df.rename(columns={'FACIES': 'FACIES_ID', 'ACTIVE_FORMATION_NAMES': 'ACTIVE_FORMATION_ID'})

def find_facies_name(row):
    for key, value in facies.items():
        if row['FACIES_ID'] == int(value):
            return key

def find_formation_name(row):
    for key, value in formations.items():
        if row['ACTIVE_FORMATION_ID'] == int(value):
            return key

# remove cells that are in and near faults
raw_data = df.values.tolist()

chunked_list = []
chunk_size = 2

for i in range(1, len(raw_data), chunk_size):
    chunked_list.append(raw_data[i:i+chunk_size])

tmp = []
for index, sublist in enumerate(chunked_list):
    if len(sublist)==2 and index>0 and index<len(chunked_list):
        if sublist[0][0]!=sublist[1][0]:
            tmp.append(chunked_list[index-1:index+2])

# flatten the list
tmp = [item for sublist in tmp for item in sublist]

# remove unwanted data
final = [item for item in chunked_list if item not in tmp]

# flatten the list
final = [item for sublist in final for item in sublist]

df_cleaned = pd.DataFrame(final, columns = df.columns.to_list()).drop_duplicates('DEPTH', keep='last', ignore_index=True)
df_cleaned.insert(5, 'FACIES_NAME', df_cleaned.apply(lambda row: find_facies_name(row), axis=1))
df_cleaned.insert(8, 'ACTIVE_FORMATION_NAMES', df_cleaned.apply(lambda row: find_formation_name(row), axis=1))

print('\nDepth duplicates and other unwanted data dropped: \n', df_cleaned.head(80).tail(10))

well_td = df_cleaned['DEPTH'].max()
print('\nWell TD: ', well_td, 'm')

#### find lengths of non-shale intervals
d0 = df_cleaned['DEPTH'].values[0]
#print('\nFirst MD', d0)
tvd0 = df_cleaned['TVDMSL'].values[0]
fid0 = df_cleaned['FACIES_ID'].values[0]
formation_id0 = df_cleaned['ACTIVE_FORMATION_ID'].values[0]

data = []
for (d, tvd, fid, formation_id, index_k) in zip(df_cleaned['DEPTH'], df_cleaned['TVDMSL'], df_cleaned['FACIES_ID'], df_cleaned['ACTIVE_FORMATION_ID'], df_cleaned['INDEX_K']):
    l = d - d0
    if (fid != fid0 or formation_id != formation_id0):                            
        data.append([l, d0, d, tvd0, tvd, fid0, formation_id0, index_k])
        fid0 = fid
        d0 = d
        tvd0 = tvd
        formation_id0 = formation_id
    else:
        if l > 10:    # split intervals that are longer than 10 m
            data.append([l, d0, d, tvd0, tvd, fid0, formation_id0, index_k])
            d0 = d
            tvd0 = tvd
#print(data)

df_interval = pd.DataFrame(data, columns = ['LENGTH', 'MD_START', 'MD_END', 'TVD_START', 'TVD_END', 'FACIES_ID', 'ACTIVE_FORMATION_ID', 'INDEX_K'])
df_interval.insert(6, 'FACIES_NAME', df_interval.apply(lambda row: find_facies_name(row), axis=1))
df_interval.insert(8, 'ACTIVE_FORMATION_NAMES', df_interval.apply(lambda row: find_formation_name(row), axis=1))
#print(df_interval.head())

non_shale_facies = facies_for_frac_initiation
print(f'\nInput facies for fracture initiation: {non_shale_facies}')

formations = formations_for_frac
print(f'Input formations for fracture initiation: {formations}')

#### select intervals for defined facies and formations
df_non_shale = df_interval.loc[df_interval['FACIES_NAME'].isin(non_shale_facies) & df_interval['ACTIVE_FORMATION_NAMES'].isin(formations)]

if df_non_shale.shape[0] == 0:
    df_non_shale = df_interval.loc[df_interval['ACTIVE_FORMATION_NAMES'].isin(formations)] 

#print(f'\nNon-shale intervals of the selected facies {non_shale_facies} and within the selected formations {formations}: \n')
#print(f'{df_non_shale} \n')

k_index_min = int(df_non_shale['INDEX_K'].min())
k_index_max = int(df_non_shale['INDEX_K'].max())
print(f'\nk_index_min = {k_index_min}; k_index_max = {k_index_max}')

print(f'\nUser input k-indices: k_index_for_frac_start={k_index_for_frac_start}; k_index_for_frac_end={k_index_for_frac_end}')
if k_index_for_frac_start == 0:
    k_index_for_frac_start = k_index_min
else:
    k_index_for_frac_start = max(k_index_for_frac_start, k_index_min)

if k_index_for_frac_end == 0:
    k_index_for_frac_end = k_index_max
else:
    k_index_for_frac_end = min(k_index_for_frac_end, k_index_max)

k_index_range = range(k_index_for_frac_start, k_index_for_frac_end)
print(f'Final range of k-indices: {k_index_for_frac_start}-{k_index_for_frac_end}')

#### select intervals for the defined k-indices
df_non_shale_final = df_non_shale.loc[df_non_shale['INDEX_K'].isin(k_index_range)]
df_non_shale_final.to_csv("resinsight/output/non_shale_intervals.csv")
print(f'\nFinal non-shale intervals of the selected facies {non_shale_facies} and within the selected formations {formations} and k-indices {k_index_range}: \n')
print(f'{df_non_shale_final} \n')

#### find the formation top for fracturing
formation_top = df_non_shale['MD_START'].min() 
print('\nformation_top of non-shale:',round(formation_top,1), 'm')

fracable_top = df_non_shale_final['MD_START'].min() 
print('fracable_top of non-shale:',round(fracable_top,1), 'm')

formation_bot = df_non_shale['MD_END'].max() 
print('\nformation_bottom of non-shale:',round(formation_bot,1), 'm')

fracable_bot = df_non_shale_final['MD_END'].max() 
print('fracable_bot of non-shale:',round(fracable_bot,1), 'm')

if well_td - fracable_bot >= rathole:
    bottom_clearance = 0
else:
    bottom_clearance = rathole - (well_td - fracable_bot)
#print('\nclearance between the bottom fracture and the end of the last non-shale interval: ', bottom_clearance)

fracable_bot = fracable_bot - bottom_clearance
print('total available length for fracturing: ', round((fracable_bot-fracable_top),1), 'm')


frac_locs = []
frac_info = {}
for i in range(number_of_fracs):
    if number_of_fracs == 1:
        frac_spacing = fracable_bot - fracable_top
        frac_loc = fracable_top + 0.5*(fracable_bot - fracable_top)
        print(frac_loc)
        df_frac = df_non_shale.iloc[(df_non_shale['MD_START']-frac_loc).abs().argsort()[:3]]
    else:
        frac_spacing = (fracable_bot - fracable_top)/((number_of_fracs)-1)
        if frac_spacing < min_frac_spacing:
            number_of_fracs = math.floor((fracable_bot - fracable_top)/min_frac_spacing) + 1
            frac_spacing = (fracable_bot - fracable_top)/((number_of_fracs) - 1)
            print('\nFracture spacing is re-set based on min fracture spacing and the max number of fractures recalculated to be: ', number_of_fracs)
        print('\nInitial frac spacing: ', round(frac_spacing, 1), ' m')
    
        if i == 0:
            frac_loc = fracable_top
        else:
            frac_loc = frac_md + frac_spacing
            if frac_loc > fracable_bot:
                frac_loc = fracable_bot
            frac_loc_min = frac_md + min_frac_spacing
        print('###########################################################################################################################################')
        print('\nProjected location of fracture #', str(i)+' of '+str(number_of_fracs)+':', round(frac_loc, 1), 
                ', to be used as a guide to find fracture location in its vicinity and in non-shale facies\n')
        df_frac = df_non_shale.iloc[(frac_loc - df_non_shale['MD_START']).abs().argsort()[:]]  
        df_frac = df_frac.loc[df_frac['MD_START']>= frac_loc - frac_spacing]
        df_frac = df_frac.drop(df_frac[df_frac['MD_START'] < (frac_loc-0.5*frac_spacing)].index)  
    print(df_frac)#.head())

    if df_frac['MD_START'].min()-frac_loc > 0.5*frac_spacing:
        frac_md = frac_loc
    elif df_frac.shape[0]==0:
        frac_md = frac_loc 
    else:    
        if df_frac['LENGTH'].values[0] > 20:
            frac_md = max(fracable_top, df_frac['MD_START'].values[0]) + 10
        else:
            frac_md = max(fracable_top, df_frac['MD_START'].values[0]) + 0.5 *df_frac['LENGTH'].values[0]   

    frac_md = round(min(frac_md, fracable_bot),2)

    for index, row in df_frac.iterrows():
        if frac_md>=row['MD_START'] and frac_md<=row['MD_END']:
            frac_formation = row['ACTIVE_FORMATION_NAMES']
            frac_facies = row['FACIES_NAME']
            break
        else:
            frac_formation = row['ACTIVE_FORMATION_NAMES']
            frac_facies = 'SHALE'
    print('\nThe selected location of fracture #', str(i)+' of '+str(number_of_fracs)+':', round(frac_md,1))
    frac_locs.append(frac_md)
    frac_info['StimPlanModel_'+f'{(i+1):02}'] = [frac_md, frac_formation, frac_facies]

print('###########################################################################################################################################')
print('\nfinal fracture locations in MD: ', frac_locs) 
print('final frac spacing', [round(x - frac_locs[i - 1],1) for i, x in enumerate(frac_locs)][1:])
print('\nfinal fracture location, formation and facies: ', frac_info, '\n') 
print('###########################################################################################################################################')

with open('resinsight/input/frac_info.json', 'w') as f:
     json.dump(frac_info, f)

######## 
tvd_interp = np.interp(frac_locs, df_cleaned['DEPTH'],df_cleaned['TVDMSL'])
tvd_fracables = np.interp([fracable_top, fracable_bot], df_cleaned['DEPTH'],df_cleaned['TVDMSL'])
tvd_formation_boundaries =  np.interp([formation_top, formation_bot], df_cleaned['DEPTH'],df_cleaned['TVDMSL'])

formation_bot_fm_id9 = df_non_shale.loc[(df_non_shale['ACTIVE_FORMATION_ID'] == 9), :]['MD_END'].max() 
tvd_formation_bot_fm_id9 =  np.interp(formation_bot_fm_id9, df_cleaned['DEPTH'],df_cleaned['TVDMSL'])

#formation_boundary_md = df_cleaned.loc[(df_cleaned['ACTIVE_FORMATION_ID'] == 9), :]['DEPTH'].max()
#formation_boundary_tvd = df_cleaned.loc[(df_cleaned['ACTIVE_FORMATION_ID'] == 9), :]['TVDMSL'].max()

fig = plt.figure(figsize=(10, 8))
# plotting well
plt.plot(df_cleaned['DEPTH'],df_cleaned['TVDMSL'])

# plotting fracable top and bottom
plt.plot(frac_locs, tvd_interp, 'd', label='Fracture locations')
plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [tvd_fracables[0],tvd_fracables[0]], 'g--', label='fracable top')
plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [tvd_fracables[1],tvd_fracables[1]], 'r--', label='fracable bottom')

# plotting formation top and bottom
plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [tvd_formation_boundaries[0],tvd_formation_boundaries[0]], 'g-', label='Top of non-shale intervals')
plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [tvd_formation_boundaries[1],tvd_formation_boundaries[1]], 'r-', label='Bottom of non-shale intervals')
plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [tvd_formation_bot_fm_id9,tvd_formation_bot_fm_id9], 'b:', label='formation boundary(non-shale)')
#plt.plot([df_cleaned['DEPTH'].min(), df_cleaned['DEPTH'].max()], [formation_boundary_tvd,formation_boundary_tvd], 'm-.', label='formation boundary(non-shale)')

plt.title('Fracture locations and boundaries of non-shale intervals')
plt.xlabel('MD')
plt.ylabel('TVDMSL')
plt.legend(loc="upper right")
plt.gca().invert_yaxis()
fig.savefig('resinsight/output/fracture_locations.png')
#plt.show()
