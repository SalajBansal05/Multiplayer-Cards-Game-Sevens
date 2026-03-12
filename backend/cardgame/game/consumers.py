from channels.generic.websocket import AsyncWebsocketConsumer
import json

from .game_manager import game_manager


class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room = "game_room"

        await self.channel_layer.group_add(
            self.room,
            self.channel_name
        )

        await self.accept()

        self.player_id = game_manager.add_player()

        await self.send_state()

        # if game just started send update to everyone
        if len(game_manager.players) == 4:

            await self.channel_layer.group_send(
                self.room,
                {"type": "game_update"}
            )

    async def disconnect(self, close_code):

        game_manager.remove_player(self.player_id)

        await self.channel_layer.group_discard(
            self.room,
            self.channel_name
        )

    async def receive(self, text_data):

        data = json.loads(text_data)

        if data["action"] == "play_card":

            card = data["card"]

            if game_manager.play_card(self.player_id, card):

                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

        if data["action"] == "pass":

            if game_manager.pass_turn(self.player_id):

                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

    async def game_update(self, event):

        await self.send_state()

    async def send_state(self):
        counts = {p: len(h) for p, h in game_manager.hands.items()}

        await self.send(
            text_data=json.dumps({
                "piles": game_manager.piles,
                "hand": game_manager.hands.get(self.player_id, []),
                "turn": game_manager.current_turn,
                "player": self.player_id,
                "players": game_manager.players,
                "counts": counts
            })
        )