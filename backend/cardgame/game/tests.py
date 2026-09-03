from django.test import TestCase

from .game_manager import GameManager


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