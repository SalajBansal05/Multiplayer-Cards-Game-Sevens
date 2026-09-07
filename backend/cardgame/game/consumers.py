from channels.generic.websocket import AsyncWebsocketConsumer
import json

from .room_manager import room_manager
from urllib.parse import parse_qs

import asyncio

class GameConsumer(AsyncWebsocketConsumer):
    
    async def start_disconnect_timer(self):

        room = self.game_room
        game_manager = room.game_manager

        if not game_manager.paused:
            return

        if room.disconnect_task is not None:
            return

        player_id = game_manager.disconnected_player

        room.disconnect_task = asyncio.create_task(
            self.disconnect_timeout_task(player_id)
        )
        
    async def disconnect_timeout_task(self, player_id):

        try:
            await asyncio.sleep(60)
            
            game_manager = self.game_room.game_manager

            if (game_manager.paused and game_manager.disconnected_player == player_id):

                timed_out = game_manager.handle_disconnect_timeout()

                if timed_out:
                    if self.game_room.host_player == player_id:
                        remaining_players = game_manager.players

                        if remaining_players:
                            new_host = remaining_players[0]

                            self.game_room.host_player = new_host
                            self.game_room.host_token = (
                                game_manager.player_tokens[new_host]
                            )

                    await self.channel_layer.group_send(
                        self.room,
                        {"type": "game_update"}
                    )

        except asyncio.CancelledError:
            pass

        finally:
            self.game_room.disconnect_task = None

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

        game_manager = self.game_room.game_manager

        if game_manager.resume_after_reconnect(self.player_id):

            if self.game_room.disconnect_task is not None:
                self.game_room.disconnect_task.cancel()
                self.game_room.disconnect_task = None

            await self.channel_layer.group_send(
                self.room,
                {"type": "game_update"}
            )

        await self.send_state()

        # If this player completed the room, notify everyone.
        await self.channel_layer.group_send(
            self.room,
            {"type": "game_update"}
        )
        
    async def disconnect(self, close_code):

        if hasattr(self, "player_id"):

            game_manager = self.game_room.game_manager

            if self.player_id in game_manager.players:
                game_manager.remove_player(self.player_id)

                if game_manager.check_for_disconnected_turn():

                    await self.start_disconnect_timer()

                    await self.channel_layer.group_send(
                        self.room,
                        {"type": "game_update"}
                    )

        if hasattr(self, "room"):
            await self.channel_layer.group_discard(
                self.room,
                self.channel_name
            )

    async def receive(self, text_data):

        data = json.loads(text_data)

        game_manager = self.game_room.game_manager
        
        if data["action"] == "start_game":
            if self.player_id != self.game_room.host_player:
                await self.send(text_data=json.dumps({
                    "error": "Only the host can start the game."
                }))
                return

            if game_manager.start_game():
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )
            else:
                await self.send(text_data=json.dumps({
                    "error": "Game cannot be started. At least 2 players must be ready."
                }))

        if data["action"] == "play_card":
            card = data["card"]

            if game_manager.play_card(
                self.player_id,
                card
            ):
                if game_manager.paused:
                    await self.start_disconnect_timer()

                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

        if data["action"] == "pass":

            if game_manager.pass_turn(
                self.player_id
            ):
                if game_manager.paused:
                    await self.start_disconnect_timer()

                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

        if data["action"] == "rematch":
            if game_manager.play_again(self.player_id):
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )
            else:
                await self.send(text_data=json.dumps({
                    "error": "You cannot choose Play Again right now."
                }))
            
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

            # This client is leaving, so remove its channel
            # before broadcasting the update.
            await self.channel_layer.group_discard(
                self.room,
                self.channel_name
            )

            # Notify only the players who remain in the room.
            if room is not None:
                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

            await self.close()
            return
        
        if data["action"] == "end_game":

            game_manager = self.game_room.game_manager

            if self.player_id != self.game_room.host_player:
                await self.send(
                    text_data=json.dumps({
                        "error": "Only the host can end the game."
                    })
                )
                return

            if game_manager.end_game():

                await self.channel_layer.group_send(
                    self.room,
                    {"type": "game_update"}
                )

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
                "game_ended": game_manager.game_ended,
                "piles": game_manager.piles,
                "hand": game_manager.hands.get(
                    self.player_id,
                    []
                ),
                "turn": game_manager.current_turn,
                "player": self.player_id,
                "players": game_manager.players,
                "players_playing_again": list(game_manager.players_playing_again),
                "counts": counts,
                "scores": scores,
                "winner": game_manager.winner,
                "paused": game_manager.paused,
                "disconnected_player": game_manager.disconnected_player,
                "disconnect_timeout_expired": game_manager.disconnect_timeout_expired,
            })
        )