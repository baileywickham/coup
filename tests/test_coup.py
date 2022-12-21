from coup import __version__
from coup import *


def test_version():
    assert __version__ == '0.1.0'


def test_pre_deck():
    deck = Deck()
    assert len(deck.cards) == 15
    pre_card = Card('duke')

    deck1 = Deck(pre_cards=[pre_card])
    assert len(deck1.cards) == 14
    assert deck1.cards.count(pre_card) == 2

def test_income():
    players = [Player('test0'), Player('test1')]
    c = Coup(players)
    assert c.active_players == players
    assert c.current_player.name == 'test0'
    assert c.get_player('test0').coins == 2
    c.trigger('income')
    assert c.get_player('test0').coins == 3
    assert c.get_player('test1').coins == 2
    c.trigger('income')
    assert c.get_player('test1').coins == 3


def test_pre_card():
    pre_card = Card('duke')
    new_deck = Deck(pre_cards=[pre_card])
    assert len(new_deck.cards) == 14
    player = [Player('test0', cards=[pre_card])]
    assert player[0].cards[0].name == 'duke'
    c = Coup(player)
    assert len(c.deck.cards) == 13
