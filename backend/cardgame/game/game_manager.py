from .deck import deal_cards


class GameManager:

    def __init__(self):

        self.players = []
        self.hands = {}

        self.piles = {
            "hearts": {"low": None, "high": None},
            "spades": {"low": None, "high": None},
            "diamonds": {"low": None, "high": None},
            "clubs": {"low": None, "high": None},
        }

        self.started = False
        self.winner = None
        self.current_turn = None

    def add_player(self):
        if self.started:
            return None
        player_id = None
        for i in range(1,5):
            pid = f"Player {i}"
            if pid not in self.players:
                self.players.append(pid)
                player_id = pid
                break
                        
        if len(self.players) == 4 and not self.started:
            self.hands, self.current_turn = deal_cards(self.players)
            self.started = True

        return player_id

    def remove_player(self, player_id):

        if player_id in self.players:
            self.players.remove(player_id)

    def play_card(self, player_id, card):
        
        if self.winner:
            return False
        
        if player_id not in self.players:
            return False
        
        if player_id != self.current_turn:
            return False

        if all(p["low"] is None for p in self.piles.values()):
            if card != "7H":
                return False
            
        if card not in self.hands[player_id]:
            return False

        suit = card[-1]
        rank = card[:-1]

        suit_map = {
            "H": "hearts",
            "S": "spades",
            "D": "diamonds",
            "C": "clubs"
        }

        pile = self.piles[suit_map[suit]]

        rank_order = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
        r = rank_order.index(rank) + 1

        valid_move = False

        if pile["low"] is None:

            if rank == "7":
                pile["low"] = 7
                pile["high"] = 7
                valid_move = True

        else:

            if r == pile["low"] - 1:
                pile["low"] = r
                valid_move = True

            elif r == pile["high"] + 1:
                pile["high"] = r
                valid_move = True

        if not valid_move:
            return False

        # remove card only after valid move
        self.hands[player_id].remove(card)
        if len(self.hands[player_id]) == 0:
            self.winner = player_id
            self.started = False

        # move to next player
        players = self.players
        i = players.index(player_id)
        self.current_turn = players[(i + 1) % len(players)]

        return True

    def pass_turn(self, player_id):

        if player_id != self.current_turn:
            return False

        players = self.players
        i = players.index(player_id)

        self.current_turn = players[(i + 1) % len(players)]

        return True
    
    def get_scores(self):
        rank_values = {
            "A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, 
            "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13
        }
        scores = {}
        for player_id, hand in self.hands.items():
            # Score is sum of ranks; rank is card[:-1]
            score = sum(rank_values.get(card[:-1], 0) for card in hand)
            scores[player_id] = score
        return scores

    def reset_game(self):
        self.piles = {
            "hearts": {"low": None, "high": None},
            "spades": {"low": None, "high": None},
            "diamonds": {"low": None, "high": None},
            "clubs": {"low": None, "high": None},
        }

        self.hands, self.current_turn = deal_cards(self.players)

        self.winner = None
        self.started = True

game_manager = GameManager()