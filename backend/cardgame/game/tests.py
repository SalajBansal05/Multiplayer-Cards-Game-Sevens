from django.test import TestCase

from .game_manager import GameManager


class GameManagerTests(TestCase):

    def create_full_game(self):
        """
        Create a GameManager with four players and a dealt game.
        """
        game = GameManager()

        for _ in range(4):
            game.add_player()

        return game

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

        # Still an unopened game.
        self.assertTrue(
            all(pile["low"] is None for pile in game.piles.values())
        )

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

        # The game has not started with any card yet.
        self.assertTrue(
            all(pile["low"] is None for pile in game.piles.values())
        )

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

        # Give the other player a card they could otherwise play.
        game.hands[other_player] = ["7H"]

        result = game.play_card(other_player, "7H")

        self.assertFalse(result)
        self.assertIsNone(game.piles["hearts"]["low"])
        self.assertEqual(game.current_turn, current_player)

    def test_invalid_card_is_rejected(self):
        game = self.create_full_game()

        player = game.current_turn

        # Player does not have this card.
        game.hands[player] = ["7H"]

        result = game.play_card(player, "7S")

        self.assertFalse(result)

        self.assertIsNone(game.piles["spades"]["low"])
        self.assertIn("7H", game.hands[player])

    def test_valid_move_changes_turn(self):
        game = self.create_full_game()

        current_player = game.current_turn

        # Force the opening move.
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

        # If the player has only 7H, playing it should win.
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

        # Player remains part of the game.
        self.assertIn(player, game.players)

        # Their hand is preserved.
        self.assertEqual(game.hands[player], original_hand)

        # Only connection status changes.
        self.assertFalse(game.connected[player])

    def test_connected_players_are_tracked(self):
        game = GameManager()

        player1 = game.add_player()
        player2 = game.add_player()

        self.assertTrue(game.connected[player1])
        self.assertTrue(game.connected[player2])

        game.remove_player(player1)

        self.assertFalse(game.connected[player1])
        self.assertTrue(game.connected[player2])