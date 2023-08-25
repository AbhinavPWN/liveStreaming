import os
from datetime import datetime
from uuid import uuid4
import ffmpeg
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse, HttpResponseBadRequest
from django.shortcuts import render
import subprocess

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# import signal

video_process = None
global_process = None


def homepage(request):
    # Check if the session ID already exists in the user's session
    session_id = request.session.get('session_id')

    # If not, generate a new session ID and store it in the user's session
    if not session_id:
        session_id = str(uuid4())  # Generate a unique UUID as the session ID
        request.session['session_id'] = session_id

    return render(request, 'streaming/homepage.html', {'session_id': session_id})


def session_page(request):
    return render(request, 'streaming/session.html')


def stream_video(request, room_name):
    # Check if the session ID already exists in the user's session
    session_id = request.session.get('session_id')

    # If not, generate a new session ID and store it in the user's session
    if not session_id:
        session_id = str(uuid4())  # Generate a unique UUID as the session ID
        request.session['session_id'] = session_id

    return render(request, 'streaming/stream.html', {'room_name': room_name, 'session_id': session_id})


def create_room(request):
    return render(request, 'streaming/create_room.html')


def start_rtmp_stream(request):
    if request.method == 'POST':
        # Get the session ID or user token from the client-side request
        session_id = request.POST.get('session_id')  # Adjust this based on your frontend data

        # Get the room name dynamically from the URL
        room_name = request.POST.get('room_name')  # Assuming you pass the 'room_name' in the request

        if not room_name:
            return JsonResponse({'error': 'Room name is missing.'}, status=400)

        rtmp_url = f'rtmp://localhost/live/{room_name}?session={session_id}'

        try:
            (
                ffmpeg.input('video="OBS Virtual Camera"', format='dshow', framerate=30)
                .output(rtmp_url, 'pipe: ', format='flv', rtbufsize='256M')
                # .run_async(pipe_stdin=True)
                .run_async(pipe_stdout=True, pipe_stderr=True)
            )

            return JsonResponse({'message': 'RTMP stream started successfully'})
        except ImportError:
            return JsonResponse(
                {'error': 'ffmpeg is not installed. Install ffmpeg-python using "pip install ffmpeg-python".'})
        except Exception as e:
            return JsonResponse({'error': f'Error starting RTMP stream: {str(e)}'})
    else:
        return JsonResponse({'error': 'This endpoint only accepts POST requests'}, status=400)


# Separate view function for WebSocket connection to the consumer
def initiate_websocket(request, room_name):
    # Create a WebSocket connection to the consumer
    channel_layer = get_channel_layer()
    session_id = request.POST.get('session_id')  # Assuming you pass the 'session_id' in the request

    async_to_sync(channel_layer.group_send)(
        f'video_group_{room_name}',  # Replace 'room_name' with your desired room name
        {
            'type': 'video_frame',
            'data': {
                'session_id': session_id,
            }
        }
    )

    return JsonResponse({'message': 'WebSocket connection established.'})


def capture_video(request):
    def generate_video():
        # Run FFmpeg command to capture video from webcam and yield the output
        ffmpeg_command = (
            # ffmpeg.input('video=Integrated Camera', format='dshow', framerate=30)
            ffmpeg.input('video="OBS Virtual Camera"', format='dshow', framerate=30)
            .output('pipe:', format='mp4', vcodec='libx264', preset='ultrafast', vf='format=yuv420p', rtbufsize='256M')
            .run_async(pipe_stdout=True)
        )
        for chunk in ffmpeg_command.stdout.iter_content(chunk_size=4096):
            yield chunk

    response = StreamingHttpResponse(generate_video(), content_type='video/mp4')
    response['Content-Disposition'] = 'attachment; filename="captured_video.mp4"'
    return response


def start_video_capture(request):
    global video_process
    if video_process is None:
        output_path = 'output_video.mp4'
        # Run FFmpeg command to capture video from webcam and save it to a file
        video_process = (
            ffmpeg.input('video="OBS Virtual Camera"', format='dshow', framerate=30, )
            .output(output_path, format='mp4', vcodec='libx264', preset='ultrafast', vf='fps=30', rtbufsize='256M')
            .run_async(pipe_stdin=True)
        )

        return HttpResponse(status=200)

    return HttpResponse("Video capture is already running.", status=400)


def get_video_process(request, session_id):
    # Get the session dictionary from the session store
    session_dict = request.session.get('session', {})

    # Get the FFmpeg process from the session dictionary
    video_process_name = session_dict.get('video_process', None)

    return video_process_name


@csrf_exempt
@require_POST
def stop_video_capture(request):
    # Check if the request is a POST request
    if request.method != 'POST':
        return HttpResponseBadRequest('Only POST requests are allowed.')

    # Check if the request contains the session_id parameter
    if 'session_id' not in request.POST:
        return HttpResponseBadRequest('The session_id parameter is missing.')

    # Get the session ID from the request
    session_id = request.POST['session_id']

    # Get the FFmpeg process
    local_video_process = get_video_process(session_id)

    # Stop capturing video
    if local_video_process is not None:
        if session_id == local_video_process.session_id:
            local_video_process.communicate(input=b'q')  # Send 'q' to FFmpeg to stop gracefully
            local_video_process = None
            return JsonResponse("Video capture stopped.", status=200)
        else:
            return JsonResponse({'error': 'Video capture is not running for this session.'}, status=400)
    else:
        return JsonResponse({'error': 'Video capture is not running.'}, status=400)


def view_stream(request, room_name):
    return render(request, 'streaming/view_stream.html', {'room_name': room_name})
