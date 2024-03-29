import pytest

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
    player1 = [Player(name='test1', cards=[Card('assassin'), Card('assassin')])]
    c1 = Coup(player1)
    assert len(c1.deck.cards) == 13
    assert len(c1.current_player.cards) == 2
    assert c1.current_player.cards[0].name == 'assassin'
    assert c1.current_player.cards[1].name == 'assassin'


def test_foreign_aid():
    player = [Player('test0', cards=[Card('duke')]), Player('test1', cards=[Card('assassin'), Card('assassin')])]
    c = Coup(player)
    assert c.get_player('test0').coins == 2
    c.trigger('foreign_aid')
    c.trigger('decline_block_foreign_aid')
    assert c.get_player('test0').coins == 4
    assert c.current_player.name == 'test1'
    c.trigger('foreign_aid')
    c.trigger('block_foreign_aid', blocker='test0')
    c.trigger('decline_challenge_block_foreign_aid')
    assert c.get_player('test1').coins == 2
    assert c.current_player.name == 'test0'
    c.trigger('foreign_aid')
    c.trigger('block_foreign_aid', blocker='test1')
    c.trigger('challenge_block_foreign_aid')
    assert c.get_player('test1').influence() == 1
    assert c.get_player('test0').coins == 6
    assert c.current_player.name == 'test1'
    c.trigger('foreign_aid')
    c.trigger('block_foreign_aid', blocker='test0')
    c.trigger('challenge_block_foreign_aid')
    assert c.get_player('test1', active=False).influence() == 0
    assert c.get_player('test1', active=False).is_dead() is True
    assert c.get_player('test1', active=False).coins == 2


def test_assassin():
    players = [Player('test0', cards=[Card('assassin'), Card('duke')]), Player('test1', cards=[Card('contessa'), Card('duke')])]
    c = Coup(players)
    c.trigger('income')
    c.trigger('income')
    assert c.current_player.name == 'test0'
    c.trigger('assassin', target='test1')
    c.trigger('decline_block_assassin')
    assert c.get_player('test0').influence() == 2
    assert c.get_player('test1').influence() == 1
    c.trigger('income')
    assert c.current_player.name == 'test0'
    c.trigger('assassin', target='test1')
    c.trigger('block_assassin')
    c.trigger('decline_challenge_block_assassin')
    assert c.get_player('test0').influence() == 2
    assert c.get_player('test1').influence() == 1
    assert c.current_player.name == 'test1'
    print(c)
    c.trigger('assassin', target='test0')
    c.trigger('block_assassin')
    c.trigger('challenge_block_assassin', challenger='test1')
    assert c.get_player('test1', active=False).influence() == 1
    assert c.current_player.name == 'test0'
    c.trigger('assassin', target='test1')
    c.trigger('block_assassin')
    c.trigger('challenge_block_assassin', challenger='test0')
    assert c.get_player('test0', active=False).is_dead()


def test_coup():
    players = [Player(name='test0', coins=7), Player(name='test1')]
    c = Coup(players)
    c.trigger('coup', target='test1')
    assert c.get_player('test1').influence() == 1
    assert c.get_player('test0').coins == 0


def test_force_coup():
    players = [Player(name='test0', coins=10), Player(name='test1')]
    c = Coup(players, debug=True)
    c.trigger('income')
    assert c.players[0].coins == 10


def test_duke():
    players = [Player('test0', cards=[Card('duke')]), Player('test1', cards=[Card('contessa'), Card('contessa')])]
    c = Coup(players)
    assert c.current_player.name == 'test0'
    assert c.current_player.coins == 2
    c.trigger('duke')
    c.trigger('decline_challenge_duke')
    assert c.get_player('test0').coins == 5

    assert c.current_player.name == 'test1'
    c.trigger('duke')
    c.trigger('challenge_duke', challenger='test0')
    assert c.get_player('test1').influence() == 1
    assert c.get_player('test0').coins == 5
    assert c.get_player('test1').coins == 2

    assert c.current_player.name == 'test0'
    c.trigger('duke')
    c.trigger('challenge_duke', challenger='test1')
    assert c.get_player('test1', active=False).influence() == 0
    assert c.get_player('test0').influence() == 2
    assert c.get_player('test0').coins == 8


def test_captain():
    c = Coup([Player('test0', cards=[Card('captain'), Card('captain')]), Player('test1', cards=[Card('contessa'), Card('contessa')])])
    assert c.current_player.name == 'test0'
    c.trigger('captain', target='test1')
    c.trigger('decline_challenge_captain')
    assert c.get_player('test1').coins == 0
    assert c.get_player('test0').coins == 4
    assert c.current_player.name == 'test1'
    c.trigger('captain', target='test0')
    c.trigger('challenge_captain', target='test0')
    assert c.get_player('test1').influence() == 1
    assert c.get_player('test1').coins == 0
    assert c.get_player('test0').coins == 4
    c.trigger('captain', target='test1')
    c.trigger('block_captain')
    c.trigger('challenge_block_captain', challenger='test1')
    assert c.get_player('test1', active=False).influence() == 0
    assert c.get_player('test1', active=False).coins == 0
    assert c.get_player('test0').coins == 4




def test_ambassador():
    players = [Player('test0', cards=[Card('duke')]), Player('test1', cards=[Card('contessa'), Card('contessa')])]
    c = Coup(players)
