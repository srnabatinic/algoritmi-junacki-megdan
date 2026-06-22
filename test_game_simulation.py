# test_game_simulation.py

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_loop import GameLoop
from piece import Color

print("=== GAME SIMULATION TEST ===\n")

try:
    game = GameLoop(ai_color=Color.BLACK)
    print("Game initialized - WHITE vs AI(BLACK)\n")
    
    start_time = time.time()
    max_time = 20  # 20 seconds timeout
    
    # Play 10 moves
    for turn in range(10):
        elapsed = time.time() - start_time
        if elapsed > max_time:
            print(f"TIMEOUT after {elapsed:.1f}s - stopping")
            break
        
        moves = game.mg.get_all_moves(game.board, game.current_player)
        
        if not moves:
            print(f"Turn {turn+1}: No moves available - Game Over!")
            break
        
        if game.current_player == Color.BLACK:
            # AI chooses with 3 second timeout
            turn_start = time.time()
            move = game.minimax.get_best_move(game.board, game.current_player)
            turn_time = time.time() - turn_start
            player = f"BLACK(AI)[{turn_time:.1f}s]"
        else:
            # Take first move
            move = moves[0]
            player = "WHITE(HUMAN)"
        
        if move:
            from_r, from_c = game.board.index_to_row_col(move.from_idx)
            to_r, to_c = game.board.index_to_row_col(move.to_idx)
            from_sq = f"{'abcdefgh'[from_c]}{8-from_r}"
            to_sq = f"{'abcdefgh'[to_c]}{8-to_r}"
            eat = f" x{len(move.captured)}" if move.captured else ""
            
            print(f"Turn {turn+1} ({player}): {from_sq} -> {to_sq}{eat}")
            
            game.apply_move(move)
            game.current_player = game.switch_player()
        else:
            print(f"Turn {turn+1}: No move found!")
            break
        
    total_time = time.time() - start_time
    print(f"\n=== SIMULATION COMPLETE ({total_time:.1f}s total) ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
