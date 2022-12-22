import enum


class States(enum.Enum):
    player_turn = 'player_turn'
    game_over = 'game_over'
    waiting_block_foreign_aid = 'waiting_foreign_aid_block'
    waiting_block_assassin = 'waiting_block_assassin'
    waiting_challenge_duke = 'waiting_challenge_duke'
    waiting_challenge_ambassador = 'waiting_challenge_ambassador'
    waiting_challenge_block_assassin = 'waiting_challenge_block_assassin'
    waiting_challenge_block_captain = 'waiting_challenge_block_captain'
    waiting_challenge_block_foreign_aid = 'block_foreign_aid'
    waiting_challenge_captain = 'waiting_challenge_captain'
    ambassador_trade = 'ambassador_trade'
