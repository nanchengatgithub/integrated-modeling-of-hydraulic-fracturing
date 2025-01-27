"""

 This script exports snapshots for various properties (static and dynamic) of each loaded case
 to a snapshots folder located in the same folder as the grid file.
 A video file in .avi format also is generated for each dynamic property and saved in the same folder.

 Reruning the script will always result in a new folder that holds snapshot and video files
 folder naming follows: snapshots_case name_current time

 Put static properties for snapshots into the list named "props_stat"
 Put dynamic properties for snapshots into the list named "props_dyn"

 The user needs to create a python virtual environment to install all necessary packages

 # How to create a virtual environment using python:
 python -m venv myvenv
 cd myvenv/bin/
 source activate or source activate.csh for c-shell
 pip install --upgrade pip

 # How to install the packages required for this script under the virtual environment
 pip install rips 
 pip install opencv-python 
 pip install natsort

 # How to Set up in ResInsight Edit -> Preferences -> Scripting tab 
 In current linux terminal, type 'which python' and copy the printout 
 Find Edit -> Preferences -> Scripting tab and paste in the “Python Executable Location” 
              On the tab, append the folder containing this script to "Shared Script Folder(s)"  
  
 # How to deactivate the virtual environment when finished
 deactivate

 For questions, contact Nan Cheng (nanc@equinor.com)

"""

import os
import datetime
import cv2
from natsort import natsorted
import rips

def get_snapshot_foldername(foldername, case_name):
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(foldername, f'snapshots_{case_name}_{now}')

def create_snapshot_folder(snapshot_dirname):
    os.makedirs(snapshot_dirname, exist_ok=True)
    return snapshot_dirname

def export_snapshot(resinsight, case, snapshot_dirname, props_stat, props_dyn, n):
    resinsight.set_export_folder(export_type='SNAPSHOTS', path=snapshot_dirname)

    view = case.views()[0]
    time_steps = case.time_steps()
    tss_snapshot = range(0, len(time_steps), n)

    print('Simulation case: ' + case.name, ';      Total number of timesteps: ' + str(len(time_steps)))
    print('Toatl number of timesteps for snapshots: ' + str(len(tss_snapshot)))

    property_list = props_stat + props_dyn
    for prop in property_list:
        if prop in props_stat:
            view.apply_cell_result(result_type='STATIC_NATIVE', result_variable=prop)
            view.set_time_step(time_step=0)
            view.export_snapshot()

        if prop in props_dyn:
            view.apply_cell_result(result_type='DYNAMIC_NATIVE', result_variable = prop)

            for ts_snapshot in tss_snapshot:
                view.set_time_step(time_step=ts_snapshot)
                view.export_snapshot()

            images = [img for img in os.listdir(snapshot_dirname) if f'_{prop}_' in img and img.endswith(".png")]
            images = natsorted(images)

            video_file = os.path.join(snapshot_dirname, f'{prop}_{case.name}.avi')
            create_video(snapshot_dirname, video_file, images)

def create_video(snapshot_dirname, video_file, images):
    if len(images) == 0:
        return

    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    frame = cv2.imread(os.path.join(snapshot_dirname, images[0]))
    height, width = frame.shape[:2]
    frame_rate = 5 #  frame/sec
    video = cv2.VideoWriter(video_file, fourcc, frame_rate, (width, height))

    for image in images:
        video.write(cv2.imread(os.path.join(snapshot_dirname, image)))

    video.release()
    cv2.destroyAllWindows()

def main(props_stat, props_dyn, freq):
    resinsight = rips.Instance.find()
    cases = resinsight.project.cases()

    print("\n -------------------------------------------- Looping through cases --------------------------------------------\n")
    for case in cases:
        foldername = os.path.dirname(case.file_path)
        snapshot_dirname = get_snapshot_foldername(foldername, case.name)
        create_snapshot_folder(snapshot_dirname)

        print(f'Exporting to folder: {snapshot_dirname}')
        export_snapshot(resinsight, case, snapshot_dirname, props_stat, props_dyn, freq)

    resinsight.exit()

if __name__ == '__main__':
    props_stat = ['PERMX', 'PORO']                # list of static parameter for snapshots
    props_dyn = ['SOIL', 'SGAS', 'PRESSURE']      # list of recurrent parameter for snapshots
    freq = 3                                      # snapshot to be taken every n-th reported timestep
    main(props_stat, props_dyn, freq)
