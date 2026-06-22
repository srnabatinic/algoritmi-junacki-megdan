from board import Board
from display import Display
from move_generator import MoveGenerator
from piece import Piece, Color, PieceType

b = Board()
# Postavi ručno situaciju za skok
b.set_piece(20, Piece(Color.WHITE, PieceType.JUNAK))
b.set_piece(16, Piece(Color.BLACK, PieceType.JUNAK))
# Bela figura na 20 treba da može da pojede crnu na 16

mg = MoveGenerator()
captures = mg.get_capture_moves(b, Color.WHITE)
print(captures)