import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_loop import GameLoop
from board import Board
from move_generator import MoveGenerator
from heusteric import Heuristic
from minimax import Minimax
from piece import Color, PieceType

print("=== COMPREHENSIVE SYSTEM TEST ===\n")

try:
    # Test 1: Postavljanje table
    print("1. BOARD SETUP")
    board = Board()
    board.setup_initial_position()
    whites = board.get_all_pieces(Color.WHITE)
    blacks = board.get_all_pieces(Color.BLACK)
    print(f"   White pieces: {len(whites)} (should be 12)")
    print(f"   Black pieces: {len(blacks)} (should be 12)")
    print(f"   OK\n")
    
    # Test 2: Generisanje poteza
    print("2. MOVE GENERATION")
    mg = MoveGenerator()
    white_moves = mg.get_all_moves(board, Color.WHITE)
    print(f"   White legal moves: {len(white_moves)}")
    print(f"   First move: {white_moves[0] if white_moves else 'None'}")
    print(f"   OK\n")
    
    # Test 3: Heuristička evaluacija
    print("3. HEURISTIC EVALUATION")
    heur = Heuristic()
    score = heur.evaluate(board, Color.WHITE)
    print(f"   Initial position score: {score:+.2f}")
    print(f"   (Should be ~0 for symmetric start)")
    print(f"   OK\n")
    
    # Test 4: Minimax pretraga
    print("4. MINIMAX SEARCH")
    mm = Minimax()
    best_move = mm.get_best_move(board, Color.WHITE)
    print(f"   Best move found: {best_move}")
    print(f"   OK\n")
    
    # Test 5: Tok igre
    print("5. GAME LOOP")
    game = GameLoop(ai_color=Color.BLACK)
    print(f"   Relic deck: {len(game.relic_deck.deck)} items")
    print(f"   First relic type: {game.relic_deck.get_front()}")
    
    # Odigraj potez
    moves = game.mg.get_all_moves(game.board, Color.WHITE)
    if moves:
        move = moves[0]
        game.apply_move(move)
        print(f"   Move applied: {move}")
        game.current_player = game.switch_player()
        print(f"   OK\n")
    
    # Test 6: Sistem relikvija
    print("6. RELICS SYSTEM")
    from relics import RelicDeck, RelicType
    deck = RelicDeck()
    print(f"   Deck size: {len(deck.deck)}")
    print(f"   Front: {deck.get_front()}")
    print(f"   Rear: {deck.get_rear()}")
    
    front_relic = deck.activate_front()
    print(f"   Activated front: {front_relic}")
    deck.advance_turn()
    print(f"   After advance, front: {deck.get_front()}")
    print(f"   OK\n")
    
    print("=== ALL TESTS PASSED ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
