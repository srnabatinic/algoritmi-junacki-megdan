import time
from collections import deque

from board import Board
from piece import Color, PieceType
from move_generator import MoveGenerator
from game_state import GameState
from history_tree import HistoryTree
from display import Display
from heusteric import Heuristic
from minimax import Minimax
from relics import RelicDeck, RelicType, RelicEffect, get_relic_duration
from board_events import BrazdeLocations, RelicActivationSystem


class GameLoop:

    def __init__(self, ai_color=Color.BLACK):
        self.board = Board()
        self.board.setup_initial_position()
        self.mg = MoveGenerator()
        self.heuristic = Heuristic()
        self.minimax = Minimax()
        self.display = Display(self.board)
        self.current_player = Color.WHITE
        self.ai_color = ai_color
        self.no_progress_counter = 0
        self.move_number = 1
        self.relic_deck = RelicDeck()
        self.relic_system = RelicActivationSystem(self.relic_deck)
        initial_state = GameState(
            board=self.board.copy(),
            current_player=self.current_player,
            no_progress_counter=self.no_progress_counter,
            drum_snapshot=list(self.relic_deck.deck),
        )
        self.history = HistoryTree(initial_state)

    # ------------------------------------------------------------------ #
    #  Glavni tok igre                                                   #
    # ------------------------------------------------------------------ #

    def run(self):
        while True:
            # Na početku svakog poteza nova relikvija ulazi u Deque
            self.relic_deck.advance_turn()

            moves = self.mg.get_all_moves(self.board, self.current_player)

            if self.is_game_over(moves):
                break

            highlight_map = {m.to_idx: i + 1 for i, m in enumerate(moves)}
            self._render(moves, highlight_map)

            if self.current_player == self.ai_color:
                print("  AI razmišlja...")
                move = self.minimax.get_best_move(self.board, self.current_player)
            else:
                move = self.get_player_move(moves)
                if move is None:  # Igrač zatražio undo
                    if self._perform_undo():
                        continue
                    # Ako nema šta da se poništi, pitaj ponovo
                    move = self.get_player_move(moves)

            if move:
                self.display.log_move(self.board, move, self.current_player, self.move_number)
                self.apply_move(move)
                # Otkucaj efekte na protivnikovim figurama (one su "opponent" za ovaj potez)
                self.tick_opponent_pieces()
                self.save_state(move)
                self.move_number += 1
                self.current_player = self.switch_player()

        self.offer_replay()

    def _render(self, moves, highlight_map):
        """Prikaži tablu i informacije; dodaj Carev drum ispod."""
        self.display.render_full(
            self.board, self.current_player,
            self.heuristic, moves, highlight_map,
        )
        self._print_drum_status()

    def _print_drum_status(self):
        deck_list = list(self.relic_deck.deck)
        deck_str = " | ".join(r.value for r in deck_list) if deck_list else "prazan"
        print(f"  CAREV DRUM  [FRONT] {deck_str} [REAR]")
        print()

    # ------------------------------------------------------------------ #
    #  Unos igrača                                                       #
    # ------------------------------------------------------------------ #

    def get_player_move(self, moves):
        while True:
            try:
                raw = input(
                    f"  Potez (1-{len(moves)}), 'u' = poništi, 'q' = izlaz: "
                ).strip().lower()
                if raw == 'u':
                    return None
                if raw == 'q':
                    print("  Izlaz iz igre.")
                    raise SystemExit(0)
                idx = int(raw) - 1
                if 0 <= idx < len(moves):
                    return moves[idx]
                print(f"  Unesite broj od 1 do {len(moves)}.")
            except ValueError:
                print("  Neispravan unos.")

    # ------------------------------------------------------------------ #
    #  Primena poteza                                                    #
    # ------------------------------------------------------------------ #

    def apply_move(self, move):
        pieces_before = sum(1 for p in self.board.board if p)

        # Brišemo captured PRE pomeranja — bitno za Topuz gde je to_idx == captured[0]
        if move.captured:
            for idx in move.captured:
                self.board.remove_piece(idx)

        piece = self.board.get_piece(move.from_idx)
        self.board.remove_piece(move.from_idx)
        self.board.set_piece(move.to_idx, piece)

        pieces_after = sum(1 for p in self.board.board if p)
        promoted = self.check_promotion(move.to_idx)
        self.update_no_progress(pieces_before, pieces_after, promoted)

        # Proveri Brazdu i ponudi aktivaciju relikvije
        self.check_brazda(move, piece)

    def check_promotion(self, index):
        if self.board.is_valid_index(index):
            piece = self.board.get_piece(index)
            if piece and piece.type == PieceType.JUNAK:
                row, _ = self.board.index_to_row_col(index)
                if (piece.color == Color.WHITE and row == 0) or \
                   (piece.color == Color.BLACK and row == 7):
                    piece.promote()
                    return True
        return False

    # ------------------------------------------------------------------ #
    #  Brazda i relikvije                                                #
    # ------------------------------------------------------------------ #

    def check_brazda(self, move, piece):
        """Ako figura stane na Brazdu, igrač (ili AI) bira i aktivira relikviju."""
        if not BrazdeLocations.is_brazda(move.to_idx, self.board):
            return

        front_relic = self.relic_deck.get_front()
        rear_relic = self.relic_deck.get_rear()

        if not front_relic and not rear_relic:
            return

        print(f"\n  *** BRAZDA! Figura je zаorala na Carевom Drumu. ***")

        if self.current_player == self.ai_color:
            # AI uvek uzima novu (front) relikviju
            chosen = self.relic_deck.activate_front()
        else:
            chosen = self._ask_relic_choice(front_relic, rear_relic)

        if chosen:
            self._apply_relic_effect(piece, chosen, move.to_idx)
            is_marko = self.relic_system.check_marko_promotion(piece)
            print(f"  Relikvija aktivirana: {chosen.value}")
            if is_marko:
                print("  *** MARKO KRALJEVIC — figura dobija Nepоkolebljivost! ***")

    def _ask_relic_choice(self, front_relic, rear_relic):
        """Pita igrača da izabere front ili rear relikviju."""
        print("  Dostupne relikvije:")
        if front_relic:
            print(f"    1. FRONT (nova)  : {front_relic.value}")
        if rear_relic:
            print(f"    2. REAR  (stara) : {rear_relic.value}")

        while True:
            choice = input("  Izaberite (1=front, 2=rear): ").strip()
            if choice == '1' and front_relic:
                return self.relic_deck.activate_front()
            if choice == '2' and rear_relic:
                return self.relic_deck.activate_rear()
            print("  Unesite 1 ili 2.")

    def _apply_relic_effect(self, piece, relic_type, piece_idx):
        """Primeni efekat relikvije prema tipu."""
        # Evidentiramo na figuri za Marko provjeru
        piece.relics.add(relic_type)
        self.relic_system.activate_relic_on_piece(piece, relic_type)

        if relic_type == RelicType.MESINA_RUJNOG_VINA:
            # Koleb se primenjuje na najbližeg neprijatelja; Marko Kraljević je imun
            target = self._find_nearest_enemy(piece_idx, piece.color)
            if target and not target.is_marko():
                duration = get_relic_duration(relic_type, is_marko=False)
                target.active_relics[relic_type] = RelicEffect(relic_type, duration)
                print("  Najbliži protivnik pogođen koleb efektom!")
            elif target and target.is_marko():
                print("  Marko Kraljević je nepokolebljiv — Mesina nema efekta!")

        elif relic_type == RelicType.TRI_TOVARA_BLAGA:
            # Krunjenje — trenutna promocija
            piece.activate_relic(relic_type)
            piece.promote()

        else:
            # Toka od čelika, Topuz, Šarac — efekat na samoj figuri
            piece.activate_relic(relic_type)

    def _find_nearest_enemy(self, from_idx, own_color):
        """Vraća najbližu neprijateljsku figuru (Manhattan distanca)."""
        from_row, from_col = self.board.index_to_row_col(from_idx)
        enemy_color = Color.BLACK if own_color == Color.WHITE else Color.WHITE
        nearest, min_dist = None, float('inf')
        for idx, ep in self.board.get_all_pieces(enemy_color):
            e_row, e_col = self.board.index_to_row_col(idx)
            dist = abs(e_row - from_row) + abs(e_col - from_col)
            if dist < min_dist:
                min_dist, nearest = dist, ep
        return nearest

    # ------------------------------------------------------------------ #
    #  Ticking efekata                                                   #
    # ------------------------------------------------------------------ #

    def tick_opponent_pieces(self):
        """
        Nakon poteza tekućeg igrača, otkucavamo efekte na protivnikovim figurama.
        Shema: Toka (na sopstvenoj figuri, duration=1) preživi sopstveni potez,
        ističe krajem protivnikovog poteza. Mesina (na neprijatelju, duration=3)
        biva odmah tikana (->2), zatim tikana posle 2 protivnikova poteza.
        """
        opponent = self.switch_player()
        for _, ep in self.board.get_all_pieces(opponent):
            ep.tick_effects()

    # ------------------------------------------------------------------ #
    #  Undo                                                              #
    # ------------------------------------------------------------------ #

    def _perform_undo(self):
        """Poništi poslednji odigrani polu-potez."""
        if self.history.current_node is self.history.root:
            print("  Nema poteza za poništavanje.")
            return False

        self.history.undo()
        prev = self.history.current_node.state

        self.board = prev.board.copy()
        self.current_player = prev.current_player
        self.no_progress_counter = prev.no_progress_counter

        if prev.drum_snapshot:
            self.relic_deck.deck = deque(prev.drum_snapshot)

        self.move_number = max(1, self.move_number - 1)
        print("  Potez je poništen.")
        return True

    # ------------------------------------------------------------------ #
    #  Čuvanje stanja                                                    #
    # ------------------------------------------------------------------ #

    def save_state(self, move):
        new_state = GameState(
            board=self.board.copy(),
            current_player=self.current_player,
            no_progress_counter=self.no_progress_counter,
            move=move,
            drum_snapshot=list(self.relic_deck.deck),
        )
        self.history.add_move(new_state)

    # ------------------------------------------------------------------ #
    #  Kraj igre i reprodukcija                                          #
    # ------------------------------------------------------------------ #

    def is_game_over(self, moves):
        if self.no_progress_counter >= 40:
            self.display.render_draw()
            return True
        if not moves:
            winner = self.switch_player()
            self.display.render_game_over(winner)
            return True
        return False

    def offer_replay(self):
        try:
            ans = input("\n  Reprodukovati partiju? (d/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if ans == 'd':
            self.replay_game()

    def replay_game(self):
        """
        Reprodukuje sve odigrane poteze iz stabla istorije (DFS),
        uključujući poništene poteze kako bi se videlo puno grananje.
        """
        paths = self.history.get_full_history()
        print(f"\n  Pronađeno {len(paths)} putanja u stablu odluka.\n")

        for path_idx, path in enumerate(paths):
            if len(paths) > 1:
                print(f"  === Putanja {path_idx + 1}/{len(paths)} ===\n")
            total = len(path) - 1  # korak 0 je početno stanje
            for step_idx, state in enumerate(path):
                self.display.render_replay_step(state.board, step_idx, total)
                if step_idx < total:
                    time.sleep(1.0)

        print("\n  Reprodukcija završena.")

    # ------------------------------------------------------------------ #
    #  Pomoćne metode                                                    #
    # ------------------------------------------------------------------ #

    def update_no_progress(self, pieces_before, pieces_after, promoted):
        if promoted or pieces_before != pieces_after:
            self.no_progress_counter = 0
        else:
            self.no_progress_counter += 1

    def switch_player(self):
        return Color.BLACK if self.current_player == Color.WHITE else Color.WHITE
