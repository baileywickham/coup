from coup.deck import Card


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
