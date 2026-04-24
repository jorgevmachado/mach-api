from __future__ import annotations

from datetime import datetime, timezone

from app.models.pokemon import Pokemon


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def initialize_species_progression(
    pokemon: Pokemon,
    *,
    discovered: bool,
) -> dict:
    hp = max(int(pokemon.hp or 1), 1)

    return {
        'hp': hp,
        'iv_hp': 0,
        'ev_hp': 0,
        'wins': 0,
        'level': 1,
        'losses': 0,
        'max_hp': hp,
        'battles': 0,
        'speed': max(int(pokemon.speed or 1), 1),
        'iv_speed': 0,
        'ev_speed': 0,
        'attack': max(int(pokemon.attack or 1), 1),
        'iv_attack': 0,
        'ev_attack': 0,
        'defense': max(int(pokemon.defense or 1), 1),
        'iv_defense': 0,
        'ev_defense': 0,
        'experience': 0,
        'special_attack': max(int(pokemon.special_attack or 1), 1),
        'iv_special_attack': 0,
        'ev_special_attack': 0,
        'special_defense': max(int(pokemon.special_defense or 1), 1),
        'iv_special_defense': 0,
        'ev_special_defense': 0,
        'discovered': discovered,
        'formula': pokemon.growth_rate.formula if pokemon.growth_rate else '',
        'discovered_at': _utcnow() if discovered else None,
    }
