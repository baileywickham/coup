import enum


class States(enum.Enum):
    player_turn = 'player_turn'
    game_over = 'game_over'
    waiting_block_foreign_aid = 'waiting_foreign_aid_block'
    waiting_block_assassinate = 'waiting_block_assassinate'
    waiting_challenge_block_assassinate = 'waiting_challenge_block_assassinate'
    waiting_challenge_block_foreign_aid = 'block_foreign_aid'
