from .deck import deal_cards


class GameManager:

    def __init__(self):

        self.players = []
        self.connected = {}
        self.player_tokens = {} # self.player_tokens[player_id] = token
        self.hands = {}
        self.final_scores = None

        self.piles = {
            "hearts": {"low": None, "high": None},
            "spades": {"low": None, "high": None},
            "diamonds": {"low": None, "high": None},
            "clubs": {"low": None, "high": None},
        }

        self.started = False
        self.winner = None
        self.current_turn = None
        self.paused = False
        self.disconnected_player = None
        self.disconnect_timeout_expired = False
        self.game_ended = False
        
    def get_player_by_token(self, token):
        for player_id, player_token in self.player_tokens.items():
            if player_token == token:
                return player_id
        return None
    
    def handle_disconnect_timeout(self):

        if not self.paused:
            return False

        if self.disconnected_player is None:
            return False

        player_id = self.disconnected_player

        if player_id not in self.players:
            return False

        self.players.remove(player_id)
        self.connected.pop(player_id, None)
        self.player_tokens.pop(player_id, None)
        self.hands.pop(player_id, None)

        self.disconnect_timeout_expired = True

        return True

    def add_player(self, token):
                
        player_id = self.get_player_by_token(token)
        if player_id is not None:
            self.connected[player_id] = True
            return player_id
        
        if self.started:
            return None
        
        player_id = None
        for i in range(1,5):
            pid = f"Player {i}"
            if pid not in self.players:
                self.players.append(pid)
                player_id = pid
                self.player_tokens[player_id] = token
                self.connected[player_id] = True
                break
                        
        if len(self.players) == 4 and not self.started and not self.game_ended:
            self.hands, self.current_turn = deal_cards(self.players)
            self.started = True

        return player_id

    def remove_player(self, player_id):

        if player_id in self.players:
            self.connected[player_id] = False
            
    def pause_for_disconnect(self, player_id):
        if not self.started:
            return False

        if player_id != self.current_turn:
            return False

        self.paused = True
        self.disconnected_player = player_id
        self.disconnect_timeout_expired = False

        return True
    
    def resume_after_reconnect(self, player_id):
        if self.disconnected_player != player_id:
            return False

        self.paused = False
        self.disconnected_player = None
        self.disconnect_timeout_expired = False

        return True

    def check_for_disconnected_turn(self):
        if not self.started:
            return False

        if self.current_turn in self.connected:
            if not self.connected[self.current_turn]:
                return self.pause_for_disconnect(
                    self.current_turn
                )

        return False
    
    def play_card(self, player_id, card):
        if self.paused:
            return False
        
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
            self.final_scores = self.get_scores()

        # move to next player
        players = self.players
        i = players.index(player_id)
        self.current_turn = players[(i + 1) % len(players)]

        self.check_for_disconnected_turn()

        return True

    def pass_turn(self, player_id):
        
        if self.paused:
            return False

        if player_id != self.current_turn:
            return False
        
        if all(p["low"] is None for p in self.piles.values()):
            return False

        players = self.players
        i = players.index(player_id)

        self.current_turn = players[(i + 1) % len(players)]
        self.check_for_disconnected_turn()

        return True
    
    def end_game(self):
        if not self.paused:
            return False

        if not self.disconnect_timeout_expired:
            return False

        self.final_scores = self.get_scores()

        self.started = False
        self.paused = False
        self.disconnected_player = None
        self.game_ended = True

        return True
    
    def get_scores(self):
        if self.final_scores is not None:
            return self.final_scores.copy()

        rank_values = {
            "A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
            "7": 7, "8": 8, "9": 9, "10": 10,
            "J": 11, "Q": 12, "K": 13
        }

        scores = {}
        for player_id, hand in self.hands.items():
            score = sum(
                rank_values.get(card[:-1], 0)
                for card in hand
            )
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
        self.paused = False
        self.disconnected_player = None
        self.disconnect_timeout_expired = False
        self.game_ended = False
        self.final_scores = None

game_manager = GameManager()