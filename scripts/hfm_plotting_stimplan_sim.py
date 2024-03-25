#!/usr/bin/env python

import glob
import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import shutil

csvs = sorted(glob.glob('stimplan/output/*/data_vs_time.csv'))
print('\n' + str(len(csvs)) + ' data_vs_time.csv files found: ')

for csv in csvs:
    print(csv)
    df = pd.read_csv(csv, skiprows=[0, 2])#, index_col ='Time')
    # drop the last column that is empty
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    df_units = pd.read_csv(csv, skiprows=[0,1]).iloc[0:10]
    df_units = df_units.loc[:, ~df_units.columns.str.contains('^Unnamed: 15')]
    
    #### assign proper unit for each parameter
    units_update = []   
    for ele in df_units.columns:
        if 'Unnamed:' in ele:
            ele = ' (fraction)'
            units_update.append(ele)
        elif '.' in ele:
            ele = " (" + ele[0:ele.find('.')] + ")"
            units_update.append(ele)
        else:
            ele = " (" + ele + ")"
            units_update.append(ele)     
#    print(df_units.head())
    #print(units_update)
    
    # make a new list of columnn with corresponding unit attached 
    new_col_name = [m+str(n) for m,n in zip(df.columns, units_update)]
#### ['Time (min)', 'BHP (bar)', 'Net Pressure (bar)', 'Pump Rate (lpm)', 'Loss Rate (lpm)', 'Concentration (kg/m^3)', 
##### 'Slurry Volume (m^3)', 'Efficiency (fraction)', 'Overall Efficiency (fraction)', 'Penetration (m)', 'Height (m)', 
#### 'Average Width (cm)', 'Temperature (C)', 'Acid Penetration (m)', 'Incremental Fluid Efficiency (fraction)']

#    print(new_col_name) 
    df.columns = new_col_name    
#    print(df.head())
    #### make a smaller dataframe for parameters of interest
    df_reduced = df[['Time (min)','BHP (bar)', 'Net Pressure (bar)', 'Pump Rate (lpm)', 'Loss Rate (lpm)', 'Concentration (kg/m^3)', 
                     'Overall Efficiency (fraction)', 'Penetration (m)', 'Height (m)', 'Average Width (cm)']]
#    print(df_reduced.head())

    info_py = '\n Python script location: ' + os.path.join(os.getcwd(),sys.argv[0])
    info_input = 'Input file: ' + csv
    png = '\n Location of this png plot: ' + csv.split('.csv')[0]+'.png'
    df.plot(title=info_input + png, x=new_col_name[0], subplots=True, grid=True, figsize=(16, 9))
    plt.minorticks_on()
    plt.savefig(csv.split('.csv')[0]+'.png')

    filename = csv.split('.csv')[0] + '_reduced.png'
    png_reduced = '\n Location of this png plot: ' + filename
    df_reduced.plot(title=info_input + png_reduced, x=df_reduced.columns[0], subplots=True, grid=True, figsize=(16, 9))
    plt.minorticks_on()
    plt.savefig(filename)
#    plt.show()
