from __future__ import annotations

import random
from typing import Iterable

from app.models.pokemon import Pokemon
from app.models.pokemon_move import PokemonMove


def build_default_nickname(name: str) -> str:
    return name.replace('-', ' ').title()


def pick_equipped_moves(moves: Iterable[PokemonMove], limit: int = 4) -> list[PokemonMove]:
    moves_list = list(moves)
    if len(moves_list) <= limit:
        return moves_list

    return random.sample(moves_list, limit)


def initialize_instance_progression(pokemon: Pokemon, *, nickname: str) -> dict:
    iv_hp = random.randint(0, 31)
    iv_speed = random.randint(0, 31)
    iv_attack = random.randint(0, 31)
    iv_defense = random.randint(0, 31)
    iv_special_attack = random.randint(0, 31)
    iv_special_defense = random.randint(0, 31)

    hp = max(int(pokemon.hp or 1) + iv_hp, 1)

    return {
        'hp': hp,
        'iv_hp': iv_hp,
        'ev_hp': 0,
        'wins': 0,
        'level': 1,
        'losses': 0,
        'max_hp': hp,
        'battles': 0,
        'nickname': nickname,
        'speed': max(int(pokemon.speed or 1) + iv_speed, 1),
        'iv_speed': iv_speed,
        'ev_speed': 0,
        'attack': max(int(pokemon.attack or 1) + iv_attack, 1),
        'iv_attack': iv_attack,
        'ev_attack': 0,
        'defense': max(int(pokemon.defense or 1) + iv_defense, 1),
        'iv_defense': iv_defense,
        'ev_defense': 0,
        'experience': 0,
        'special_attack': max(int(pokemon.special_attack or 1) + iv_special_attack, 1),
        'iv_special_attack': iv_special_attack,
        'ev_special_attack': 0,
        'special_defense': max(
            int(pokemon.special_defense or 1) + iv_special_defense,
            1,
        ),
        'iv_special_defense': iv_special_defense,
        'ev_special_defense': 0,
        'formula': pokemon.growth_rate.formula if pokemon.growth_rate else '',
    }
