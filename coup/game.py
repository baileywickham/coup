from typing import Optional, Callable

from transitions import State, EventData
from transitions.extensions import GraphMachine

from coup.deck import *
from coup.states import *

from functools import partial


class Player:
    def __init__(self, name, cards=None, coins=2):
        self.name = name
        self.coins = coins
        self.cards: list[Card] = cards or []

    def __repr__(self):
        return f'{self.name}: {self.coins} coins, cards: {self.cards}'

    def show(self, name) -> Card:
        """
        Validate a player has a claimed card and return it (to the deck).
        :parameter str name: the name of the card to return
        :return Card: the card return
        """
        for card in self.cards:
            if card.name == name:
                self.cards.remove(Card(name))
                return card

    def lose_influence(self, name=None):
        """
        force a player to lose influence.
        :param name: if provided, flip this card over
        :return:
        """
        for card in self.cards:
            if name:
                if card.face_up is False and card.name == name:
                    card.face_up = True
                    return
            if card.face_up is False:
                card.face_up = True
                return

    def is_dead(self) -> bool:
        """
        :return bool: returns if the player is dead
        """
        for card in self.cards:
            if card.face_up is False:
                return False
        return True

    def draw(self, card: Card):
        self.cards.append(card)

    def influence(self) -> int:
        """
        :return int: returns the number of influence left
        """
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
              State(name=States.waiting_block_assassin),
              State(name=States.waiting_challenge_block_assassin),
              State(name=States.waiting_challenge_duke), ]

    def __init__(self, players: list[Player], debug=False):
        self.debug = debug
        if self.debug:
            import logging
            logging.basicConfig(level=logging.DEBUG)
            # Set transitions' log level to INFO; DEBUG messages will be omitted
            logging.getLogger('transitions').setLevel(logging.INFO)

        # Since an FSM isn't a turing machine, we must store some state in the class
        self.foreign_aid_blocker: Optional[Player] = None
        self.assassin_target: Optional[Player] = None
        self.captain_target: Optional[Player] = None
        self.player_index = 0
        self.players = players
        self.active_players = players.copy()
        self.current_player = self.active_players[0]

        pre_cards = []
        for player in self.active_players:
            pre_cards.extend(player.cards)
        self.deck = Deck(pre_cards=pre_cards)

        for player in self.active_players:
            while len(player.cards) < 2:
                player.draw(self.deck.draw())

        self.m: GraphMachine = GraphMachine(model=self, states=Coup.states, initial=States.player_turn, send_event=True,
                                            show_state_attributes=True, show_conditions=True,
                                            show_auto_transitions=True,
                                            auto_transitions=False)
        self.m.add_transition(trigger='game_over', source=States.player_turn, dest=States.game_over),

        self.m.add_transition(trigger='income', source=States.player_turn, dest=States.player_turn,
                              before=self.do_income, unless=self.force_coup),
        self.m.add_transition(trigger='coup', source=States.player_turn, dest=States.player_turn, before=self.do_coup),

        # Foreign aid states
        self.m.add_transition(trigger='foreign_aid', source=States.player_turn, dest=States.waiting_block_foreign_aid,
                              unless=self.force_coup),
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
        self.m.add_transition(trigger='assassin', source=States.player_turn, dest=States.waiting_block_assassin,
                              before=self.queue_assassin, unless=self.force_coup)
        self.m.add_transition(trigger='challenge_assassin', source=States.waiting_block_assassin,
                              dest=States.player_turn,
                              before=self.resolve_challenge(self.get_current_player, 'assassin'))
        self.m.add_transition(trigger='block_assassin', source=States.waiting_block_assassin,
                              dest=States.waiting_challenge_block_assassin)
        self.m.add_transition(trigger='decline_block_assassin', source=States.waiting_block_assassin,
                              dest=States.player_turn, before=self.do_assassin)
        self.m.add_transition(trigger='challenge_block_assassin', source=States.waiting_challenge_block_assassin,
                              dest=States.player_turn, before=self.resolve_challenge_block_assassin)
        self.m.add_transition(trigger='decline_challenge_block_assassin',
                              source=States.waiting_challenge_block_assassin,
                              dest=States.player_turn)

        # Duke states
        self.m.add_transition(trigger='duke', source=States.player_turn, dest=States.waiting_challenge_duke,
                              unless=self.force_coup)
        self.m.add_transition(trigger='decline_challenge_duke', source=States.waiting_challenge_duke,
                              dest=States.player_turn, before=self.do_duke)
        self.m.add_transition(trigger='challenge_duke', source=States.waiting_challenge_duke, dest=States.player_turn,
                              before=self.resolve_challenge(self.get_current_player, 'duke', self.do_duke))

        # Captain states
        self.m.add_transition(trigger='captain', source=States.player_turn, dest=States.waiting_challenge_captain,
                              before=self.queue_captain, unless=self.force_coup)
        self.m.add_transition(trigger='decline_block', source=States.waiting_challenge_captain, dest=States.player_turn,
                              before=self.do_captain)
        self.m.add_transition(trigger='block_captain', source=States.waiting_challenge_captain,
                              dest=States.waiting_challenge_block_captain)
        self.m.add_transition(trigger='challenge_block_captain', source=States.waiting_challenge_block_captain,
                              dest=States.player_turn, before=self.resolve_challenge_block_captain)
        self.m.add_transition(trigger='decline_challenge_block_captain', source=States.waiting_challenge_block_captain,
                              dest=States.player_turn)
        self.m.add_transition(trigger='decline_challenge', source=States.waiting_challenge_captain,
                              dest=States.player_turn, before=self.do_captain)
        self.m.add_transition(trigger='challenge_captain', source=States.waiting_challenge_captain,
                              dest=States.player_turn,
                              before=self.resolve_challenge(self.get_current_player, 'captain', self.do_captain))

        # Ambassador states
        self.m.add_transition(trigger='ambassador', source=States.player_turn, dest=States.waiting_challenge_ambassador,
                              unless=self.force_coup)

        self.m.get_graph().draw('coup.png', prog='dot')

    def __repr__(self):
        return f'State: {self.state}\n' + '\n'.join([str(player) for player in self.active_players])

    def get_current_player(self) -> Player:
        """ Helper method to return the current player, needed because of the resolve_conflict closure."""
        return self.current_player

    def get_assassin_target(self) -> Player:
        return self.assassin_target

    def force_coup(self, event):
        return True if self.current_player.coins >= 10 else False

    def exchange_card(self, player: Player, card: Card):
        self.deck.return_to_deck(card)
        player.draw(self.deck.draw())

    def get_player(self, name: str, active: bool = True) -> Player:
        """
        Returns a player
        :param active: only returns active players
        :param name: name of player to return
        :return:
        """
        search_list = self.active_players if active else self.players
        for player in search_list:
            if player.name == name:
                return player

    def next_turn(self, event):
        self.assassin_target = None
        self.foreign_aid_blocker = None
        self.captain_target = None
        if self.debug:
            if len(self.active_players) == 0:
                self.trigger('game_over')
        self.player_index = (self.player_index + 1) % len(self.active_players)
        self.current_player = self.active_players[self.player_index]

    def do_income(self, event=None):
        self.current_player.coins += 1

    def do_foreign_aid(self, event=None):
        self.current_player.coins += 2

    def do_coup(self, event: EventData):
        target: Player = self.get_player(event.kwargs.get('target'))
        if self.current_player.coins < 7:
            raise Exception('need at least 7 coins')
        if not target:
            raise Exception('undefined target')
        self.current_player.coins -= 7
        self.lose_influence(target)

    def do_assassin(self, event: EventData):
        self.lose_influence(self.assassin_target)

    def do_duke(self, event: EventData = None):
        self.current_player.coins += 3

    def lose_influence(self, target: Player):
        target.lose_influence()
        if target.is_dead():
            self.active_players.remove(target)

    def resolve_challenge_block_foreign_aid(self, event: EventData):
        blocker: Player = self.foreign_aid_blocker
        if card := blocker.show('duke'):
            self.lose_influence(self.current_player)
            self.exchange_card(blocker, card)
        else:
            self.lose_influence(blocker)
            self.do_foreign_aid()

    def resolve_challenge_block_assassin(self, event: EventData):
        blocker = self.assassin_target
        if card := blocker.show('contessa'):
            self.lose_influence(self.current_player)
            self.exchange_card(blocker, card)
        else:
            self.lose_influence(blocker)

    def resolve_challenge_block_captain(self, event: EventData):
        blocker = self.captain_target
        if card := (blocker.show('captain') or blocker.show('ambassador')):
            self.lose_influence(self.current_player)
            self.exchange_card(blocker, card)
        else:
            self.lose_influence(blocker)
            self.do_captain()

    def get_possible_transitions(self):
        return self.m.get_triggers(self.state)

    def queue_assassin(self, event: EventData):
        if self.current_player.coins < 3:
            raise Exception('need at least 3 coins')
        target: Player = self.get_player(event.kwargs.get('target'))
        if not target or target == self.current_player:
            raise Exception('invalid target')
        self.assassin_target = target

    def queue_block_foreign_aid(self, event: EventData):
        blocker: Player = self.get_player(event.kwargs.get('blocker'))
        if not blocker or blocker == self.current_player:
            raise Exception('invalid blocker')
        self.foreign_aid_blocker = blocker

    def queue_captain(self, event: EventData):
        target = self.get_player(event.kwargs.get('target'))
        self.captain_target = target

    def do_captain(self, event: Optional[EventData]):
        if self.captain_target.coins >= 2:
            self.captain_target.coins -= 2
            self.current_player.coins += 2
        else:
            self.current_player.coins += self.captain_target.coins
            self.captain_target.coins = 0

    def resolve_challenge(self, get_challenged: Callable[[], Player], card_name: str, callback=None):
        def part(event: EventData):
            challenged: Player = get_challenged()
            challenger = self.get_player(event.kwargs.get('challenger'))
            if not challenger:
                raise Exception('challenger is not defined')
            if card := challenged.show(card_name):
                # The challenged won
                self.lose_influence(challenger)
                self.exchange_card(challenged, card)
                if callback:
                    callback()
            else:
                # The challenger won
                self.lose_influence(challenged)

        return part


players = [Player(name='hi', coins=12)]
c = Coup(players, debug=True)
