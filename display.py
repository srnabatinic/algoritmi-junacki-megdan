from piece import Color, PieceType
import os

# Širina linije table i info-boksa (ukupno sa okvirom)
BOARD_LINE_W = 38   # svaka linija table ima tačno 38 znakova
BOX_INNER    = 29   # znakova između ║ i ║  (║ + 29 + ║ = 31 ukupno)


class Display:

    def __init__(self, board=None):
        self.board = board
        self.move_log = []

    # ------------------------------------------------------------------ #
    #  Pomoćne metode za info-boks                                         #
    # ------------------------------------------------------------------ #

    def _box(self, text=""):
        """Linija boksa: ║ <tekst poravnat na BOX_INNER znakova> ║"""
        return "║ " + str(text)[:BOX_INNER - 2].ljust(BOX_INNER - 2) + " ║"

    def _box_top(self):
        return "╔" + "═" * BOX_INNER + "╗"

    def _box_div(self):
        return "╠" + "═" * BOX_INNER + "╣"

    def _box_bot(self):
        return "╚" + "═" * BOX_INNER + "╝"

    def _box_center(self, text):
        return "║" + str(text)[:BOX_INNER].center(BOX_INNER) + "║"

    # ------------------------------------------------------------------ #
    #  Simbol figure                                                       #
    # ------------------------------------------------------------------ #

    def _get_symbol(self, piece):
        return {
            (Color.WHITE, PieceType.JUNAK):          "w",
            (Color.WHITE, PieceType.KRALJEVIC):       "W",
            (Color.WHITE, PieceType.MARKO_KRALJEVIC): "M",
            (Color.BLACK, PieceType.JUNAK):           "b",
            (Color.BLACK, PieceType.KRALJEVIC):       "B",
            (Color.BLACK, PieceType.MARKO_KRALJEVIC): "m",
        }.get((piece.color, piece.type), "?")

    # ------------------------------------------------------------------ #
    #  Tabla                                                               #
    # ------------------------------------------------------------------ #

    def get_board_lines(self, board, highlight_map=None):
        lines = []
        W = BOARD_LINE_W

        # Zaglavlje kolona — "a" je poravnato sa centrom prve tamne kolone
        lines.append(("     " + "   ".join("abcdefgh")).ljust(W))
        lines.append(("   ┌" + "───┬" * 7 + "───┐").ljust(W))

        for row in range(8):
            rn = 8 - row
            line = f" {rn} │"                       # " 8 │" — 4 znaka
            for col in range(8):
                idx = board.row_col_to_index(row, col)
                if idx is not None:
                    if highlight_map and idx in highlight_map:
                        n = highlight_map[idx]
                        cell = str(n)
                        line += f"{cell:>2} │"      # desno poravnano, 4 znaka
                    else:
                        piece = board.get_piece(idx)
                        sym = self._get_symbol(piece) if piece else "·"
                        line += f" {sym} │"         # 4 znaka
                else:
                    line += "   │"                  # belo polje, 4 znaka
            line += f" {rn}"                        # desni redni broj
            lines.append(line)                      # ukupno 38 znakova

            if row < 7:
                lines.append(("   ├" + "───┼" * 7 + "───┤").ljust(W))

        lines.append(("   └" + "───┴" * 7 + "───┘").ljust(W))
        lines.append(("     " + "   ".join("abcdefgh")).ljust(W))

        return lines

    # ------------------------------------------------------------------ #
    #  Heuristička traka                                                   #
    # ------------------------------------------------------------------ #

    def _heuristic_bar(self, score):
        """Vraća string 'B [████·│·····] W' koji stane u info-boks."""
        bar_w = 19                          # znakova unutar zagrada
        center = bar_w // 2                 # = 9
        clamped = max(-10.0, min(10.0, score))
        fill = int((clamped / 10.0) * center)

        bar = ["·"] * bar_w
        bar[center] = "│"
        if fill > 0:
            for i in range(center, center + fill):
                bar[i] = "█"
        elif fill < 0:
            for i in range(center + fill, center):
                bar[i] = "█"

        # "B [" + 19 znakova + "] W" = 27 znakova → stane u BOX_INNER-2=27
        return "B [" + "".join(bar) + "] W"

    # ------------------------------------------------------------------ #
    #  Info panel (desna strana)                                           #
    # ------------------------------------------------------------------ #

    def get_info_lines(self, board, color, heuristic, moves, move_number):
        lines = []

        base_score, breakdown = heuristic.evaluate_with_mobility(board, color)

        # ── Evaluacija ──────────────────────────────────────────────── #
        lines.append(self._box_top())
        lines.append(self._box_center("EVALUACIJA POZICIJE"))
        lines.append(self._box_div())

        bar_str = self._heuristic_bar(base_score)
        lines.append(self._box(bar_str))
        lines.append(self._box(f"  Score:      {base_score:+.2f}"))
        lines.append(self._box(f"  Mobilnost:  {breakdown['mobilnost']:+.2f}"))

        lines.append(self._box_div())
        for name, val in breakdown.items():
            if name in ("ukupno", "mobilnost"):
                continue
            lines.append(self._box(f"  {name.capitalize():<14} {val:+.2f}"))

        # ── Na potezu ────────────────────────────────────────────────── #
        lines.append(self._box_div())
        player_str = "Beli  (w/W/M)" if color == Color.WHITE else "Crni  (b/B/m)"
        lines.append(self._box(f"  Na potezu:  {player_str}"))

        # ── Dostupni potezi ──────────────────────────────────────────── #
        lines.append(self._box_div())
        lines.append(self._box("  DOSTUPNI POTEZI:"))

        for i, move in enumerate(moves[:10]):
            fr, fc = board.index_to_row_col(move.from_idx)
            tr, tc = board.index_to_row_col(move.to_idx)
            fsq = f"{'abcdefgh'[fc]}{8 - fr}"
            tsq = f"{'abcdefgh'[tc]}{8 - tr}"
            eat = f" x{len(move.captured)}" if move.captured else ""
            lines.append(self._box(f"  {i + 1:2}. {fsq} → {tsq}{eat}"))

        if len(moves) > 10:
            lines.append(self._box(f"  ... i još {len(moves) - 10} poteza"))

        # ── Log odigranih poteza ─────────────────────────────────────── #
        lines.append(self._box_div())
        lines.append(self._box("  ODIGRANI POTEZI:"))
        for entry in self.move_log[-6:]:
            lines.append(self._box(f"  {entry}"))

        lines.append(self._box_bot())
        return lines

    # ------------------------------------------------------------------ #
    #  Glavni prikaz (tabla levo + info desno)                            #
    # ------------------------------------------------------------------ #

    def render_full(self, board, color, heuristic, moves, highlight_map=None):
        self._clear()

        board_lines = self.get_board_lines(board, highlight_map)
        info_lines  = self.get_info_lines(board, color, heuristic, moves,
                                          len(self.move_log))

        print(f"\n  JUNAČKI MEGDAN\n")

        total = max(len(board_lines), len(info_lines))
        for i in range(total):
            left  = board_lines[i] if i < len(board_lines) else ""
            right = info_lines[i]  if i < len(info_lines)  else ""
            print(f"{left:<{BOARD_LINE_W}}  {right}")

        print()

    # ------------------------------------------------------------------ #
    #  Log poteza                                                          #
    # ------------------------------------------------------------------ #

    def log_move(self, board, move, color, move_number):
        fr, fc = board.index_to_row_col(move.from_idx)
        tr, tc = board.index_to_row_col(move.to_idx)
        fsq = f"{'abcdefgh'[fc]}{8 - fr}"
        tsq = f"{'abcdefgh'[tc]}{8 - tr}"
        player = "B" if color == Color.WHITE else "C"
        eat = f" (x{len(move.captured)})" if move.captured else ""
        self.move_log.append(f"{move_number}. {player}: {fsq}→{tsq}{eat}")

    # ------------------------------------------------------------------ #
    #  Kraj igre i reprodukcija                                            #
    # ------------------------------------------------------------------ #

    def render_game_over(self, winner):
        print("\n" + "═" * 42)
        if winner == Color.WHITE:
            print("  KRAJ IGRE — Pobedio je BELI!  (w/W/M)")
        elif winner == Color.BLACK:
            print("  KRAJ IGRE — Pobedio je CRNI!  (b/B/m)")
        print("═" * 42 + "\n")

    def render_draw(self):
        print("\n" + "═" * 42)
        print("  REMI — 40 poteza bez promene broja figura.")
        print("═" * 42 + "\n")

    def render_replay_step(self, board, move_number, total_moves):
        board_lines = self.get_board_lines(board)
        print(f"\n  Reprodukcija — Potez {move_number}/{total_moves}\n")
        for line in board_lines:
            print(line)

    # ------------------------------------------------------------------ #
    #  Interno                                                             #
    # ------------------------------------------------------------------ #

    def _clear(self):
        os.system("cls" if os.name == "nt" else "clear")
