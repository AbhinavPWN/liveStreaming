import os
import shutil
from datetime import datetime
import pyrtmp
from django.http import HttpResponse
from django.shortcuts import render
import subprocess

from videolive.settings import MEDIA_ROOT

video_process = None


def stream_video(request, room_name):
    return render(request, 'streaming/stream.html', {'room_name': room_name})


def create_room(request):
    return render(request, 'streaming/create_room.html')


def capture_video(request):
    # Generate a unique filename for the video
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"video_{timestamp}.mp4"

    # Run FFmpeg command to capture video from webcam and save it to a file
    command = [
        'ffmpeg', '-f', 'v4l2', '-i', '/dev/video0', '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast',
        video_filename
    ]

    # Start the FFmpeg process with the given command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()

    # Check if the video file was created successfully
    if process.returncode == 0:
        # Move the saved video file to a desired location
        destination_path = os.path.join('media', video_filename)
        shutil.move(video_filename, destination_path)

        # Read the saved video file
        with open(destination_path, 'rb') as video_file:
            video_data = video_file.read()

        # Set the response content type as video/mp4
        response = HttpResponse(video_data, content_type='video/mp4')
        response['Content-Length'] = len(video_data)

        return response
    else:
        # If there was an error while capturing the video, return an error response
        error_message = process.stderr.read()


#         return HttpResponse(f'Error capturing video: {error_message}', status=500)


def start_video_capture(request):
    global video_process
    if video_process is None:
        # Run FFmpeg command to capture video from webcam and save it to a file
        command = [
            'ffmpeg', '-f', 'v4l2', '-i', '/dev/video0', '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset',
            'ultrafast', 'output_video.mp4'
        ]

        # Start the FFmpeg process with the given command
        video_process = subprocess.Popen(command)

    return HttpResponse(status=200)


def stop_video_capture(request):
    global video_process
    if video_process is not None:
        # Terminate the FFmpeg process
        video_process.terminate()
        video_process = None

    return HttpResponse(status=200)

# def capture_video(request):
#     rtmp_server_url = 'rtmp://your-media-server-url'
#     rtmp_stream_key = 'your-stream-key'
#     rtmp_client = pyrtmp.Rtmp(rtmp_server_url)
#     rtmp_client.connect()
#     rtmp_client.publish(rtmp_stream_key)
#
#     # Generate a unique filename for the video
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     video_filename = f"video_{timestamp}.mp4"
#
#     # Run FFmpeg command to capture video from webcam and save it to a file
#     command = [
#         'ffmpeg', '-f', 'v4l2', '-i', '/dev/video0', '-vf', 'format=yuv420p', '-c:v', 'libx264', '-preset', 'ultrafast',
#         '-f', 'flv', f'{rtmp_server_url}/{rtmp_stream_key}'
#     ]
#
#     # Start the FFmpeg process with the given command
#     process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     process.wait()
#
#     # Check if the video file was created successfully
#     if process.returncode == 0:
#         # Move the saved video file to a desired location
#         destination_path = os.path.join('media', video_filename)
#         shutil.move(video_filename, destination_path)
#
#         # Read the saved video file
#         with open(destination_path, 'rb') as video_file:
#             video_data = video_file.read()
#
#         # Set the response content type as video/mp4
#         response = HttpResponse(video_data, content_type='video/mp4')
#         response['Content-Length'] = len(video_data)
#
#         return response
#     else:
#         # If there was an error while capturing the video, return an error response
#         error_message = process.stderr.read()
#         return HttpResponse(f'Error capturing video: {error_message}', status=500)
