#!/usr/bin/env python


#### this script QCs the StimPlan models that are exported from ResInsight by plotting all relevant data together
#### Sept 2021

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
import os
import glob
from hfm_fracture_modeling import wellname, input_vars


def stimplan_model_qc(model_dir, lastdata):
    """
       This function plots all the key data of a stimplan model that is generated from ResInsight and data in LASTDATA file.
       Input is a directory that contains the model files: Geological.frk, Deviation.frk and Perfs.frk and the LASTDATA file
    """

    geom = os.path.join(model_dir, 'Geological.frk')
    dev = os.path.join(model_dir, 'Deviation.frk')
    perfs = os.path.join(model_dir, 'Perfs.frk')
    lastdata = lastdata

    ### process Deviation.frk file
    tree = ET.parse(dev)
    root = tree.getroot()
    for child in root:
        depth_type=child.find("name").text
        depth_type=depth_type.strip('\n')
        if depth_type == "mdArray":
            md=child.find("data").text
            md=md.split('\n')[1:-1]
        if depth_type == "tvdArray":
            tvd=child.find("data").text
            tvd=tvd.split('\n')[1:-1]

    md = [float(i) for i in md]
    tvd = [float(i) for i in tvd]

    ### process Perfs.frk file
    tree = ET.parse(perfs)
    root = tree.getroot()
    perf_top_md=float(root.find(".//topMD").text)
    perf_bot_md=float(root.find(".//bottomMD").text)

    f = interp1d(md, tvd, kind = 'linear')
    perf_top_tvd = f(perf_top_md)
    perf_bot_tvd = f(perf_bot_md)

    ### process Geological.frk file
    tree = ET.parse(geom)
    root = tree.getroot()
    for child in root:
        depth_type=child.find("name").text
        depth_type=depth_type.strip('\n')
        if depth_type == "dpthlyr":
            geom_tvd = child.find("data").text
            geom_tvd = geom_tvd.split('\n')[1:-1]
    print('Number of layers of the StimPlan geomodel: ',str(len(geom_tvd)))
    geom_top_tvd = float(geom_tvd[0])
    geom_bot_tvd = float(geom_tvd[-1])

    ### process lastdata.FRK file
    lastdata_well_md = []
    lastdata_well_tvd = []

    with open(lastdata, 'r', errors='ignore') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            ### process grid depths
            if line.startswith("espgridtop"):
                lastdata_grid_top = float((lines[index+1]))
            if line.startswith("espgridbot"):
                lastdata_grid_bot = float((lines[index+1]))
            ### process perf depths
            # if depths are md
            if line.startswith("Frac_1:perfTop"):
                lastdata_perf_top_md = float((lines[index+1]))
            if line.startswith("Frac_1:perfBottom"):
                lastdata_perf_bot_md = float((lines[index+1]))
            ### process layer depths
            if line.startswith("dpthlyr"):
                lastdata_num_lyrs = int(lines[index+4])
                lastdata_layer_top = float((lines[index+6]))
                lastdata_layer_bot = float((lines[index+6+lastdata_num_lyrs-1]))
            ### process well trajectory
            if line.startswith("mdArray"):
                lastdata_num_pt = int(lines[index+4])
                #print(lastdata_num_pt)
                for i in range(0, lastdata_num_pt):
                    lastdata_well_md.append(float(lines[index+6+i]))
                #print(len(lastdata_well_md))
            if line.startswith("tvdArray"):
                lastdata_num_pt = int(lines[index+4])
                #print(lastdata_num_pt)
                for i in range(0, lastdata_num_pt):
                    lastdata_well_tvd.append(float(lines[index+6+i]))
                #print(len(lastdata_well_tvd))


    f = interp1d(lastdata_well_md, lastdata_well_tvd, kind = 'linear')
    lastdata_perf_top_tvd = f(lastdata_perf_top_md)
    lastdata_perf_bot_tvd = f(lastdata_perf_bot_md)
#

    fig = plt.figure(figsize=(10, 8))
    plt.plot(md, tvd, 'r-', label='well trajectory')
    plt.plot(perf_top_md, perf_top_tvd, 'go', label='Perf top')
    plt.plot(perf_bot_md, perf_bot_tvd, 'bo', label='Perf bottom')
    plt.plot([0, max(md)], [geom_top_tvd, geom_top_tvd], 'm-', label='geo-model top')
    plt.plot([0, max(md)], [geom_bot_tvd, geom_bot_tvd], 'k-', label='geo-model bottom')

    ### lastdata 
    plt.plot(lastdata_perf_top_md, lastdata_perf_top_tvd, 'gP', label='lastdata_Perf top')
    plt.plot(lastdata_perf_bot_md, lastdata_perf_bot_tvd, 'bP', label='lastdata_Perf bottom')
    plt.plot([0, max(md)], [lastdata_grid_top, lastdata_grid_top], 'm--', label='lastdata_grid_top')
    plt.plot([0, max(md)], [lastdata_grid_bot, lastdata_grid_bot], 'k--', label='lastdata_grid_bot')
    plt.plot([0, max(md)], [lastdata_layer_top, lastdata_layer_top], 'm:', label='lastdata_layer_top')
    plt.plot([0, max(md)], [lastdata_layer_bot, lastdata_layer_bot], 'k:', label='lastdata_layer_bot')
    plt.plot(lastdata_well_md, lastdata_well_tvd, 'b--', label='lastdata well trajectory')


#    plt.ylim(0.9*geom_top_tvd, 1.1*geom_bot_tvd)
    plt.legend()
    plt.gca().invert_yaxis()
    plt.title('Location of the model and lastdata: '+model_dir + '\n' + lastdata, fontsize=8)
    plt.xlabel('MD', fontsize=16)
    plt.ylabel('TVD', fontsize=16)
#    plt.show()
    return fig

############################ QC of model dimensions and well  #########################################


models = glob.glob(f'stimplan/model/{wellname}/*')
lastdata_files = glob.glob('stimplan/input/*.FRK')

for model in models:
    print(f'\nStimPlan model: {model}')
    lastdata = input_vars['default_base_data']

    zone = model.split('_')[-1]

    for lastdata_file in lastdata_files:
        if zone in lastdata_file:
            lastdata = lastdata_file
    print(f'StimPlan basedata: {lastdata}')

    fig=stimplan_model_qc(model, lastdata)
    fig_name = model.split('/')[-1] + '.png'
    fig.savefig(os.path.join(model, fig_name))



############################ QC of input parameters #########################################

def stimplan_base_file(base_file, prop):
    prop_data_base_file = []
    depth_base_file = []
    with open(base_file, 'r', errors='ignore') as f:
        lines = f.readlines()
        for index, line in enumerate(lines):
            ### process well trajectory
            if line.strip()==prop:
                num_pt = int(lines[index+4])
                #print(f'\nNumber of data points for property {prop} of : {num_pt}')
                for i in range(0, num_pt):
                    prop_data_base_file.append(float(lines[index+6+i]))
                #print(prop_data_base_file)
            if line.strip()=='dpthlyr':
                num_pt = int(lines[index+4])
                #print(f'\nNumber of data points for property {prop} of : {num_pt}')
                for i in range(0, num_pt):
                    depth_base_file.append(float(lines[index+6+i]))
    return [depth_base_file, prop_data_base_file]

def geological(geom, prop):
    ### process Geological.frk file
    tree = ET.parse(geom)
    root = tree.getroot()
    for child in root:
        if child.find("name").text.strip() == prop:
            #print(child.find("name").text)
            prop_data_str = child.find("data").text.split('\n')
            prop_data_lst = list(filter(None, prop_data_str))
            prop_data_geomodel = [float(i) for i in prop_data_lst]
            #print(prop_data_geomodel)
        if child.find("name").text.strip() == 'dpthlyr':
            #print(child.find("name").text)
            depth_data_str = child.find("data").text.split('\n')
            depth_data_lst = list(filter(None, depth_data_str))
            depth_data_geomodel = [float(i) for i in depth_data_lst]
    return [depth_data_geomodel, prop_data_geomodel]



def plot_data(base_file, stimplan_geomodel):
    fig, ax = plt.subplots(1, len(props), sharey=True, figsize=(24, 12))
    i = 0
    
    for key, value in props.items():
        print(f'\n###################### {value} ({key}) ######################')
        data_base_file = stimplan_base_file(base_file, key)
        data_geomodel = geological(stimplan_geomodel, key)
        if key == 'zoneHorizPerm':
            ax[i].semilogx(data_base_file[1], data_base_file[0], 'r-o', label = base_file.split('/')[-1])
            ax[i].semilogx(data_geomodel[1], data_geomodel[0], 'b-x', label = stimplan_geomodel.split('stimplan/model/')[-1])
        else:
            ax[i].plot(data_base_file[1], data_base_file[0], 'r-o', label = f'StimPlan base file') 
            ax[i].plot(data_geomodel[1], data_geomodel[0], 'b-x', label = f'StimPlan Geomodel')
        ax[i].grid(linestyle='--')
        ax[i].minorticks_on()
        ax[i].set_xlabel(f'{value} ({key})')

        i = i + 1
    
    fig.text(0.06, 0.5, f'Depth', ha='center', va='center', rotation='vertical')
    plt.gca().invert_yaxis()
    plt.suptitle(f'{base_file} \n{stimplan_geomodel}')
    plt.legend()
    filename = stimplan_geomodel.split('.frk')[0]+'_vs_'+base_file.split('/')[-1].split('.FRK')[0]+'.png'
    fig.savefig(filename)
    #plt.show() 
    return


stimplan_minifrac_base_files = sorted(glob.glob(f'stimplan/input/*minifrac*.FRK'))
stimplan_mainfrac_base_files = sorted(glob.glob(f'stimplan/input/*mainfrac*.FRK'))
stimplan_geomodels = sorted(glob.glob(f'stimplan/model/{wellname}/*/Geological.frk'))

props = {'strs':'stress at top of layer', 'strsg':'stress gradient', 'elyr':'Young\'s moduls', 'poissonr': 'Poisson\'s ratio',
         'tuflyr': 'fracture toughness', 'clyrc': 'fluid loss coefficient', 'clyrs':'spurt loss', 'pembed':'proppant embedment',
          'zoneHorizPerm':'permx'}


for base_file, stimplan_geomodel in zip(stimplan_minifrac_base_files, stimplan_geomodels):
    print(f'\nStimplan minifrac base file: {base_file} \nStimPlan geo-model: {stimplan_geomodel}')
    plot_data(base_file, stimplan_geomodel)

for base_file, stimplan_geomodel in zip(stimplan_mainfrac_base_files, stimplan_geomodels):
    print(f'\nStimplan mainfrac base file: {base_file} \nStimPlan geo-model: {stimplan_geomodel}')
    plot_data(base_file, stimplan_geomodel)

    
