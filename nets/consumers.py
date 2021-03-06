# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.contrib.auth.models import User
from .models import Message, Net
import datetime
from django.utils.html import urlize
from django.template.defaultfilters import linebreaksbr

import time

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.net_name = self.scope['url_route']['kwargs']['net_id']
        self.net_group_name = 'chat_%s' % self.net_name

        # Join net group
        await self.channel_layer.group_add(
            self.net_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave net group
        await self.channel_layer.group_discard(
            self.net_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):

        data = json.loads(text_data)
        
        if data['command'] == 'delete':

            message_id = data['message_id']

            # Send message to remove message to net group
            await self.channel_layer.group_send(
                self.net_group_name,
                {
                    'type': 'delete',
                    'message_id': message_id
                }
            )

        elif data['command'] == 'typing':
            
            user_id = data['user_id']
            
            # Send message to net group
            await self.channel_layer.group_send(
                self.net_group_name,
                {
                    'type': 'typing',
                    'user_id': user_id
                }
            )
        

        elif data['command'] == 'image':

            user_id = data['user_id']
            message = data['message']
            image_url = data['image_url']
            date_sent = data['date_sent']
            message_id = data['message_id'] 

            # Put in <br> where \n exists for real-time chat
            message=linebreaksbr(message)

            # Urlize message for real-time chat
            message=urlize(message)

            # Send message to net group
            await self.channel_layer.group_send(
                self.net_group_name,
                {
                    'type': 'image_message',
                    'message': message,
                    'message_id': message_id,
                    'user_id': user_id,
                    'image_url': image_url,
                    'date_sent': date_sent
                }
            )

        else:

            user_id = data['user_id']
            net_id = data['net_id']
            message = data['message']

            # Replace <div> and <br> in message with \n
            message=message.replace("<div>","")
            message=message.replace("</div>","")
            message=message.replace("<br>", "\n")

            # Save to database and get message id
            message_id = await self.save_message(net_id, user_id, message)

            # Put in <br> where \n exists for real-time chat
            message=linebreaksbr(message)

            # Urlize message for real-time chat
            message=urlize(message)

            # Send message to net group
            await self.channel_layer.group_send(
                self.net_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'user_id': user_id,
                    'message_id': message_id
                }
            )


    # Receive who is typing from net group
    async def typing(self, event):

        user_id = event['user_id']

        await self.send(text_data=json.dumps({
            'typing': 'True',
            'user_id': user_id

        }))

    # Receive message to delete from net group
    async def delete(self, event):

        message_id = event['message_id']

        await self.send(text_data=json.dumps({
            'delete': 'True',
            'message_id': message_id

        }))

    # Receive message from net group
    async def chat_message(self, event):

        message = event['message']
        user_id = event['user_id']
        message_id = event['message_id']

        #Get username and profile pic url
        user_info = await self.get_user_info(user_id)

        username = user_info[0]
        user_image = user_info[1]

        # Get date
        date = datetime.datetime.now()

        # Month
        date_sent = date.strftime("%B ")

        # Day + Year
        day_year = date.strftime("%d, %Y, ")

        if day_year[0] == "0":
            day_year = day_year[1:]
            
        date_sent += day_year

        # Hour
        hour = date.strftime("%H:%M")
        if hour[0] == "0":
            hour = hour[1:]
        date_sent += hour + ' '
        
        # AM/PM  
        date_sent += date.strftime('%p').lower().replace("", ".")[1:]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'message_id':message_id,
            'date_sent': date_sent,
            'username': username,
            'user_image': user_image
        }))

    # Receive image message from net group
    async def image_message(self, event):

        message = event['message']
        user_id = event['user_id']
        message_id = event['message_id']

        #Get username and profile pic url
        user_info = await self.get_user_info(user_id)

        username = user_info[0]
        user_image = user_info[1]

        image_url = event['image_url']
        date_sent = event['date_sent']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'date_sent': date_sent,
            'username': username,
            'user_image': user_image,
            'image_url': image_url,
            'message_id': message_id
        }))


    @database_sync_to_async
    def get_user_info(self, user_id):
        user_id = int(user_id)
        username = User.objects.get(id=user_id).username
        image_url = User.objects.get(id=user_id).profile.image.url

        return (username, image_url)

    @database_sync_to_async
    def save_message(self, net_id, user_id, message):

        message = Message(net= Net.objects.get(id=net_id),
                          author = User.objects.get(id=user_id),
                          date_sent = datetime.datetime.now(),
                          content = message, 
                          )

        message.save()

        return message.id



