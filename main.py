from game_loop import GameLoop
from piece import Color

def main():
    print("\n" + "═"*40)
    print("       JUNAČKI MEGDAN")
    print("  Strateška igra zasnovana na srpskoj epici")
    print("═"*40)
    print()
    print("  1. Igraj kao Beli (AI igra Crnim)")
    print("  2. Igraj kao Crni (AI igra Belim)")
    print("  3. AI vs AI (gledaj partiju)")
    print()
    
    while True:
        choice = input("  Izbor (1/2/3): ").strip()
        if choice in ("1", "2", "3"):
            break
        print("  Unesite 1, 2 ili 3.")
    
    if choice == "1":
        game = GameLoop(ai_color=Color.BLACK)
    elif choice == "2":
        game = GameLoop(ai_color=Color.WHITE)
    else:
        # AI vs AI — oba su AI
        game = GameLoop(ai_color=Color.WHITE)
        game.ai_color_both = True
        # Override get_player_move da nikad ne pita
        original_run = game.run
        def ai_vs_ai_run():
            from move_generator import MoveGenerator
            while True:
                moves = game.mg.get_all_moves(game.board, game.current_player)
                if game.is_game_over(moves):
                    break
                highlight_map = {m.to_idx: i+1 for i, m in enumerate(moves)}
                game.display.render_full(
                    game.board, game.current_player,
                    game.heuristic, moves, highlight_map
                )
                print(f"  AI ({game.current_player.value}) razmišlja...")
                move = game.minimax.get_best_move(game.board, game.current_player)
                if move:
                    game.display.log_move(game.board, move, game.current_player, game.move_number)
                    game.apply_move(move)
                    game.save_state(move)
                    game.move_number += 1
                    game.current_player = game.switch_player()
        game.run = ai_vs_ai_run
    
    game.run()
    
    input("\n  Pritisni Enter za izlaz...")

if __name__ == "__main__":
    main()