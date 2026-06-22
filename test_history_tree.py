from board import Board
from piece import Piece, Color, PieceType
from move_generator import MoveGenerator, Move
from game_state import GameState
from history_tree import HistoryTree

# Pocetno stanje
b = Board()
b.setup_initial_position()
mg = MoveGenerator()

initial_state = GameState(
    board=b.copy(),
    current_player=Color.WHITE,
    no_progress_counter=0,
    move=None
)

tree = HistoryTree(initial_state)
print(f"Koren: igrac={tree.root.state.current_player}, potez={tree.root.state.move}")

# Simuliraj prvi potez - beli igra 20->16
move1 = Move(20, 16)
b.set_piece(16, b.get_piece(20))
b.remove_piece(20)

state1 = GameState(
    board=b.copy(),
    current_player=Color.BLACK,
    no_progress_counter=1,
    move=move1
)
tree.add_move(state1)
print(f"Posle poteza 1: igrac={tree.current_node.state.current_player}, potez={tree.current_node.state.move}")

# Simuliraj drugi potez - crni igra 11->16 (jedenje nije obavezno u ovom testu)
move2 = Move(11, 15)
b.set_piece(15, b.get_piece(11))
b.remove_piece(11)

state2 = GameState(
    board=b.copy(),
    current_player=Color.WHITE,
    no_progress_counter=2,
    move=move2
)
tree.add_move(state2)
print(f"Posle poteza 2: igrac={tree.current_node.state.current_player}, potez={tree.current_node.state.move}")

# Undo - vracamo se na state1
tree.undo()
print(f"Posle undo: igrac={tree.current_node.state.current_player}, potez={tree.current_node.state.move}")

# Odigraj alternativni potez iz state1 - crni igra drugacije
b2 = tree.current_node.state.board.copy()
move2b = Move(10, 15)
b2.set_piece(15, b2.get_piece(10))
b2.remove_piece(10)

state2b = GameState(
    board=b2.copy(),
    current_player=Color.WHITE,
    no_progress_counter=2,
    move=move2b
)
tree.add_move(state2b)
print(f"Alternativni potez: igrac={tree.current_node.state.current_player}, potez={tree.current_node.state.move}")

# Proveri grananje - state1 treba da ima 2 deteta
tree.undo()
print(f"Broj dece cvora state1: {len(tree.current_node.children)}")

# Prikazi sve putanje kroz stablo
tree.undo()  # vrati se na koren
# Koren nema move pa dodajemo jedan potez pa idemo nazad na koren
all_paths = tree.get_full_history()
print(f"Broj putanja u stablu: {len(all_paths)}")
for i, path in enumerate(all_paths):
    moves_in_path = [str(s.move) for s in path if s.move is not None]
    print(f"  Putanja {i+1}: {' -> '.join(moves_in_path)}")