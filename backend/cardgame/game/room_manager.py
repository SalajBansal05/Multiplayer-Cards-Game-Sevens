import secrets
import string

from .game_manager import GameManager


class GameRoom:

    def __init__(self, room_id, host_token):
        self.room_id = room_id
        self.host_token = host_token
        self.game_manager = GameManager()

        # The player who creates the room automatically becomes the host.
        self.host_player = self.game_manager.add_player(host_token)

    @property
    def group_name(self):
        return f"game_room_{self.room_id}"


class RoomManager:

    def __init__(self):
        self.rooms = {}

    def _generate_room_id(self):
        """
        Generate a unique 6-character room code.
        """
        characters = string.ascii_uppercase + string.digits

        while True:
            room_id = "".join(
                secrets.choice(characters)
                for _ in range(6)
            )

            if room_id not in self.rooms:
                return room_id

    def create_room(self, host_token):
        """
        Create a new room and assign its creator as the host.
        """
        room_id = self._generate_room_id()

        room = GameRoom(
            room_id=room_id,
            host_token=host_token
        )

        self.rooms[room_id] = room

        return room

    def get_room(self, room_id):
        """
        Return the room with the given ID,
        or None if the room does not exist.
        """
        if room_id is None:
            return None

        return self.rooms.get(room_id.upper())

    def join_room(self, room_id, token):
        """
        Join an existing room using a player token.

        Returns:
            (room, player_id) on success
            (None, None) if the room is invalid, full,
            or the token already belongs to another room.
        """
        room = self.get_room(room_id)

        if room is None:
            return None, None

        existing_room = self.get_room_for_token(token)

        if existing_room is not None and existing_room is not room:
            return None, None

        player_id = room.game_manager.add_player(token)

        if player_id is None:
            return None, None

        return room, player_id

    def get_room_for_token(self, token):
        """
        Find the room to which a player token currently belongs.

        Returns:
            GameRoom if found, otherwise None.
        """
        for room in self.rooms.values():
            if room.game_manager.get_player_by_token(token) is not None:
                return room

        return None
    
    def token_in_any_room(self, token):
        """
        Check whether a player token already belongs to any room.

        Returns:
            GameRoom if the token belongs to a room,
            otherwise None.
        """
        return self.get_room_for_token(token)

    def leave_room(self, room_id, token):
        """
        Explicitly remove a player from a room.

        If the host leaves, another player becomes host.
        If the room becomes empty, it is deleted.

        Returns:
            The remaining room, or None if the room was deleted.
        """
        room = self.get_room(room_id)

        if room is None:
            return None

        player_id = room.game_manager.get_player_by_token(token)

        if player_id is None:
            return room

        # Remove the player completely from this room.
        room.game_manager.players.remove(player_id)
        room.game_manager.connected.pop(player_id, None)
        room.game_manager.player_tokens.pop(player_id, None)
        room.game_manager.hands.pop(player_id, None)

        # If nobody remains, delete the room.
        if len(room.game_manager.players) == 0:
            del self.rooms[room.room_id]
            return None

        # If the host left, assign the first remaining player as host.
        if token == room.host_token:
            new_host = room.game_manager.players[0]
            room.host_player = new_host
            room.host_token = room.game_manager.player_tokens[new_host]

        return room


room_manager = RoomManager()