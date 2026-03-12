import random

suits = ["H", "S", "C", "D"]
ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]

def generate_deck():
    deck = []
    for s in suits:
        for r in ranks:
            deck.append(r+s)
    random.shuffle(deck)
    return deck

def deal_cards(players):
    deck = generate_deck()
    hands = {}
    
    for i, p in enumerate(players):
        hands[p] = deck[i::len(players)]
    
    for player in players:
        if "7H" in hands[player]:
            current_turn = player
            break

    return hands, current_turn
