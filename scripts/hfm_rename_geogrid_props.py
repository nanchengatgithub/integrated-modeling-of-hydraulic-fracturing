#!/usr/bin/env python

import os
from hfm_fracture_modeling import input_vars
import glob
import xtgeo


geogrid_path = input_vars['geogrid_path']
prop_list = ['phit', 'swl', 'klogh', 'kv', 'facies']

geogrid_props =glob.glob(os.path.join(geogrid_path, 'geogrid--*.roff'))
for geogrid_prop in geogrid_props:
    for prop in prop_list:
        if prop in geogrid_prop: 
            print('\nread property file from: ', geogrid_prop)
            p = xtgeo.gridproperty_from_file(geogrid_prop, fformat="roff")
            if prop == 'phit':
                p.name = "PORO"
            if prop == 'swl':
                p.name = "SWL"
            if prop == 'klogh':
                p.name = "PERMX"
            if prop == 'kv':
                p.name = "PERMZ"
            if prop == 'facies':
                p.name = "FACIES"
            p.to_file(geogrid_prop.split('--')[0]+'--'+p.name+'.roff', fformat="roff")
print('\nFinished properly')
