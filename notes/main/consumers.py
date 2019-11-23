import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Notes


class NotesConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        self.user = f'{self.scope["user"]}'
        await self.channel_layer.group_add(
            self.user,
            self.channel_name
        )

        await self.send({
            'type': 'websocket.accept',
        })

    async def websocket_receive(self, event):
        data = json.loads(event.get('text'))
        response_data = {}
        if data.get('type') == 'add':
            obj_id = await self.save_note(self.scope['user'], data.get('text'))
            response_data.update({"type": "add",
                                  "text": data.get("text"),
                                  "id": obj_id})
        elif data.get('type') == 'delete':
            await self.delete_note(data.get("id"))
            response_data.update({"type": "delete",
                                  'id': data.get('id')})
        await self.channel_layer.group_send(
            self.user,
            {
                "type": "note",
                "text": json.dumps(response_data)
            }
        )

    async def note(self, event):
        await self.send(
            {
                "type": "websocket.send",
                "text": event['text']
            }
        )

    @database_sync_to_async
    def save_note(self, user, note_text):
        obj = Notes.objects.create(user=str(user), note=note_text)
        obj.save()
        return obj.id

    @database_sync_to_async
    def delete_note(self, pk):
        Notes.objects.get(id=pk).delete()

    async def websocket_disconnect(self, event):
        print('disconnected', event)