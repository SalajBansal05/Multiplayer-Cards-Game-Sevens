from channels.generic.websocket import AsyncWebsocketConsumer
import json

from .game_manager import game_manager
from urllib.parse import parse_qs

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.room = "game_room"

        query_params = parse_qs(
            self.scope["query_string"].decode()
        )
        token = query_params.get("token", [None])[0]
        if token is None:
            await self.accept()

            await self.send(
                text_data=json.dumps({
                    "error": "Player identity is missing."
                })
            )

            await self.close()
            return

        self.player_id = game_manager.add_player(token)
        if self.player_id is None:
            await self.accept()

            await self.send(
                text_data=json.dumps({
                    "error": "Game is full or already in progress."
                })
            )

            await self.close()
            return

        await self.channel_layer.group_add(
            self.room,
            self.channel_name
        )
        await self.accept()
        await self.send_state()

        if len(game_manager.players) == 4:
            await self.channel_layer.group_send(
                self.room,
                {"type": "game_update"}
            )

    async def disconnect(self, close_code):

        if hasattr(self, "player_id"):
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
        
        if data["action"] == "rematch":
            game_manager.reset_game()

            await self.channel_layer.group_send(
                self.room,
                {"type": "game_update"}
            )

    async def game_update(self, event):

        await self.send_state()

    async def send_state(self):
        counts = {p: len(h) for p, h in game_manager.hands.items()}
        scores = game_manager.get_scores()
        
        await self.send(
            text_data=json.dumps({
                "piles": game_manager.piles,
                "hand": game_manager.hands.get(self.player_id, []),
                "turn": game_manager.current_turn,
                "player": self.player_id,
                "players": game_manager.players,
                "counts": counts,
                "scores": scores,
                "winner": game_manager.winner
            })
        )