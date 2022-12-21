from typing import Optional

from transitions import State, EventData
from transitions.extensions import GraphMachine

from coup.deck import *
from coup.states import *


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
        """
        Validate a player has a claimed card and return it (to the deck).
        """
        for card in self.cards:
            if card.name == name:
                return card

    def lose_influence(self, name=None):
        """
        force a player to lose influence.
        :param name:
        :return:
        """
        for card in self.cards:
            if card.face_up is False:
                card.face_up = True
                return

    def is_dead(self):
        for card in self.cards:
            if card.face_up is False:
                return False
        return True

    def draw(self, card: Card):
        self.cards.append(card)

    def influence(self):
        influence = 0
        for card in self.cards:
            if card.face_up is False:
                influence += 1
        return influence


class Coup:
    states = [State(name=States.player_turn, on_enter='next_turn'),
              State(name=States.game_over),
              State(name=States.waiting_block_foreign_aid),
              State(name=States.waiting_challenge_block_foreign_aid),
              State(name=States.waiting_block_assassinate),
              State(name=States.waiting_challenge_block_assassinate), ]

    def __init__(self, players: list[Player], debug=False):
        if debug:
            import logging
            logging.basicConfig(level=logging.DEBUG)
            # Set transitions' log level to INFO; DEBUG messages will be omitted
            logging.getLogger('transitions').setLevel(logging.INFO)

        # Since an FSM isn't a turing machine, we must store some state in the class
        self.foreign_aid_blocker: Optional[Player] = None
        self.assassination_target: Optional[Player] = None
        self.player_index = 0
        self.players = players
        self.active_players = players
        self.current_player = players[0]

        pre_cards = []
        for player in players:
            pre_cards.extend(player.cards)
        self.deck = Deck(pre_cards=pre_cards)

        for player in self.active_players:
            while len(player.cards) < 2:
                player.draw(self.deck.draw())

        self.m: GraphMachine = GraphMachine(model=self, states=Coup.states, initial=States.player_turn, send_event=True,
                                            auto_transitions=False)
        self.m.add_transition(trigger='game_over', source=States.player_turn, dest=States.game_over),

        self.m.add_transition(trigger='income', source=States.player_turn, dest=States.player_turn, before='do_income'),
        self.m.add_transition(trigger='coup', source=States.player_turn, dest=States.player_turn, before='do_coup'),

        # Foreign aid states
        self.m.add_transition(trigger='foreign_aid', source=States.player_turn, dest=States.waiting_block_foreign_aid),
        self.m.add_transition(trigger='decline_block_foreign_aid', source=States.waiting_block_foreign_aid,
                              dest=States.player_turn, before='do_foreign_aid'),
        self.m.add_transition(trigger='block_foreign_aid',
                              source=States.waiting_block_foreign_aid, dest=States.waiting_challenge_block_foreign_aid,
                              before=self.queue_block_foreign_aid),
        self.m.add_transition(trigger='challenge_block_foreign_aid', source=States.waiting_challenge_block_foreign_aid,
                              dest=States.player_turn, before=self.resolve_challenge_block_foreign_aid),
        self.m.add_transition(trigger='decline_challenge_block_foreign_aid',
                              source=States.waiting_challenge_block_foreign_aid,
                              dest=States.player_turn),
        # Assassinate states
        self.m.add_transition(trigger='assassinate', source=States.player_turn, dest=States.waiting_block_assassinate,
                              before=self.queue_assassinate)
        self.m.add_transition(trigger='challenge_assassin', source=States.waiting_block_assassinate,
                              dest=States.player_turn, before=self.resolve_challenge_assassin)
        self.m.add_transition(trigger='block_assassinate', source=States.waiting_block_assassinate,
                              dest=States.waiting_challenge_block_assassinate)
        self.m.add_transition(trigger='decline_block_assassinate', source=States.waiting_block_assassinate,
                              dest=States.player_turn, before=self.do_assassinate)
        self.m.add_transition(trigger='challenge_block_assassinate', source=States.waiting_challenge_block_assassinate,
                              dest=States.player_turn, before=self.resolve_challenge_block_assassinate)
        self.m.add_transition(trigger='decline_challenge_block_assassinate', source=States.waiting_challenge_block_assassinate,
                              dest=States.player_turn)

        self.m.get_graph().draw('coup.png', prog='dot')

    def __repr__(self):
        return f'State: {self.state}\n' + '\n'.join([str(player) for player in self.active_players])

    def force_coup(self):
        return True if self.current_player.coins >= 10 else False

    def exchange_card(self, player: Player, card: Card):
        self.deck.return_to_deck(card)
        player.draw(self.deck.draw())

    def get_player(self, name):
        for player in self.active_players:
            if player.name == name:
                return player

    def next_turn(self, event):
        self.assassination_target = None
        self.foreign_aid_blocker = None
        if len(self.active_players) == 0:
            self.trigger('game_over')
        self.player_index = (self.player_index + 1) % len(self.active_players)
        self.current_player = self.active_players[self.player_index]

    def do_income(self, event):
        self.current_player.income()

    def do_foreign_aid(self, event):
        self.current_player.foreign_aid()

    def do_coup(self, event):
        target: Player = self.get_player(event.kwargs.get('target'))
        if self.current_player.coins < 7:
            raise Exception('need at least 7 coins')
        if not target:
            raise Exception('undefined target')
        self.lose_influence(target)

    def do_assassinate(self, event):
        self.assassination_target.lose_influence()

    def lose_influence(self, target: Player):
        target.lose_influence()
        if target.is_dead():
            self.active_players.remove(target)

    def resolve_challenge_block_foreign_aid(self, event: EventData):
        blocker: Player = self.foreign_aid_blocker
        if card := blocker.show('duke'):
            self.current_player.lose_influence()
            self.exchange_card(blocker, card)
        else:
            blocker.lose_influence()
            self.current_player.foreign_aid()

    def resolve_challenge_block_assassinate(self, event: EventData):
        blocker = self.assassination_target
        if card := blocker.show('contessa'):
            self.current_player.lose_influence()
            self.exchange_card(blocker, card)
        else:
            blocker.lose_influence()

    def resolve_challenge_assassin(self, event: EventData):
        # Challenge fails, assassination target loses a challenge
        if card := self.current_player.show('assassin'):
            self.assassination_target.lose_influence()
            self.deck.return_to_deck(card)
            self.current_player.draw(self.deck.draw())
        else:
            # Assassin loses challenge, shows a card
            self.current_player.lose_influence()

    def get_possible_transitions(self):
        return self.m.get_triggers(self.state)

    def queue_assassinate(self, event: EventData):
        if self.current_player.coins < 3:
            raise Exception('need at least 3 coins')
        target: Player = self.get_player(event.kwargs.get('target'))
        if not target or target == self.current_player:
            raise Exception('invalid target')
        self.assassination_target = target

    def queue_block_foreign_aid(self, event: EventData):
        blocker: Player = self.get_player(event.kwargs.get('blocker'))
        if not blocker or blocker == self.current_player:
            raise Exception('invalid blocker')
        self.foreign_aid_blocker = blocker
