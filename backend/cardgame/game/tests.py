from django.test import TestCase

from .game_manager import GameManager
from .room_manager import RoomManager

class GameManagerTests(TestCase):

    def create_full_game(self):
        """
        Create a GameManager with four players and a dealt game.
        """
        game = GameManager()

        for i in range(1, 5):
            game.add_player(f"token-{i}")

        return game

    # ---------------------------------------------------------
    # Commit 1: Game rules and state
    # ---------------------------------------------------------

    def test_game_starts_with_four_players(self):
        game = self.create_full_game()

        self.assertEqual(len(game.players), 4)
        self.assertTrue(game.started)
        self.assertIsNotNone(game.current_turn)

    def test_player_with_7h_gets_first_turn(self):
        game = self.create_full_game()

        player_with_7h = None

        for player, hand in game.hands.items():
            if "7H" in hand:
                player_with_7h = player
                break

        self.assertIsNotNone(player_with_7h)
        self.assertEqual(game.current_turn, player_with_7h)

    def test_first_move_must_be_7h(self):
        game = self.create_full_game()

        player = game.current_turn

        # Make sure this player has 7H and another seven.
        game.hands[player] = ["7H", "7S"]

        # Trying another seven must fail.
        result = game.play_card(player, "7S")

        self.assertFalse(result)

        # Nothing should have changed.
        self.assertIsNone(game.piles["spades"]["low"])
        self.assertIn("7S", game.hands[player])
        self.assertEqual(game.current_turn, player)

    def test_first_turn_cannot_pass(self):
        game = self.create_full_game()

        player = game.current_turn

        result = game.pass_turn(player)

        self.assertFalse(result)

        # Turn must remain unchanged.
        self.assertEqual(game.current_turn, player)

    def test_7h_can_be_played_as_first_move(self):
        game = self.create_full_game()

        player = game.current_turn

        # Ensure the current player has 7H.
        game.hands[player] = ["7H"]

        result = game.play_card(player, "7H")

        self.assertTrue(result)

        self.assertEqual(game.piles["hearts"]["low"], 7)
        self.assertEqual(game.piles["hearts"]["high"], 7)

    def test_wrong_player_cannot_play(self):
        game = self.create_full_game()

        current_player = game.current_turn

        other_player = next(
            player for player in game.players
            if player != current_player
        )

        game.hands[other_player] = ["7H"]

        result = game.play_card(other_player, "7H")

        self.assertFalse(result)
        self.assertIsNone(game.piles["hearts"]["low"])
        self.assertEqual(game.current_turn, current_player)

    def test_invalid_card_is_rejected(self):
        game = self.create_full_game()

        player = game.current_turn

        game.hands[player] = ["7H"]

        result = game.play_card(player, "7S")

        self.assertFalse(result)

        self.assertIsNone(game.piles["spades"]["low"])
        self.assertIn("7H", game.hands[player])

    def test_valid_move_changes_turn(self):
        game = self.create_full_game()

        current_player = game.current_turn

        game.hands[current_player] = ["7H"]

        result = game.play_card(current_player, "7H")

        self.assertTrue(result)

        next_index = (
            game.players.index(current_player) + 1
        ) % len(game.players)

        expected_next_player = game.players[next_index]

        self.assertEqual(game.current_turn, expected_next_player)

    def test_winner_detected(self):
        game = self.create_full_game()

        player = game.current_turn

        game.hands[player] = ["7H"]

        result = game.play_card(player, "7H")

        self.assertTrue(result)
        self.assertEqual(game.winner, player)
        self.assertFalse(game.started)

    def test_disconnect_preserves_player_state(self):
        game = self.create_full_game()

        player = game.players[2]

        original_hand = list(game.hands[player])

        game.remove_player(player)

        self.assertIn(player, game.players)
        self.assertEqual(game.hands[player], original_hand)
        self.assertFalse(game.connected[player])

    def test_connected_players_are_tracked(self):
        game = GameManager()

        player1 = game.add_player("token-1")
        player2 = game.add_player("token-2")

        self.assertTrue(game.connected[player1])
        self.assertTrue(game.connected[player2])

        game.remove_player(player1)

        self.assertFalse(game.connected[player1])
        self.assertTrue(game.connected[player2])

    # ---------------------------------------------------------
    # Commit 2: Persistent player identity / reconnection
    # ---------------------------------------------------------

    def test_new_token_gets_new_player(self):
        game = GameManager()

        player = game.add_player("token-123")

        self.assertEqual(player, "Player 1")
        self.assertEqual(
            game.player_tokens["Player 1"],
            "token-123"
        )
        self.assertTrue(game.connected["Player 1"])

    def test_same_token_returns_same_player(self):
        game = GameManager()

        player1 = game.add_player("token-123")

        game.remove_player(player1)

        player2 = game.add_player("token-123")

        self.assertEqual(player1, player2)
        self.assertEqual(player2, "Player 1")
        self.assertTrue(game.connected["Player 1"])

    def test_reconnect_does_not_create_extra_player(self):
        game = GameManager()

        player = game.add_player("token-123")
        game.remove_player(player)

        reconnected_player = game.add_player("token-123")

        self.assertEqual(len(game.players), 1)
        self.assertEqual(reconnected_player, player)

    def test_reconnect_does_not_redeal_cards(self):
        game = self.create_full_game()

        player = game.players[2]

        original_hand = list(game.hands[player])
        original_turn = game.current_turn

        game.remove_player(player)

        reconnected_player = game.add_player(
            game.player_tokens[player]
        )

        self.assertEqual(reconnected_player, player)
        self.assertEqual(game.hands[player], original_hand)
        self.assertEqual(game.current_turn, original_turn)

    def test_reconnecting_existing_player_is_allowed_after_game_started(self):
        game = self.create_full_game()

        player = game.players[2]
        token = game.player_tokens[player]

        game.remove_player(player)

        self.assertTrue(game.started)
        self.assertFalse(game.connected[player])

        reconnected_player = game.add_player(token)

        self.assertEqual(reconnected_player, player)
        self.assertTrue(game.connected[player])
        self.assertTrue(game.started)

    def test_new_player_cannot_join_started_game(self):
        game = self.create_full_game()

        new_player = game.add_player("new-token")

        self.assertIsNone(new_player)
        self.assertEqual(len(game.players), 4)

    def test_new_player_cannot_take_disconnected_players_slot(self):
        game = self.create_full_game()

        disconnected_player = game.players[2]

        game.remove_player(disconnected_player)

        new_player = game.add_player("new-token")

        self.assertIsNone(new_player)

        self.assertIn(disconnected_player, game.players)
        self.assertFalse(game.connected[disconnected_player])

    def test_get_player_by_token(self):
        game = GameManager()

        player = game.add_player("token-123")

        self.assertEqual(
            game.get_player_by_token("token-123"),
            player
        )

        self.assertIsNone(
            game.get_player_by_token("unknown-token")
        )
        
    # ---------------------------------------------------------
    # Commit 4: Disconnect Handling and Game Lifecycle
    # ---------------------------------------------------------
    
    def test_disconnected_current_player_pauses_game(self):
        game = self.create_full_game()

        current_player = game.current_turn

        game.remove_player(current_player)

        result = game.check_for_disconnected_turn()

        self.assertTrue(result)
        self.assertTrue(game.paused)
        self.assertEqual(
            game.disconnected_player,
            current_player
        )

    def test_disconnected_non_current_player_does_not_pause_game(self):
        game = self.create_full_game()

        current_player = game.current_turn

        other_player = next(
            player for player in game.players
            if player != current_player
        )

        game.remove_player(other_player)

        result = game.check_for_disconnected_turn()

        self.assertFalse(result)
        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)

    def test_game_pauses_when_turn_reaches_disconnected_player(self):
        game = self.create_full_game()

        current_player = game.current_turn

        next_index = (
            game.players.index(current_player) + 1
        ) % len(game.players)

        next_player = game.players[next_index]

        game.remove_player(next_player)

        # Keep an extra card so the current player does not win.
        game.hands[current_player] = ["7H", "8H"]

        result = game.play_card(
            current_player,
            "7H"
        )

        self.assertTrue(result)
        self.assertEqual(
            game.current_turn,
            next_player
        )

        self.assertTrue(game.paused)
        self.assertEqual(
            game.disconnected_player,
            next_player
        )

    def test_game_pauses_after_multiple_turns_when_player_is_disconnected(self):
        game = self.create_full_game()

        p1 = game.current_turn

        p2_index = (
            game.players.index(p1) + 1
        ) % len(game.players)

        p2 = game.players[p2_index]

        p3_index = (
            game.players.index(p2) + 1
        ) % len(game.players)

        p3 = game.players[p3_index]

        # P3 disconnects while it is P1's turn.
        game.remove_player(p3)

        # P1 must not win after playing 7H.
        game.hands[p1] = ["7H", "8H"]

        result = game.play_card(p1, "7H")

        self.assertTrue(result)
        self.assertEqual(game.current_turn, p2)
        self.assertFalse(game.paused)

        # P2 must also not win.
        game.hands[p2] = ["7S", "8S"]

        result = game.play_card(p2, "7S")

        self.assertTrue(result)
        self.assertEqual(game.current_turn, p3)

        # P3 is disconnected, so the game must now pause.
        self.assertTrue(game.paused)
        self.assertEqual(
            game.disconnected_player,
            p3
        )

    def test_reconnecting_blocking_player_can_resume_game(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        result = game.add_player(
            game.player_tokens[player]
        )

        self.assertEqual(result, player)
        self.assertTrue(game.connected[player])

        resumed = game.resume_after_reconnect(player)

        self.assertTrue(resumed)
        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)
        self.assertFalse(
            game.disconnect_timeout_expired
        )

    def test_non_blocking_reconnect_does_not_resume_game(self):
        game = self.create_full_game()

        current_player = game.current_turn

        other_player = next(
            player for player in game.players
            if player != current_player
        )

        game.remove_player(other_player)

        result = game.add_player(
            game.player_tokens[other_player]
        )

        self.assertEqual(result, other_player)
        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)

    def test_paused_game_rejects_play(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        game.hands[player] = ["7H"]

        result = game.play_card(player, "7H")

        self.assertFalse(result)

    def test_paused_game_rejects_pass(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        result = game.pass_turn(player)

        self.assertFalse(result)
        
    def test_check_for_disconnected_turn_sets_timeout_flag_false(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)

        result = game.check_for_disconnected_turn()

        self.assertTrue(result)
        self.assertTrue(game.paused)
        self.assertEqual(
            game.disconnected_player,
            player
        )
        self.assertFalse(
            game.disconnect_timeout_expired
        )


    def test_reconnect_clears_timeout_state(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        game.disconnect_timeout_expired = True

        resumed = game.resume_after_reconnect(player)

        self.assertTrue(resumed)
        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)
        self.assertFalse(
            game.disconnect_timeout_expired
        )


    def test_reset_game_clears_disconnect_state(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        game.disconnect_timeout_expired = True

        game.reset_game()

        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)
        self.assertFalse(
            game.disconnect_timeout_expired
        )
    
    def test_game_cannot_end_before_timeout(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)
        self.assertFalse(game.disconnect_timeout_expired)

        result = game.end_game()

        self.assertFalse(result)
        self.assertTrue(game.paused)
        self.assertTrue(game.started)


    def test_game_can_end_after_timeout(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        game.disconnect_timeout_expired = True

        result = game.end_game()

        self.assertTrue(result)
        self.assertFalse(game.started)
        self.assertFalse(game.paused)
        self.assertTrue(game.game_ended)
        self.assertIsNone(game.disconnected_player)


    def test_reset_game_clears_game_ended_state(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        game.disconnect_timeout_expired = True
        game.end_game()

        self.assertTrue(game.game_ended)

        game.reset_game()

        self.assertFalse(game.game_ended)
        self.assertTrue(game.started)
        self.assertFalse(game.paused)
        self.assertIsNone(game.disconnected_player)
        self.assertFalse(
            game.disconnect_timeout_expired
        )
        
    def test_timeout_removes_disconnected_player(self):
        game = self.create_full_game()

        player = game.current_turn

        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        result = game.handle_disconnect_timeout()

        self.assertTrue(result)

        self.assertNotIn(player, game.players)
        self.assertNotIn(player, game.connected)
        self.assertNotIn(player, game.player_tokens)
        self.assertNotIn(player, game.hands)

        self.assertTrue(game.disconnect_timeout_expired)
        self.assertTrue(game.paused)
        self.assertEqual(
            game.disconnected_player,
            player
        )
        
    def test_timed_out_player_cannot_reconnect_until_game_ends(self):
        game = self.create_full_game()

        player = game.current_turn
        token = game.player_tokens[player]

        game.remove_player(player)
        game.check_for_disconnected_turn()

        game.handle_disconnect_timeout()

        # The player has been removed from the current game.
        self.assertNotIn(player, game.players)
        self.assertNotIn(player, game.player_tokens)

        # Game is still active/paused, so they cannot rejoin yet.
        result = game.add_player(token)

        self.assertIsNone(result)

        # End the game.
        game.end_game()

        # Now they can join the room again.
        result = game.add_player(token)

        self.assertIsNotNone(result)
        
    def test_final_scores_are_preserved_after_player_leaves(self):
        game = self.create_full_game()

        scores_before = game.get_scores()

        game.winner = game.players[0]
        game.started = False
        game.final_scores = game.get_scores()

        player = game.players[3]

        game.players.remove(player)
        game.connected.pop(player, None)
        game.player_tokens.pop(player, None)
        game.hands.pop(player, None)

        scores_after = game.get_scores()

        self.assertEqual(
            scores_after,
            scores_before
        )
        
    def test_timed_out_player_can_rejoin_ended_game_without_starting_it(self):
        game = self.create_full_game()

        player = game.current_turn
        token = game.player_tokens[player]

        # Disconnect and time out the current player.
        game.remove_player(player)
        game.check_for_disconnected_turn()

        self.assertTrue(game.paused)

        game.handle_disconnect_timeout()

        # End the game.
        game.disconnect_timeout_expired = True
        result = game.end_game()

        self.assertTrue(result)
        self.assertTrue(game.game_ended)
        self.assertFalse(game.started)

        # Timed-out player rejoins the room.
        result = game.add_player(token)

        self.assertIsNotNone(result)

        # Rejoining as the fourth player must NOT
        # automatically start another game.
        self.assertFalse(game.started)
        self.assertTrue(game.game_ended)
        self.assertEqual(len(game.players), 4)
        
        
# ---------------------------------------------------------
# Commit 3: Multiple Player Rooms (RoomManager)
# ---------------------------------------------------------
    
class RoomManagerTests(TestCase):

    def test_create_room_assigns_host(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")

        self.assertIsNotNone(room)
        self.assertEqual(len(room.room_id), 6)
        self.assertEqual(room.host_token, "host-token")
        self.assertEqual(room.host_player, "Player 1")

        self.assertIs(
            rooms.get_room(room.room_id),
            room
        )

    def test_room_has_separate_game_manager(self):
        rooms = RoomManager()

        room1 = rooms.create_room("token-1")
        room2 = rooms.create_room("token-2")

        self.assertIsNot(
            room1.game_manager,
            room2.game_manager
        )

    def test_players_in_different_rooms_are_independent(self):
        rooms = RoomManager()

        room1 = rooms.create_room("host-1")
        room2 = rooms.create_room("host-2")

        room1, player1 = rooms.join_room(
            room1.room_id,
            "token-2"
        )

        room2, player2 = rooms.join_room(
            room2.room_id,
            "token-3"
        )

        self.assertEqual(player1, "Player 2")
        self.assertEqual(player2, "Player 2")

        self.assertEqual(
            len(room1.game_manager.players),
            2
        )

        self.assertEqual(
            len(room2.game_manager.players),
            2
        )

    def test_join_nonexistent_room_fails(self):
        rooms = RoomManager()

        room, player = rooms.join_room(
            "ABC123",
            "token-1"
        )

        self.assertIsNone(room)
        self.assertIsNone(player)

    def test_fifth_player_cannot_join_room(self):
        rooms = RoomManager()

        room = rooms.create_room("token-1")

        rooms.join_room(room.room_id, "token-2")
        rooms.join_room(room.room_id, "token-3")
        rooms.join_room(room.room_id, "token-4")

        joined_room, player = rooms.join_room(
            room.room_id,
            "token-5"
        )

        self.assertIsNone(joined_room)
        self.assertIsNone(player)

        self.assertEqual(
            len(room.game_manager.players),
            4
        )

    def test_same_token_reconnects_to_same_room(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")

        room, player = rooms.join_room(
            room.room_id,
            "token-2"
        )

        room.game_manager.remove_player(player)

        joined_room, reconnected_player = rooms.join_room(
            room.room_id,
            "token-2"
        )

        self.assertIs(joined_room, room)
        self.assertEqual(reconnected_player, player)
        self.assertTrue(room.game_manager.connected[player])

    def test_get_room_for_token(self):
        rooms = RoomManager()

        room1 = rooms.create_room("host-token")
        room2 = rooms.create_room("other-host")

        rooms.join_room(room2.room_id, "target-token")

        found_room = rooms.get_room_for_token(
            "target-token"
        )

        self.assertIs(found_room, room2)

        self.assertIsNone(
            rooms.get_room_for_token("unknown-token")
        )

    def test_group_names_are_unique(self):
        rooms = RoomManager()

        room1 = rooms.create_room("token-1")
        room2 = rooms.create_room("token-2")

        self.assertNotEqual(
            room1.group_name,
            room2.group_name
        )

        self.assertEqual(
            room1.group_name,
            f"game_room_{room1.room_id}"
        )
        
    def test_host_reassigned_when_host_leaves(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")

        rooms.join_room(room.room_id, "token-2")
        rooms.join_room(room.room_id, "token-3")

        remaining_room = rooms.leave_room(
            room.room_id,
            "host-token"
        )

        self.assertIs(remaining_room, room)

        self.assertEqual(
            room.host_player,
            "Player 2"
        )

        self.assertEqual(
            room.host_token,
            "token-2"
        )

        self.assertNotIn(
            "Player 1",
            room.game_manager.players
        )

    def test_last_player_leaving_deletes_room(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")

        room_id = room.room_id

        result = rooms.leave_room(
            room_id,
            "host-token"
        )

        self.assertIsNone(result)
        self.assertIsNone(rooms.get_room(room_id))

    def test_non_host_leaving_does_not_change_host(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")

        rooms.join_room(room.room_id, "token-2")

        result = rooms.leave_room(
            room.room_id,
            "token-2"
        )

        self.assertIs(result, room)

        self.assertEqual(
            room.host_player,
            "Player 1"
        )

        self.assertEqual(
            room.host_token,
            "host-token"
        )

    def test_leaving_player_is_removed_from_room_state(self):
        rooms = RoomManager()

        room = rooms.create_room("host-token")
        rooms.join_room(room.room_id, "token-2")

        player = "Player 2"

        result = rooms.leave_room(
            room.room_id,
            "token-2"
        )

        self.assertIs(result, room)

        self.assertNotIn(
            player,
            room.game_manager.players
        )

        self.assertNotIn(
            player,
            room.game_manager.connected
        )

        self.assertNotIn(
            player,
            room.game_manager.player_tokens
        )

        self.assertNotIn(
            player,
            room.game_manager.hands
        )
        
    def test_room_groups_are_isolated(self):
        rooms = RoomManager()

        room1 = rooms.create_room("host-1")
        room2 = rooms.create_room("host-2")

        self.assertNotEqual(
            room1.group_name,
            room2.group_name
        )

    def test_room_game_state_is_isolated(self):
        rooms = RoomManager()

        room1 = rooms.create_room("host-1")
        room2 = rooms.create_room("host-2")

        room1_manager = room1.game_manager
        room2_manager = room2.game_manager

        room1_manager.hands["Player 1"] = ["7H"]
        room2_manager.hands["Player 1"] = ["7S"]

        self.assertEqual(
            room1_manager.hands["Player 1"],
            ["7H"]
        )

        self.assertEqual(
            room2_manager.hands["Player 1"],
            ["7S"]
        )