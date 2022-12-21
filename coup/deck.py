import random


class Card:
    def __init__(self, name, face_up=False):
        self.name = name
        self.face_up = face_up

    def __repr__(self):
        return f'{self.name}, {"UP" if self.face_up else "DOWN"}'

    def __eq__(self, other):
        return isinstance(other, Card) and other.name == self.name


class Deck:
    card_types = ['duke', 'assassin', 'contessa', 'captain', 'ambassador']

    def __init__(self, pre_cards: list[Card] = None):
        """ Returns a shuffled deck
        :parameter pre_cards a list of pre drawn cards for debugging purposes. These cards are considered already drawn
        and will not be added to the deck."""
        self.cards: list[Card] = []
        for card_type in Deck.card_types:
            while self.cards.count(Card(card_type)) + (pre_cards.count((Card(card_type))) if pre_cards else 0) < 3:
                self.cards.append(Card(card_type))
        self.shuffle()

    def return_to_deck(self, card):
        self.cards.append(card)
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def shuffle(self):
        random.shuffle(self.cards)
