#!/usr/bin/env python

import os
import datetime
import glob
import yaml
import lasio
import sys

ri_py_path = '/prog/ResInsight/current/Python'                                     #### for resinsight that is available in komodo 
ri_exe = '/prog/ResInsight/current/ResInsight'                                     #### for resinsight that is available in komodo  

sys.path.insert(0, ri_py_path)
print(sys.path)
import rips
print(rips.__file__ + '\n')

## launch ResInsight
resinsight = rips.Instance.launch(resinsight_executable = ri_exe, console=True)#False) 
print("\nResInsight version: " + resinsight.version_string())    

case = resinsight.project.load_case('../ecl/DROGON-7.EGRID')
case.import_formation_names(formation_files='../ecl/simgrid_zone_layer_mapping.lyr')    
view = case.create_view()


well_path_coll = resinsight.project.descendants(rips.WellPathCollection)[0]
well_paths = resinsight.project.import_well_paths(well_path_files=['../resinsight/Well-3.dev'])

well_name = well_paths[-1]
# Add a curve intersection based on the modeled well path
print(f'Add a curve intersection based on the modeled well path')
intersection_coll = resinsight.project.descendants(rips.IntersectionCollection)[0]

well_path_intersection = intersection_coll.add_new_object(rips.CurveIntersection)
well_path_intersection.type = "CS_WELL_PATH"  # One of [CS_WELL_PATH, CS_SIMULATION_WELL, CS_POLYLINE, CS_AZIMUTHLINE, CS_POLYGON]
well_path_intersection.well_path = well_name
well_path_intersection.update()
        
#### Save the project to file

resinsight.project.save('test.rsp')    
resinsight.exit()
