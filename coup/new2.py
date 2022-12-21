from transitions import State, Machine, Transition, EventData
import random

from transitions.extensions import GraphMachine


class Card:
    def __init__(self, name, face_up=False):
        self.name = name
        self.face_up = face_up

    def __repr__(self):
        return f'{self.name}'

    def __eq__(self, other):
        return isinstance(other, Card) and other.name == self.name


class Deck:
    card_types = ['duke', 'assassin', 'contessa', 'captain', 'ambassador']

    def __init__(self, pre_cards: list[Card] = None):
        """ Returns a shuffled deck
        :parameter pre_cards a list of pre drawn cards for debugging purposes."""
        self.cards: list[Card] = pre_cards or []
        for card_type in Deck.card_types:
            while self.cards.count(Card(card_type)) < 3:
                self.cards.append(Card(card_type))
        self.shuffle()

    def return_to_deck(self, card):
        self.cards.append(card)
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop()

    def shuffle(self):
        random.shuffle(self.cards)


class Player:
    def __init__(self, name, cards=None, coins=2):
        self.name = name
        self.coins = coins
        self.cards: list[Card] = cards or []

    def income(self):
        self.coins += 1

    def foreign_aid(self):
        self.coins += 2

    def __repr__(self):
        return f'{self.name}: {self.coins} coins, cards: {self.cards}'

    def show(self, name):
        """In the case where a player must show a card to validate they have it, return it to the deck
        """
        for card in self.cards:
            if card.name == name:
                return card

    def lose_influence(self):
        for card in self.cards:
            if card.face_up is False:
                card.face_up = True

    def is_dead(self):
        return all([True if card.face_up else False for card in self.cards])

    def draw(self, card: Card):
        self.cards.append(card)


class Coup:
    states = [State(name='player_turn', on_enter='next_turn'),
              State(name='waiting_fa_block'),
              State(name='block_foreign_aid')]

    def __init__(self, players: list[Player], deck: Deck = None):
        self.player_index = 0
        self.players = players
        self.active_players = players
        self.current_player = players[0]

        self.deck = deck or Deck()
        for player in self.active_players:
            while len(player.cards) < 2:
                player.draw(self.deck.draw())

        self.m = GraphMachine(model=self, states=Coup.states, initial='player_turn', send_event=True,
                              auto_transitions=False)
        transitions = [{'trigger': 'income', 'source': 'player_turn', 'dest': 'player_turn', 'after': 'do_income'},
                       {'trigger': 'foreign_aid', 'source': 'player_turn', 'dest': 'waiting_fa_block'},
                       {'trigger': 'decline_block', 'source': 'waiting_fa_block', 'dest': 'player_turn',
                        'after': 'do_foreign_aid'},
                       {'trigger': 'accept_block', 'source': 'waiting_fa_block', 'dest': 'block_foreign_aid'},
                       {'trigger': 'challenge_block', 'source': 'block_foreign_aid', 'dest': 'player_turn',
                        'after': 'challenge_block_foreign_aid'},
                       {'trigger': 'decline_challenge_block', 'source': 'block_foreign_aid', 'dest': 'player_turn'}
                       ]
        self.m.add_transitions(transitions)
        self.m.get_graph().draw('coup.png', prog='dot')

    def get_player(self, name):
        for player in self.active_players:
            if player.name == name:
                return player

    def next_turn(self, event):
        self.player_index = (self.player_index + 1) % len(self.active_players)
        self.current_player = self.active_players[self.player_index]
        print('current player: ', self.current_player)

    def do_income(self, event):
        self.current_player.income()

    def do_foreign_aid(self, event):
        self.current_player.foreign_aid()

    def challenge_block_foreign_aid(self, event: EventData):
        blocker: Player = self.get_player(event.kwargs.get('blocker'))
        if not blocker:
            raise Exception('needs challenger')
        if card := blocker.show('duke'):
            self.current_player.lose_influence()
        else:
            blocker.lose_influence()
            self.deck.return_to_deck(card)
            blocker.draw(self.deck.draw())
            self.current_player.foreign_aid()

    def get_possible_transitions(self):
        return self.m.get_triggers(self.state)


preCard = Card('duke')
newDeck = Deck(pre_cards=[preCard])
players = [Player('test0', cards=[preCard]), Player('test1')]
c = Coup(players)
c.trigger('income')
c.trigger('foreign_aid')
c.trigger('accept_block')
print(c.get_possible_transitions())
c.trigger('challenge_block', blocker='test0')
print(c.active_players)
print(c.get_possible_transitions())
