from .deck import deal_cards

class GameState:
    def __init__(self):
        self.players = []
        self.hands = {}
        self.piles = {
            "hearts": {"low": None, "high": None},
            "spades": {"low": None, "high": None},
            "diamonds": {"low": None, "high": None},
            "clubs": {"low": None, "high": None},
        }
        self.current_turn = None
        self.started = False

game_state = GameState()