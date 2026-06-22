# quick_test.py - Test relics system

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game_loop import GameLoop
from piece import Color

print("=== JUNACKI MEGDAN - RELIC SYSTEM TEST ===\n")

try:
    # Initialize game
    game = GameLoop(ai_color=Color.BLACK)
    print("1. GameLoop created - OK")
    print("2. Relic deck initialized - OK")
    
    # Run a few turns
    moves = game.mg.get_all_moves(game.board, Color.WHITE)
    print(f"3. Got {len(moves)} moves for White - OK")
    
    # Make first move
    if moves:
        move = moves[0]
        print(f"4. Making first move: {move}")
        game.apply_move(move)
        print("5. Move applied - OK")
        
        # Advance turn (which adds new relic to deck)
        game.relic_deck.advance_turn()
        print("6. Relic deck advanced - OK")
        
        # Check if any piece got a relic
        active_relics_count = 0
        for idx, piece in game.board.get_all_pieces(Color.WHITE):
            if piece.get_active_relics():
                active_relics_count += 1
        
        print(f"7. White pieces with relics: {active_relics_count}")
        print("\n=== SYSTEM OPERATIONAL ===")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
