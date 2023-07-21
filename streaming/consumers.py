from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime


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

    async def receive(self, text_data=None, bytes_data=None):
        if text_data:
            # Log or print the received video frame
            print('Received video frame:', text_data)

            # Generate timestamp for the current frame
            timestamp = datetime.now().isoformat()


            # Broadcast received video frames to all connected clients
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_frame',
                    'data': {
                        'timestamp': timestamp,
                        'frame': text_data,
                        'frame_counter': self.frame_counter,
                    },
                }
            )
            self.frame_counter += 1

        elif bytes_data:
            # Handle received video frames
            pass

    async def video_frame(self, event):
        # Get the video frame data from the event
        frame_data = event['data']

        # Process and handle the video frames here
        # Example: you can save the frames to a file, perform real-time analysis, etc.
        timestamp = frame_data['timestamp']
        frame = frame_data['frame']
        frame_counter = frame_data['frame_counter']

        # Print the video frame details
        print('Received video frame at', timestamp)
        print('Frame Counter:', frame_counter)

    @property
    def connection_groups(self):
        # Assign a unique group name to each consumer based on the room name
        return [self.room_group_name]
