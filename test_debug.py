import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_loop import GameLoop
from piece import Color

print("=== DEBUG TEST ===\n")

try:
    game = GameLoop(ai_color=Color.BLACK)
    print("1. GameLoop created")
    
    # Igraj dok ne nastane problem
    for turn in range(12):
        print(f"\nTurn {turn+1}:")
        print(f"  Current player: {game.current_player}")
        
        moves = game.mg.get_all_moves(game.board, game.current_player)
        print(f"  Available moves: {len(moves)}")
        
        if not moves:
            print(f"  No moves - Game Over!")
            break
        
        # Uzmi prvi potez za svakog igrača
        move = moves[0]
        print(f"  Move: {move}")
        
        game.apply_move(move)
        print(f"  Move applied")
        
        game.current_player = game.switch_player()
        print(f"  Next player: {game.current_player}")
    
    print("\n=== TEST COMPLETE ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
