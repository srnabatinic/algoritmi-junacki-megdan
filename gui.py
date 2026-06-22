import tkinter as tk
from tkinter import messagebox
from collections import deque

from board import Board
from move_generator import MoveGenerator
from minimax import Minimax
from heusteric import Heuristic
from piece import Color, PieceType
from relics import RelicDeck, RelicType, RelicEffect, get_relic_duration
from board_events import BrazdeLocations, RelicActivationSystem
from history_tree import HistoryTree
from game_state import GameState

CELL_SIZE = 70
BOARD_SIZE = 8

PIECE_STYLES = {
    (Color.WHITE, PieceType.JUNAK):          {"fill": "#f8f1d4", "outline": "#7a5c2c", "text": "J",  "text_color": "#3d2500"},
    (Color.WHITE, PieceType.KRALJEVIC):      {"fill": "#ffe4b5", "outline": "#8b5a2b", "text": "K",  "text_color": "#4b2e1e"},
    (Color.WHITE, PieceType.MARKO_KRALJEVIC):{"fill": "#ffd700", "outline": "#8b6508", "text": "MK", "text_color": "#2f1e00"},
    (Color.BLACK, PieceType.JUNAK):          {"fill": "#3b3b3b", "outline": "#111111", "text": "j",  "text_color": "#ffffff"},
    (Color.BLACK, PieceType.KRALJEVIC):      {"fill": "#222b40", "outline": "#0f172a", "text": "K",  "text_color": "#f8f8ff"},
    (Color.BLACK, PieceType.MARKO_KRALJEVIC):{"fill": "#5b1c1c", "outline": "#2a0d0d", "text": "mk", "text_color": "#fff5f0"},
}

RELIC_ABBREV = {
    RelicType.TOKA_OD_CELIKA:    "Tk",
    RelicType.MESINA_RUJNOG_VINA:"Ms",
    RelicType.TOPUZ:             "Tp",
    RelicType.SARAC:             "Sr",
    RelicType.TRI_TOVARA_BLAGA:  "Bl",
}

RELIC_DESC = {
    RelicType.TOKA_OD_CELIKA:    "Oklop — blokira jedno jedenje",
    RelicType.MESINA_RUJNOG_VINA:"Koleb — najblizi neprijatelj ne moze da skace (2 poteza)",
    RelicType.TOPUZ:             "Razorni udarac — direktno jedenje bez preskakanja",
    RelicType.SARAC:             "Sarcev skok — jednom preskocci sopstvenu figuru",
    RelicType.TRI_TOVARA_BLAGA:  "Krunjenje — trenutna promocija u Kraljevica",
}


# ────────────────────────────────────────────────────────────────────────── #
#  Pomocna klasa: dijalog za izbor relikvije                                 #
# ────────────────────────────────────────────────────────────────────────── #

class RelicChoiceDialog:
    """Modalni dijalog prikazan kada figura stane na Brazdu."""

    def __init__(self, parent, front_relic, rear_relic, relic_deck):
        self.result = None
        self.relic_deck = relic_deck

        dlg = tk.Toplevel(parent)
        dlg.title("Brazda — Carev Drum")
        dlg.resizable(False, False)
        dlg.wait_visibility()  # Sačekaj da prozor bude vidljiv pre grab_set
        dlg.grab_set()
        dlg.focus_set()

        tk.Label(
            dlg,
            text="Figura je zaorala na Carevom Drumu!\nIzaberite relikviju:",
            font=("Segoe UI", 12, "bold"),
            pady=8,
        ).pack(padx=24)

        if front_relic:
            desc = RELIC_DESC.get(front_relic, "")
            btn_text = f"FRONT (nova):\n{front_relic.value}\n{desc}"
            tk.Button(
                dlg, text=btn_text,
                command=lambda: self._pick(dlg, "front"),
                width=36, height=3,
                bg="#c8e8c0", font=("Segoe UI", 10),
            ).pack(pady=6, padx=24)

        if rear_relic:
            desc = RELIC_DESC.get(rear_relic, "")
            btn_text = f"REAR (stara):\n{rear_relic.value}\n{desc}"
            tk.Button(
                dlg, text=btn_text,
                command=lambda: self._pick(dlg, "rear"),
                width=36, height=3,
                bg="#c0d0e8", font=("Segoe UI", 10),
            ).pack(pady=6, padx=24)

        dlg.wait_window()

    def _pick(self, dlg, side):
        if side == "front":
            self.result = self.relic_deck.activate_front()
        else:
            self.result = self.relic_deck.activate_rear()
        dlg.destroy()


# ────────────────────────────────────────────────────────────────────────── #
#  Pomocna klasa: prozor za reprodukciju                                     #
# ────────────────────────────────────────────────────────────────────────── #

class ReplayWindow:
    """DFS obilazak stabla istorije, prikaz svakog stanja na tabli."""

    def __init__(self, parent, paths):
        self.paths = [p for p in paths if len(p) > 1]
        if not self.paths:
            messagebox.showinfo("Reprodukcija", "Nema poteza za reprodukciju.")
            return

        self.path_idx = 0
        self.step = 0
        self._auto_id = None
        self.auto_running = False

        win = tk.Toplevel(parent)
        win.title("Reprodukcija partije")
        win.resizable(False, False)
        self.win = win

        self.canvas = tk.Canvas(win,
                                width=CELL_SIZE * BOARD_SIZE,
                                height=CELL_SIZE * BOARD_SIZE)
        self.canvas.pack()

        info = tk.Frame(win)
        info.pack(fill="x", padx=8, pady=2)
        self.step_label = tk.Label(info, text="", font=("Segoe UI", 10))
        self.step_label.pack(side="left")
        self.path_label = tk.Label(info, text="", font=("Segoe UI", 10), fg="#666")
        self.path_label.pack(side="right")

        nav = tk.Frame(win)
        nav.pack(pady=4)
        tk.Button(nav, text="|<< Pocetak",   command=self.go_first, width=12).grid(row=0, column=0, padx=2)
        tk.Button(nav, text="< Prethodni",   command=self.go_prev,  width=12).grid(row=0, column=1, padx=2)
        tk.Button(nav, text="Sledeci >",     command=self.go_next,  width=12).grid(row=0, column=2, padx=2)
        tk.Button(nav, text="Kraj >>|",      command=self.go_last,  width=12).grid(row=0, column=3, padx=2)

        auto_row = tk.Frame(win)
        auto_row.pack(pady=2)
        self.auto_btn = tk.Button(auto_row, text="Pokreni auto-prikaz",
                                  command=self.toggle_auto, width=20)
        self.auto_btn.pack(side="left", padx=4)

        if len(self.paths) > 1:
            branch = tk.Frame(win)
            branch.pack(pady=2)
            tk.Label(branch, text="Grana:").pack(side="left")
            tk.Button(branch, text="< Preth.", command=self.prev_path, width=9).pack(side="left", padx=2)
            tk.Button(branch, text="Sled. >",  command=self.next_path, width=9).pack(side="left", padx=2)

        self._render()

    # --- navigation ---

    def _cur_path(self):
        return self.paths[self.path_idx]

    def go_first(self):
        self.step = 0
        self._render()

    def go_last(self):
        self.step = len(self._cur_path()) - 1
        self._render()

    def go_prev(self):
        if self.step > 0:
            self.step -= 1
            self._render()

    def go_next(self):
        if self.step < len(self._cur_path()) - 1:
            self.step += 1
            self._render()

    def prev_path(self):
        self.path_idx = (self.path_idx - 1) % len(self.paths)
        self.step = 0
        self._render()

    def next_path(self):
        self.path_idx = (self.path_idx + 1) % len(self.paths)
        self.step = 0
        self._render()

    def toggle_auto(self):
        if self.auto_running:
            self.auto_running = False
            self.auto_btn.config(text="Pokreni auto-prikaz")
            if self._auto_id:
                self.win.after_cancel(self._auto_id)
        else:
            self.auto_running = True
            self.auto_btn.config(text="Zaustavi auto-prikaz")
            self._auto_step()

    def _auto_step(self):
        if not self.auto_running:
            return
        if self.step < len(self._cur_path()) - 1:
            self.step += 1
            self._render()
            self._auto_id = self.win.after(1000, self._auto_step)
        else:
            self.auto_running = False
            self.auto_btn.config(text="Pokreni auto-prikaz")

    # --- drawing ---

    def _render(self):
        path = self._cur_path()
        state = path[self.step]
        board = state.board

        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                sq = "#8c5c2c" if (row + col) % 2 == 1 else "#d6b57f"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=sq, outline="#4a3822")
                idx = board.row_col_to_index(row, col)
                if idx is None:
                    continue
                if board.is_brazda(idx):
                    self.canvas.create_rectangle(x1+3, y1+3, x2-3, y2-3,
                                                 outline="#ffd700", width=3)
                piece = board.get_piece(idx)
                if piece:
                    style = PIECE_STYLES.get(
                        (piece.color, piece.type),
                        {"fill": "#999", "outline": "#000", "text": "?", "text_color": "#000"},
                    )
                    self.canvas.create_oval(x1+10, y1+10, x2-10, y2-10,
                                            fill=style["fill"], outline=style["outline"], width=2)
                    self.canvas.create_text((x1+x2)//2, (y1+y2)//2,
                                            text=style["text"], fill=style["text_color"],
                                            font=("Segoe UI", 16, "bold"))

        total = len(path) - 1
        self.step_label.config(text=f"Potez {self.step} / {total}")
        self.path_label.config(text=f"Putanja {self.path_idx+1} / {len(self.paths)}")


# ────────────────────────────────────────────────────────────────────────── #
#  Glavna klasa                                                              #
# ────────────────────────────────────────────────────────────────────────── #

class GuiGame:

    def __init__(self, root, ai_color=Color.BLACK):
        self.root = root
        self.ai_color = ai_color
        self.board = Board()
        self.move_generator = MoveGenerator()
        self.minimax = Minimax()
        self.heuristic = Heuristic()
        self.selected_index = None
        self.legal_moves = []
        self.move_log = []
        self.no_progress_counter = 0
        self.current_player = Color.WHITE
        self.relic_deck = RelicDeck()
        self.relic_system = RelicActivationSystem(self.relic_deck)
        self.history = None
        self._setup_ui()
        self.reset_board()

    # ------------------------------------------------------------------ #
    #  UI setup                                                          #
    # ------------------------------------------------------------------ #

    def _setup_ui(self):
        self.root.title("JUNACKI MEGDAN - GUI")
        self.root.resizable(False, False)

        # --- Canvas (levo) ---
        self.canvas = tk.Canvas(
            self.root,
            width=CELL_SIZE * BOARD_SIZE,
            height=CELL_SIZE * BOARD_SIZE,
        )
        self.canvas.grid(row=0, column=0, rowspan=20, padx=(10, 0), pady=10)
        self.canvas.bind("<Button-1>", self._on_click)

        right = tk.Frame(self.root, width=310)
        right.grid(row=0, column=1, sticky="nw", padx=10, pady=10)

        # Status
        self.status_label = tk.Label(
            right, text="", font=("Segoe UI", 11, "bold"),
            anchor="w", justify="left", width=36,
        )
        self.status_label.pack(anchor="w", pady=(0, 4))

        # Broj figura po igracu
        self.pieces_label = tk.Label(
            right, text="", font=("Segoe UI", 10),
            anchor="w", justify="left", width=36,
        )
        self.pieces_label.pack(anchor="w", pady=(0, 4))

        # Carev Drum panel
        drum_frame = tk.LabelFrame(right, text="  Carev Drum  ",
                                   font=("Segoe UI", 10, "bold"),
                                   padx=6, pady=4)
        drum_frame.pack(fill="x", pady=(0, 6))
        self._drum_labels = []
        for i in range(5):
            bg = "#f0e8d0" if i % 2 == 0 else "#e8d8b8"
            lbl = tk.Label(drum_frame, text="—", font=("Segoe UI", 9),
                           anchor="w", width=34, bg=bg)
            lbl.pack(fill="x", pady=1)
            self._drum_labels.append(lbl)
        tk.Label(drum_frame, text="FRONT (nova) ↑              ↓ REAR (stara)",
                 font=("Segoe UI", 7, "italic"), fg="#666").pack()

        # Aktivni efekti
        self.effects_label = tk.Label(
            right, text="", font=("Segoe UI", 9),
            anchor="nw", justify="left", width=36, fg="#2a2a6a",
        )
        self.effects_label.pack(anchor="w", pady=(0, 4))

        # Log poteza
        self.log_label = tk.Label(
            right, text="", font=("Courier", 9),
            anchor="nw", justify="left", width=36,
        )
        self.log_label.pack(anchor="w", pady=(0, 4))

        # Dugmici
        btn = tk.Frame(right)
        btn.pack(anchor="w", pady=(4, 0))

        tk.Button(btn, text="Nova igra",      command=self.reset_board,   width=15).grid(row=0, column=0, pady=3)
        tk.Button(btn, text="AI kao Beli",    command=self._set_ai_white, width=15).grid(row=1, column=0, pady=3)
        tk.Button(btn, text="AI kao Crni",    command=self._set_ai_black, width=15).grid(row=2, column=0, pady=3)

        self.undo_btn = tk.Button(
            btn, text="Ponisti potez (Undo)",
            command=self.undo_move,
            width=15, bg="#d4a0a0", activebackground="#c08080",
        )
        self.undo_btn.grid(row=3, column=0, pady=3)

        tk.Button(
            btn, text="Reprodukcija",
            command=self.show_replay,
            width=15, bg="#a0a0d4", activebackground="#8080c0",
        ).grid(row=4, column=0, pady=3)

    # ------------------------------------------------------------------ #
    #  Reset / nova igra                                                 #
    # ------------------------------------------------------------------ #

    def reset_board(self):
        self.board = Board()
        self.board.setup_initial_position()
        self.current_player = Color.WHITE
        self.selected_index = None
        self.legal_moves = []
        self.move_log = []
        self.no_progress_counter = 0
        self.relic_deck = RelicDeck()
        self.relic_system = RelicActivationSystem(self.relic_deck)

        initial_state = GameState(
            board=self.board.copy(),
            current_player=self.current_player,
            no_progress_counter=self.no_progress_counter,
            drum_snapshot=(list(self.relic_deck.deck), self.relic_deck.cycle_index),
        )
        self.history = HistoryTree(initial_state)

        # Pripremi deck za prvi potez
        self.relic_deck.advance_turn()
        self._update_display()

        if self.current_player == self.ai_color:
            self.root.after(300, self._ai_turn)

    def _set_ai_white(self):
        self.ai_color = Color.WHITE
        self.reset_board()

    def _set_ai_black(self):
        self.ai_color = Color.BLACK
        self.reset_board()

    # ------------------------------------------------------------------ #
    #  Klik na tablu                                                     #
    # ------------------------------------------------------------------ #

    def _on_click(self, event):
        if self.current_player == self.ai_color:
            return
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        index = self.board.row_col_to_index(row, col)
        if index is None:
            return

        piece = self.board.get_piece(index)

        if self.selected_index is None:
            if piece and piece.color == self.current_player:
                self._select(index)
            return

        move = self._find_move(self.selected_index, index)
        if move:
            self._apply_move(move)
            return

        if piece and piece.color == self.current_player:
            self._select(index)
        else:
            self.selected_index = None
            self.legal_moves = []
            self._update_display()

    def _select(self, index):
        self.selected_index = index
        all_moves = self.move_generator.get_all_moves(self.board, self.current_player)
        self.legal_moves = [m for m in all_moves if m.from_idx == index]
        self._update_display()

    def _find_move(self, from_idx, to_idx):
        for m in self.legal_moves:
            if m.from_idx == from_idx and m.to_idx == to_idx:
                return m
        return None

    # ------------------------------------------------------------------ #
    #  AI potez                                                          #
    # ------------------------------------------------------------------ #

    def _ai_turn(self):
        moves = self.move_generator.get_all_moves(self.board, self.current_player)
        if not moves:
            self._check_game_over()
            return
        move = self.minimax.get_best_move(self.board, self.current_player)
        if not move:
            move = moves[0]
        self._apply_move(move)

    # ------------------------------------------------------------------ #
    #  Primena poteza                                                    #
    # ------------------------------------------------------------------ #

    def _apply_move(self, move):
        pieces_before = sum(1 for p in self.board.board if p)

        # Brišemo captured PRE pomeranja — bitno za Topuz gde je to_idx == captured[0]
        if move.captured:
            for idx in move.captured:
                self.board.remove_piece(idx)

        piece = self.board.get_piece(move.from_idx)
        self.board.remove_piece(move.from_idx)
        self.board.set_piece(move.to_idx, piece)

        pieces_after = sum(1 for p in self.board.board if p)
        promoted = self._check_promotion(move.to_idx)
        self._update_no_progress(pieces_before, pieces_after, promoted)

        # Brazda provera — moze prikazati dijalog za izbor relikvije
        self._check_brazda(move, piece)

        # Otkucaj efekte na protivnikovim figurama
        self._tick_opponent_pieces()

        # Sacuvaj stanje u stablo istorije (pre advance_turn)
        self._save_state(move)

        self._log_move(move, self.current_player)
        self.selected_index = None
        self.legal_moves = []
        self.current_player = self.switch_player()

        # Pripremi deck za sledeci potez
        self.relic_deck.advance_turn()

        self._update_display()

        if self._check_game_over():
            return
        if self.current_player == self.ai_color:
            self.root.after(300, self._ai_turn)

    def _check_promotion(self, index):
        piece = self.board.get_piece(index)
        if piece and piece.type == PieceType.JUNAK:
            row, _ = self.board.index_to_row_col(index)
            if (piece.color == Color.WHITE and row == 0) or \
               (piece.color == Color.BLACK and row == 7):
                piece.promote()
                return True
        return False

    def _update_no_progress(self, before, after, promoted):
        if promoted or before != after:
            self.no_progress_counter = 0
        else:
            self.no_progress_counter += 1

    # ------------------------------------------------------------------ #
    #  Brazda i relikvije                                                #
    # ------------------------------------------------------------------ #

    def _check_brazda(self, move, piece):
        if not BrazdeLocations.is_brazda(move.to_idx, self.board):
            return

        front = self.relic_deck.get_front()
        rear  = self.relic_deck.get_rear()
        if not front and not rear:
            return

        if self.current_player == self.ai_color:
            # AI uvek uzima novu (front) relikviju
            chosen = self.relic_deck.activate_front()
        else:
            dialog = RelicChoiceDialog(self.root, front, rear, self.relic_deck)
            chosen = dialog.result

        if chosen:
            self._apply_relic_effect(piece, chosen, move.to_idx)
            is_marko = self.relic_system.check_marko_promotion(piece)
            if is_marko:
                messagebox.showinfo(
                    "Marko Kraljevic!",
                    "Figura je skupila sve 4 relikvije!\n\n"
                    "Postaje MARKO KRALJEVIC!\n"
                    "(Nepokolebljivost aktivirana)",
                )

    def _apply_relic_effect(self, piece, relic_type, piece_idx):
        """Primeni efekat relikvije prema tipu."""
        piece.relics.add(relic_type)
        self.relic_system.activate_relic_on_piece(piece, relic_type)

        if relic_type == RelicType.MESINA_RUJNOG_VINA:
            # Koleb se primenjuje na najblizeg neprijatelja; Marko je imun
            target = self._find_nearest_enemy(piece_idx, piece.color)
            if target and not target.is_marko():
                dur = get_relic_duration(relic_type, is_marko=False)
                target.active_relics[relic_type] = RelicEffect(relic_type, dur)
        elif relic_type == RelicType.TRI_TOVARA_BLAGA:
            piece.activate_relic(relic_type)
            piece.promote()
        else:
            piece.activate_relic(relic_type)

    def _find_nearest_enemy(self, from_idx, own_color):
        from_row, from_col = self.board.index_to_row_col(from_idx)
        enemy_color = Color.BLACK if own_color == Color.WHITE else Color.WHITE
        nearest, min_d = None, float('inf')
        for idx, ep in self.board.get_all_pieces(enemy_color):
            r, c = self.board.index_to_row_col(idx)
            d = abs(r - from_row) + abs(c - from_col)
            if d < min_d:
                min_d, nearest = d, ep
        return nearest

    def _tick_opponent_pieces(self):
        """Otkucaj aktivne efekte na figurama protivnika (osobe koja ce igrati sledece)."""
        opponent = self.switch_player()
        for _, ep in self.board.get_all_pieces(opponent):
            ep.tick_effects()

    # ------------------------------------------------------------------ #
    #  Istorija / Undo                                                   #
    # ------------------------------------------------------------------ #

    def _save_state(self, move):
        state = GameState(
            board=self.board.copy(),
            current_player=self.current_player,
            no_progress_counter=self.no_progress_counter,
            move=move,
            drum_snapshot=(list(self.relic_deck.deck), self.relic_deck.cycle_index),
        )
        self.history.add_move(state)

    def undo_move(self):
        """Ponisti poteze dok ne bude na redu ljudski igrac."""
        if self.history.current_node is self.history.root:
            messagebox.showinfo("Undo", "Nema poteza za ponistavanje.")
            return

        # Ponisti bar jedan polu-potez
        self.history.undo()
        self._restore_from_node()

        # Ako je AI na redu, ponisti jos jedan (vrati se na igracevi potez)
        if self.current_player == self.ai_color \
                and self.history.current_node is not self.history.root:
            self.history.undo()
            self._restore_from_node()

        # Pripremi deck za obnovljeni potez
        self.relic_deck.advance_turn()

        self.selected_index = None
        self.legal_moves = []
        self._update_display()

    def _restore_from_node(self):
        state = self.history.current_node.state
        self.board = state.board.copy()
        self.current_player = state.current_player
        self.no_progress_counter = state.no_progress_counter
        if state.drum_snapshot:
            deck_list, cycle_idx = state.drum_snapshot
            self.relic_deck.deck = deque(deck_list)
            self.relic_deck.cycle_index = cycle_idx

    # ------------------------------------------------------------------ #
    #  Reprodukcija                                                      #
    # ------------------------------------------------------------------ #

    def show_replay(self):
        if self.history is None:
            return
        paths = self.history.get_full_history()
        ReplayWindow(self.root, paths)

    # ------------------------------------------------------------------ #
    #  Kraj igre                                                         #
    # ------------------------------------------------------------------ #

    def _check_game_over(self):
        moves = self.move_generator.get_all_moves(self.board, self.current_player)
        if self.no_progress_counter >= 40:
            ans = messagebox.askyesno(
                "Kraj igre",
                "REMI — 40 poteza bez promene.\n\nReprodukovati partiju?",
            )
            if ans:
                self.show_replay()
            return True
        if not moves:
            winner = self.switch_player()
            name = "BELI" if winner == Color.WHITE else "CRNI"
            ans = messagebox.askyesno(
                "Kraj igre",
                f"Pobedio je {name}!\n\nReprodukovati partiju?",
            )
            if ans:
                self.show_replay()
            return True
        return False

    # ------------------------------------------------------------------ #
    #  Iscrtavanje                                                       #
    # ------------------------------------------------------------------ #

    def _draw_board(self):
        self.canvas.delete("all")
        for row in range(8):
            for col in range(8):
                x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE

                sq = "#8c5c2c" if (row + col) % 2 == 1 else "#d6b57f"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=sq, outline="#4a3822")

                idx = self.board.row_col_to_index(row, col)
                if idx is None:
                    continue

                # Brazda — zlatni okvir i oznaka
                if self.board.is_brazda(idx):
                    self.canvas.create_rectangle(x1+3, y1+3, x2-3, y2-3,
                                                 outline="#ffd700", width=3)
                    self.canvas.create_text(x1+6, y1+4, text="B",
                                            fill="#ffd700",
                                            font=("Segoe UI", 8, "bold"),
                                            anchor="nw")

                # Selektovana figura
                if self.selected_index == idx:
                    self.canvas.create_rectangle(x1+3, y1+3, x2-3, y2-3,
                                                 outline="#44ff44", width=4)

                # Moguci potezi
                for m in self.legal_moves:
                    if m.from_idx == self.selected_index and m.to_idx == idx:
                        self.canvas.create_rectangle(x1+3, y1+3, x2-3, y2-3,
                                                     outline="#ffff44", width=4)

                piece = self.board.get_piece(idx)
                if piece:
                    self._draw_piece(piece, x1, y1, x2, y2)

    def _draw_piece(self, piece, x1, y1, x2, y2):
        style = PIECE_STYLES.get(
            (piece.color, piece.type),
            {"fill": "#999", "outline": "#000", "text": "?", "text_color": "#000"},
        )
        self.canvas.create_oval(x1+10, y1+10, x2-10, y2-10,
                                fill=style["fill"], outline=style["outline"], width=2)
        self.canvas.create_text((x1+x2)//2, (y1+y2)//2,
                                text=style["text"], fill=style["text_color"],
                                font=("Segoe UI", 16, "bold"))

        # Aktivni efekti — mali tekst u donjem levom uglu
        active = piece.get_active_relics()
        if active:
            abbr = " ".join(RELIC_ABBREV.get(r, "?") for r in active)
            self.canvas.create_text(x1+4, y2-4, text=abbr,
                                    fill="#cc3300",
                                    font=("Segoe UI", 6, "bold"),
                                    anchor="sw")

    def _update_display(self):
        self._draw_board()

        player_name = "BELI" if self.current_player == Color.WHITE else "CRNI"
        score = self.heuristic.evaluate(self.board, self.current_player)
        moves = self.move_generator.get_all_moves(self.board, self.current_player)
        self.status_label.config(
            text=(
                f"Na potezu: {player_name}    "
                f"Score: {score:+.2f}    "
                f"Poteza: {len(moves)}    "
                f"Bez promene: {self.no_progress_counter}/40"
            )
        )

        # Broj figura po igracu
        white_count = len(self.board.get_all_pieces(Color.WHITE))
        black_count = len(self.board.get_all_pieces(Color.BLACK))
        self.pieces_label.config(
            text=f"Figure — Beli: {white_count}    Crni: {black_count}"
        )

        # Carev Drum panel
        deck = list(self.relic_deck.deck)
        for i, lbl in enumerate(self._drum_labels):
            if i < len(deck):
                prefix = "-> " if i == 0 else ("<- " if i == len(deck) - 1 else "   ")
                lbl.config(text=f"{prefix}{deck[i].value}")
            else:
                lbl.config(text="—")

        # Aktivni efekti na figurama
        lines = []
        for color in (Color.WHITE, Color.BLACK):
            cname = "Beli" if color == Color.WHITE else "Crni"
            for idx, p in self.board.get_all_pieces(color):
                active = p.get_active_relics()
                if active:
                    r, c = self.board.index_to_row_col(idx)
                    sq = f"{'abcdefgh'[c]}{8-r}"
                    effects = ", ".join(RELIC_ABBREV.get(rr, "?") for rr in active)
                    lines.append(f"{cname} {sq}: [{effects}]")
        self.effects_label.config(
            text="Aktivni efekti:\n" + ("\n".join(lines) if lines else "— nema —")
        )

        # Log poteza
        self.log_label.config(
            text="Potezi:\n" + "\n".join(self.move_log[-10:])
        )

    # ------------------------------------------------------------------ #
    #  Pomocne metode                                                    #
    # ------------------------------------------------------------------ #

    def _log_move(self, move, color):
        from_r, from_c = self.board.index_to_row_col(move.from_idx)
        to_r,   to_c   = self.board.index_to_row_col(move.to_idx)
        from_sq = f"{'abcdefgh'[from_c]}{8-from_r}"
        to_sq   = f"{'abcdefgh'[to_c]}{8-to_r}"
        eat  = f" x{len(move.captured)}" if move.captured else ""
        p    = "B" if color == Color.WHITE else "C"
        n    = len(self.move_log) + 1
        self.move_log.append(f"{n:2}. {p}: {from_sq}->{to_sq}{eat}")

    def switch_player(self):
        return Color.BLACK if self.current_player == Color.WHITE else Color.WHITE


if __name__ == "__main__":
    root = tk.Tk()
    app = GuiGame(root, ai_color=Color.BLACK)
    root.mainloop()
