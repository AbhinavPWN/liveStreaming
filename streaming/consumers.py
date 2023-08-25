import json
import subprocess
import asyncio
import ffmpeg
from channels.generic.websocket import AsyncWebsocketConsumer
import base64


class VideoConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frame_counter = 0

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'video_group_{self.room_name}'

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Terminate the FFmpeg process if it's running
        if hasattr(self, 'ffmpeg_process') and self.ffmpeg_process is not None:
            self.ffmpeg_process.terminate()
            await self.ffmpeg_process.wait()
            self.ffmpeg_process = None

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            try:
                # This method will receive the session ID from the client
                text_data_json = json.loads(text_data)
                session_id = text_data_json['session_id']

                # Start the RTMP streaming process with ffmpeg
                rtmp_url = f'rtmp://localhost/live/stream?session={session_id}'
                ffmpeg_input = (
                    ffmpeg.input('video="OBS Virtual Camera"', format='dshow', video_size='640x480', framerate=30)
                    .output(rtmp_url, 'pipe:', format='flv', rtbufsize='256M')
                    .overwrite_output()
                )

                # Use asyncio.create_subprocess_exec to start the RTMP streaming process
                self.ffmpeg_process = await asyncio.create_subprocess_exec(
                    *ffmpeg_input.compile(pipe=True)
                )

                # Start sending video frames to all connected clients
                asyncio.ensure_future(self.send_video_frames(session_id))

            except Exception as e:
                print('Error: ', e)

    async def send_video_frames(self, session_id):
        packet_size = 4096
        video_input = ffmpeg.input('video="OBS Virtual Camera"', format='dshow', video_size='640x480', framerate=30)
        ffmpeg_process = (
            video_input
            .output('pipe:', format='rawvideo', pix_fmt='rgb24', rtbufsize='256M')
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )

        try:
            for frame_data in ffmpeg_process.stdout.iter_any():
                # Convert the frame data to a FilterableStream object
                frame_data = ffmpeg.input(ffmpeg_process.stdout, format='rawvideo', pix_fmt='rgb24')

                # Send the frame data to all clients in the group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'video_frame',
                        'data': frame_data,
                    }
                )

        finally:
            ffmpeg_process.terminate()
            await ffmpeg_process.wait()

        # # Adjust the sleep duration based on the frame rate of your video source
        # await asyncio.sleep(1 / 30)  # Assuming 30 frames per second

    async def video_frame(self, event):
        # This method will send video frames to all connected clients in the group
        frame_data = event['data']

        # # Send the video frame as text data to the client
        # await self.send(text_data=frame_data)

        # Send the video frame stream as binary data to the client
        async for chunk in frame_data.stdout.iter_any():
            await self.send(bytes_data=chunk)

    async def video_packet(self, event):
        packet_data = event['data']

        # Send the packet data as text data to the client
        await self.send(text_data=packet_data)
