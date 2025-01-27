# pip install moviepy


import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_writer import FFMPEG_VideoWriter


def change_frame_rate(movie_infile, movie_outfile, frame_rate):
    
    clip = VideoFileClip(movie_infile) #'path/to/video.mp4')
    writer = FFMPEG_VideoWriter(movie_outfile, clip.size, frame_rate)
    
    for frame in clip.iter_frames():
        writer.write_frame(frame)
    
    writer.close()

    
def frame_rate_opencv(movie_infile, movie_outfile, frame_rate):

    # Set the frame rate of the output video
    #fps = 30
    
    # Load the video file
    cap = cv2.VideoCapture(movie_infile) 
    
    # Get the video dimensions and frame rate
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    
    # Create an OpenCV video writer with the desired frame rate
    four_cc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(movie_outfile, four_cc, frame_rate, (width, height))
    
    # Iterate over the video frames and write them to the output video
    while cap.isOpened():
        # Read a frame from the input video
        ret, frame = cap.read()
        if not ret:
            break
    
        # Write the frame to the output video
        out.write(frame)
    
    # Release the resources
    cap.release()
    out.release()
    
if __name__ == "__main__":
    movie_infile = 
    movie_infile = 
    fps = 10
    change_frame_rate(movie_infile, movie_outfile, frame_rate)
    
