"""

 This script exports snapshots for various properties of each loaded case
 to a snapshots folder located in the same folder as the case grid
 Dynamic property can also be generated

 A video file in .avi format also is generated for each dynamic property

 Reruning the script will always result in a new folder that holds snapshot and video files
 folder naming follows: snapshots_current time_case name

 Put static properties into the list named "props_stat"
 Put dynamic properties into the list named "props_dyn"

 The user needs to create a python virtual environment to install all necessary packages

 # How to create a virtual environment using python:
 python -m venv myvenv
 cd myvenv/bin/
 source activate
 pip install --upgrade pip
 pip install rips 

 # How to install the packages required for this script under the virtual environment
 pip install opencv-python 
 pip install natsort

 # How to Set up in ResInsight Edit -> Preferences -> Scripting tab 
 In current linux terminal, type 'which python'
 Copy the output 
 Find Edit -> Preferences -> Scripting tab and paste in the “Python Executable Location” 

 # How to deactivate the virtual environment when finished
 deactivate

 For questions, contact Nan Cheng (nanc@equinor.com)

"""
import os
import rips
import cv2
import datetime
from natsort import natsorted

#now = str(datetime.datetime.now())[:19]
#now =  now.replace(' ', '_').replace(':', '').replace('-', '') + '_' 
now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# Load instance
resinsight = rips.Instance.find()
cases = resinsight.project.cases()


# Set main window size
#resinsight.set_main_window_size(width = 800, height = 500)


props_stat = ['PERMX']                # list of static parameter for snapshot
props_dyn = ['SOIL', 'PRESSURE']      # list of recurrent parameter for snapshots
property_list = props_stat + props_dyn

n = 1                                 # snapshot to be taken every n-th timestep

print ("\n -------------------------------------------- Looping through cases --------------------------------------------\n")
for case in cases:

    foldername = os.path.dirname(case.file_path)
    
    # create a folder to hold the snapshots
    snapshot_dirname = os.path.join(foldername, f'snapshots_{case.name}_{now}')
    os.makedirs(snapshot_dirname, exist_ok=True)
    
#    if os.path.exists(snapshot_dirname) is False:
#        os.mkdir(snapshot_dirname)
    
    print ("Exporting to folder: " + snapshot_dirname)
    resinsight.set_export_folder(export_type = 'SNAPSHOTS', path = snapshot_dirname)
   
    timeSteps = case.time_steps()
    tss_snapshot = range(0, len(timeSteps), n)
    print('Simulation case: ' + case.name, ';      Total number of timesteps: ' + str(len(timeSteps)))
    print('Toatl number of timesteps for snapshots: ' + str(len(tss_snapshot)) + '\n')
    
    fourcc = 0
    view = case.views()[0]
    for prop in property_list:
        if prop in props_stat:
            view.apply_cell_result(result_type = 'STATIC_NATIVE', result_variable = prop)
            view.set_time_step(time_step = 0)
            view.export_snapshot()
            
        elif prop in props_dyn:
            view.apply_cell_result(result_type = 'DYNAMIC_NATIVE', result_variable = prop)
            
            for ts_snapshot in tss_snapshot:
                view.set_time_step(time_step = ts_snapshot)   
                view.export_snapshot()                              # ‘ALL’, ‘VIEWS’ or ‘PLOTS’ default is 'ALL'


            # read all images and make a video for the property  
            video_file = prop + '_' + case.name + '.avi'

            images = [img for img in os.listdir(snapshot_dirname) if '_'+ prop+ '_' in img if img.endswith(".png")]
            images = natsorted(images)
            
            frame = cv2.imread(os.path.join(snapshot_dirname, images[0]))
            
            height, width = frame.shape[:2]
            frame_rate = 1  # 1 frame per second

            video = cv2.VideoWriter(os.path.join(snapshot_dirname, video_file), fourcc,  frame_rate, (width, height))
            
            for image in images:
                video.write(cv2.imread(os.path.join(snapshot_dirname, image)))
            
            video.release()
            cv2.destroyAllWindows()

resinsight.exit()
