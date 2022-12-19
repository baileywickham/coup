from transitions import Machine
import random
import enum
import itertools

class Deck(enum.Enum):
    Duke = 0
    Assassin = 1
    Contessa = 2
    Captain = 3
    Ambassador = 4


class States(enum.Enum):
    PLAYER_TURN = 0


class Player:
    def __init__(self, name) -> None:
        self.name = name
        self.cards: tuple
        self.coins = 2

    def get_influence(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return f'{self.name}(coins: {self.coins}, cards: {self.cards}'

    def income(self):
        self.coins += 1



class Coup:
    def __init__(self, players: list[Player]) -> None:
        self.current_player: Player
        self.players = itertools.cycle(players)

        self.deck: list[Deck] = [Deck.Duke, Deck.Assassin, Deck.Contessa, Deck.Captain, Deck.Ambassador]*3
        random.shuffle(self.deck)
        self.distribute_cards()

        self.machine = self.machine = Machine(model=self, states=States, initial='asleep')
        self.machine.add_transition('income', States.PLAYER_TURN, States.PLAYER_TURN, after=[self.income, self.next_turn])

    def draw(self) -> Deck:
        return self.deck.pop()

    def distribute_cards(self):
        for player in self.players:
            player.cards = (self.deck.pop(), self.deck.pop())

    def income(self):
        self.current_player.income()

    def next_turn(self):
        self.current_player = next(self.players)






