from channels.generic.websocket import AsyncWebsocketConsumer
import json

from .room_manager import room_manager
from urllib.parse import parse_qs

class GameConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        # Get room ID from the WebSocket URL.
        self.room_id = (
            self.scope["url_route"]["kwargs"]["room_id"]
        )

        # Find the requested room.
        self.game_room = room_manager.get_room(
            self.room_id
        )

        if self.game_room is None:
            await self.accept()

            await self.send(
                text_data=json.dumps({
                    "error": "Room not found."
                })
            )

            await self.close()
            return

        self.room = self.game_room.group_name

        # Get persistent player token from the query string.
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

        # Join this room through its GameManager.
        self.player_id = (
            self.game_room.game_manager.add_player(token)
        )

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

        # If this player completed the room, notify everyone.
        if len(self.game_room.game_manager.players) == 4:
            await self.channel_layer.group_send(
                self.room,
                {"type": "game_update"}
            )

    async def disconnect(self, close_code):

        if hasattr(self, "player_id"):
            game_manager = self.game_room.game_manager

            # Only mark as disconnected if the player
            # is still part of the room.
            if self.player_id in game_manager.players:
                game_manager.remove_player(self.player_id)

        if hasattr(self, "room"):
            await self.channel_layer.group_discard(
                self.room,
                self.channel_name
            )

    async def receive(self, text_data):

        data = json.loads(text_data)

        game_manager = self.game_room.game_manager

        if data["action"] == "play_card":
            card = data["card"]

            if game_manager.play_card(
                self.player_id,
                card
            ):
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

        if data["action"] == "pass":

            if game_manager.pass_turn(
                self.player_id
            ):
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
            
        if data["action"] == "leave_room":

            game_manager = self.game_room.game_manager

            # Players cannot explicitly leave during an active game.
            if game_manager.started and game_manager.winner is None:
                await self.send(
                    text_data=json.dumps({
                        "error": "You cannot leave while a game is in progress."
                    })
                )
                return

            room = room_manager.leave_room(
                self.room_id,
                game_manager.player_tokens[self.player_id]
            )

            # Tell the remaining players that the room changed.
            if room is not None:
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

            # This client is no longer part of the room.
            await self.channel_layer.group_discard(
                self.room,
                self.channel_name
            )

            await self.close()
            return

    async def game_update(self, event):
        await self.send_state()

    async def send_state(self):

        game_manager = self.game_room.game_manager

        counts = {
            player: len(hand)
            for player, hand in game_manager.hands.items()
        }

        scores = game_manager.get_scores()

        await self.send(
            text_data=json.dumps({
                "room_id": self.room_id,
                "host": self.game_room.host_player,
                "started": game_manager.started,
                "piles": game_manager.piles,
                "hand": game_manager.hands.get(
                    self.player_id,
                    []
                ),
                "turn": game_manager.current_turn,
                "player": self.player_id,
                "players": game_manager.players,
                "counts": counts,
                "scores": scores,
                "winner": game_manager.winner
            })
        )