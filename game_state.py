from dataclasses import dataclass, field
from typing import Optional
from board import Board

@dataclass
class GameState:
    board: Board
    current_player: object        # Color
    no_progress_counter: int
    move: object = None           # Move objekat koji je doveo do ovog stanja
    drum_snapshot: list = field(default_factory=list)
    promoted_index: Optional[int] = None    # indeks figure koja je promovisana ovim potezom
    winner: object = None          # Color ili None
    is_terminal: bool = False      # da li je igra gotova
