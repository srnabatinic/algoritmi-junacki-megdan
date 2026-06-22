from enum import Enum
from typing import List

class Color(Enum):
    WHITE = 'W'
    BLACK = 'B'

class PieceType(Enum):
    JUNAK = 'J'
    KRALJEVIC = 'K'
    MARKO_KRALJEVIC = 'KM'


class Piece():
    
    def __init__(self, color: Color, type: PieceType):
        self.color = color
        self.type = type
        self.effects = {}
        self.relics = set()
        self.active_relics = {}  # { RelicType: RelicEffect }
        
    def promote(self):
        if self.type == PieceType.JUNAK:
            self.type = PieceType.KRALJEVIC
    
    def promote_to_marko(self):
        """Promocija do Marko Kraljevića"""
        self.type = PieceType.MARKO_KRALJEVIC
    
    def activate_relic(self, relic_type):
        """Aktiviraj relikviјu na figuri"""
        from relics import get_relic_duration, RelicEffect
        duration = get_relic_duration(relic_type, is_marko=self.is_marko())
        self.active_relics[relic_type] = RelicEffect(relic_type, duration)
    
    def is_marko(self):
        return self.type == PieceType.MARKO_KRALJEVIC

    def __repr__(self):
        return f"{self.color.value}{self.type.value}"
    
    def is_king(self):
        return self.type in (PieceType.KRALJEVIC, PieceType.MARKO_KRALJEVIC)

    def tick_effects(self):
        for effect in list(self.effects.keys()):
            self.effects[effect] -= 1
            if self.effects[effect] <= 0:
                del self.effects[effect]
        for relic_type in list(self.active_relics.keys()):
            self.active_relics[relic_type].tick()
            if not self.active_relics[relic_type].is_active():
                del self.active_relics[relic_type]

    def has_effect(self, effect_name):
        return effect_name in self.effects
    
    def has_relic(self, relic_type):
        return relic_type in self.active_relics
    
    def get_active_relics(self):
        return list(self.active_relics.keys())