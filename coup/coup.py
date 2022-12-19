from random import shuffle

class States:
    START = 'start'
    PLAYER_TURN = 'pturn'

class Player:
    def __init__(self, name, tokens=2, influence=2) -> None:
        self.name = name
        self.tokens = tokens
        self.cards = []
        self.face_up_cards = []
        self.influence = influence

    def is_stealable(self):
        return self.tokens >= 2

    def harm(self):
        self.influence -= 1

class Coup:
    def __init__(self, players) -> None:
        self.deck = ['duke', 'assassin', 'ambassador', 'captain', 'contessa']*3
        self.state = States.START
        self.players = players
        self.live_players = players
        self.players_by_name = {p.name: p for p in players}
        self.dead_players = []

        self.distribute()

    def distribute(self):
        shuffle(self.deck)
        for player in self.live_players:
            player.cards = [self.deck.pop(), self.deck.pop()]

    def check_dead(self, target):
        if target.tokens <= 0:
            self.live_players.remove(target)
            self.dead_players.append(target)

    def do_income(self, player):
        player.tokens +=1

    def do_foreign_aid(self, player):
        player.tokens += 2

    def do_coup(self, player, target):
        player.tokens -= 7
        target.harm()
        self.check_dead(target)

    def do_tax(self, player):
        player.tokens += 3

    def do_assassinate(self, player, target):
        player.tokens -= 3
        target.harm()
        self.check_dead(target)

    def do_exchange(self, player, cards):
        player.cards = cards

    def do_steal(self, player, target):
        target.tokens -= 2
        player.tokens += 2

    def get_players(self):
        return self.players
players = [Player('bailey'), Player('nina')]
c = Coup(players)
