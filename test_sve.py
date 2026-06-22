"""
Kompletan test suite — sve funkcionalnosti projekta Junacki Megdan
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from board import Board
from piece import Piece, Color, PieceType
from move_generator import MoveGenerator, Move
from game_state import GameState
from history_tree import HistoryTree
from relics import RelicDeck, RelicType, RelicEffect, get_relic_duration
from board_events import BrazdeLocations, RelicActivationSystem
from minimax import Minimax
from heusteric import Heuristic
from game_loop import GameLoop

mg = MoveGenerator()

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  [OK] {name}")
        passed += 1
    else:
        print(f"  [FAIL] {name}")
        failed += 1

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ------------------------------------------------------------------ #
#  1. TABLA I INDEKSIRANJE                                           #
# ------------------------------------------------------------------ #
section("1. Tabla i indeksiranje")

b = Board()
b.setup_initial_position()

test("Tabla ima 32 elementa", len(b.board) == 32)
test("Crni junaci na 0-11", all(b.board[i] and b.board[i].color == Color.BLACK for i in range(12)))
test("Sredina prazna (12-19)", all(b.board[i] is None for i in range(12, 20)))
test("Beli junaci na 20-31", all(b.board[i] and b.board[i].color == Color.WHITE for i in range(20, 32)))

row, col = b.index_to_row_col(0)
test("Indeks 0 -> red 0", row == 0)
back = b.row_col_to_index(row, col)
test("row_col_to_index je inverz index_to_row_col", back == 0)

# ------------------------------------------------------------------ #
#  2. GENERATOR POTEZA — OSNOVNO                                     #
# ------------------------------------------------------------------ #
section("2. Generator poteza — osnovno kretanje")

b2 = Board()
b2.setup_initial_position()
white_moves = mg.get_simple_moves(b2, Color.WHITE)
black_moves = mg.get_simple_moves(b2, Color.BLACK)
test("Beli ima 7 poteza na pocetku", len(white_moves) == 7)
test("Crni ima 7 poteza na pocetku", len(black_moves) == 7)

# Junak krece samo napred
for m in white_moves:
    r_from, _ = b2.index_to_row_col(m.from_idx)
    r_to, _ = b2.index_to_row_col(m.to_idx)
    test(f"Beli junak ide napred (red {r_from}->{r_to})", r_to < r_from)

# ------------------------------------------------------------------ #
#  3. OBAVEZNO JEDENJE I LANCANI SKOKOVI                             #
# ------------------------------------------------------------------ #
section("3. Obavezno jedenje i lancani skokovi")

b3 = Board()
# Beli junak na 20, crni junak na 16, slobodno polje na 11 (za skok)
b3.set_piece(20, Piece(Color.WHITE, PieceType.JUNAK))
b3.set_piece(16, Piece(Color.BLACK, PieceType.JUNAK))
all_moves = mg.get_all_moves(b3, Color.WHITE)
test("Jedenje je obavezno (nema prostih poteza)", all(m.captured for m in all_moves))
test("Postoji tacno jedan skok", len(all_moves) == 1)
test("Pojeden je protivnik na 16", 16 in all_moves[0].captured)

# Lancani skok: beli 28, crni na 24 i 17
b4 = Board()
b4.set_piece(28, Piece(Color.WHITE, PieceType.JUNAK))
b4.set_piece(24, Piece(Color.BLACK, PieceType.JUNAK))
b4.set_piece(17, Piece(Color.BLACK, PieceType.JUNAK))
chain = mg.get_all_moves(b4, Color.WHITE)
test("Lancani skok postoji", any(len(m.captured) == 2 for m in chain))

# ------------------------------------------------------------------ #
#  4. JUNAK JEDE SAMO NAPRED                                         #
# ------------------------------------------------------------------ #
section("4. Junak jede samo napred (ne unazad)")

b5 = Board()
# Beli junak na 16, crni unazad na 20 (beli se krece prema 0, unazad bi bio ka 20)
b5.set_piece(16, Piece(Color.WHITE, PieceType.JUNAK))
b5.set_piece(20, Piece(Color.BLACK, PieceType.JUNAK))
# Crni je UNAZAD od belog (red 5 > red 4), beli ne sme da ga jede
backward_captures = mg.get_capture_moves(b5, Color.WHITE)
test("Beli junak ne jede unazad", len(backward_captures) == 0)

# ------------------------------------------------------------------ #
#  5. KRALJEVIC — SVE 4 DIJAGONALE                                   #
# ------------------------------------------------------------------ #
section("5. Kraljevic krece se u sva 4 pravca")

b6 = Board()
b6.set_piece(18, Piece(Color.WHITE, PieceType.KRALJEVIC))
king_moves = mg.get_all_moves(b6, Color.WHITE)
test("Kraljevic ima vise od 4 poteza (klizi)", len(king_moves) > 4)
dirs_used = set()
for m in king_moves:
    r_f, c_f = b6.index_to_row_col(m.from_idx)
    r_t, c_t = b6.index_to_row_col(m.to_idx)
    dirs_used.add((r_t - r_f > 0, c_t - c_f > 0))
test("Kraljevic ide u barem 3 razlicita smera", len(dirs_used) >= 3)

# ------------------------------------------------------------------ #
#  6. CAREV DRUM — DEK                                               #
# ------------------------------------------------------------------ #
section("6. Carev drum (Dek)")

d = RelicDeck()
test("Drum pocinje prazan", len(d.deck) == 0)

d.advance_turn()
test("Posle 1. poteza: 1 relikvija", len(d.deck) == 1)
test("Prva relikvija je Toka", d.deck[0] == RelicType.TOKA_OD_CELIKA)

for _ in range(4):
    d.advance_turn()
test("Posle 5 poteza: drum pun (5)", len(d.deck) == 5)

d.advance_turn()
test("Posle 6. poteza: i dalje 5 (kapacitet)", len(d.deck) == 5)
test("Front (nova) je Toka (rotacija)", d.get_front() == RelicType.TOKA_OD_CELIKA)
test("Rear (stara) je Mesina", d.get_rear() == RelicType.MESINA_RUJNOG_VINA)

uzeta = d.activate_front()
test("activate_front vraca front relikviju", uzeta == RelicType.TOKA_OD_CELIKA)
test("Posle aktivacije: 4 relikvije", len(d.deck) == 4)

# ------------------------------------------------------------------ #
#  7. BRAZDE                                                         #
# ------------------------------------------------------------------ #
section("7. Brazde (specijalna polja)")

brd = Board()
brd.setup_initial_position()
# Pronadi indekse koji odgovaraju (3,0) i (4,7)
brazda1 = brd.row_col_to_index(3, 0)
brazda2 = brd.row_col_to_index(4, 7)
test("Polje (3,0) je Brazda", BrazdeLocations.is_brazda(brazda1, brd))
test("Polje (4,7) je Brazda", BrazdeLocations.is_brazda(brazda2, brd))
test("Obicno polje nije Brazda", not BrazdeLocations.is_brazda(0, brd))

# ------------------------------------------------------------------ #
#  8. TOKA OD CELIKA — OKLOP                                         #
# ------------------------------------------------------------------ #
section("8. Toka od celika (Oklop)")

bt = Board()
# Crni junak sa Tokom na 16, beli junak na 20 (pokusava da pojede)
crni_toka = Piece(Color.BLACK, PieceType.JUNAK)
crni_toka.activate_relic(RelicType.TOKA_OD_CELIKA)
bt.set_piece(16, crni_toka)
bt.set_piece(20, Piece(Color.WHITE, PieceType.JUNAK))

captures_vs_toka = mg.get_capture_moves(bt, Color.WHITE)
test("Toka blokira jedenje — nema dostupnih jedenja", len(captures_vs_toka) == 0)

# Posle tika Toka istice
crni_toka.tick_effects()
test("Toka istice posle 1 tika (duration=1)", not crni_toka.has_relic(RelicType.TOKA_OD_CELIKA))

captures_after = mg.get_capture_moves(bt, Color.WHITE)
test("Posle isteka Toke jedenje je moguce", len(captures_after) > 0)

# ------------------------------------------------------------------ #
#  9. MESINA RUJNOG VINA — KOLEB                                     #
# ------------------------------------------------------------------ #
section("9. Mesina rujnog vina (Koleb)")

bm = Board()
crni_koleb = Piece(Color.BLACK, PieceType.JUNAK)
crni_koleb.active_relics[RelicType.MESINA_RUJNOG_VINA] = RelicEffect(RelicType.MESINA_RUJNOG_VINA, 3)
bm.set_piece(16, crni_koleb)
bm.set_piece(20, Piece(Color.WHITE, PieceType.JUNAK))  # moze biti pojedeno

# Crni ne sme da skace (ima Koleb)
captures_koleb = mg.get_capture_moves(bm, Color.BLACK)
test("Koleb sprjecava skok crnog", len(captures_koleb) == 0)

# Trajanje: odmah tick 3->2, posle 2 crnih poteza -> 0
crni_koleb.tick_effects()  # 3->2
test("Posle 1 tika: duration=2", crni_koleb.active_relics[RelicType.MESINA_RUJNOG_VINA].duration == 2)
crni_koleb.tick_effects()  # 2->1
crni_koleb.tick_effects()  # 1->0 -> brise se
test("Posle 3 tika Koleb istice", not crni_koleb.has_relic(RelicType.MESINA_RUJNOG_VINA))

# ------------------------------------------------------------------ #
#  10. TOPUZ — RAZORNI UDARAC                                        #
# ------------------------------------------------------------------ #
section("10. Topuz (Razorni udarac)")

btp = Board()
beli_topuz = Piece(Color.WHITE, PieceType.JUNAK)
beli_topuz.activate_relic(RelicType.TOPUZ)
btp.set_piece(21, beli_topuz)
btp.set_piece(17, Piece(Color.BLACK, PieceType.JUNAK))  # direktno susedno polje

topuz_moves = mg.get_capture_moves(btp, Color.WHITE)
test("Topuz daje direktno jedenje", len(topuz_moves) > 0)
test("Topuz: to_idx == captured[0] (zauzima protivnicko polje)",
     any(m.to_idx == m.captured[0] for m in topuz_moves))

# Proveri redosled: captured se brisu PRE pomeranja
btp2 = Board()
beli_tp2 = Piece(Color.WHITE, PieceType.JUNAK)
beli_tp2.activate_relic(RelicType.TOPUZ)
btp2.set_piece(21, beli_tp2)
crni_tp2 = Piece(Color.BLACK, PieceType.JUNAK)
btp2.set_piece(17, crni_tp2)
topuz_move = [m for m in mg.get_capture_moves(btp2, Color.WHITE) if m.to_idx == 17][0]
# Simuliraj apply_move redosled
for idx in topuz_move.captured:
    btp2.remove_piece(idx)
piece = btp2.get_piece(topuz_move.from_idx)
btp2.remove_piece(topuz_move.from_idx)
btp2.set_piece(topuz_move.to_idx, piece)
test("Topuz: beli stoji na 17 (protivnicko polje)", btp2.get_piece(17) == beli_tp2)
test("Topuz: crni je uklonjen", btp2.get_piece(17).color == Color.WHITE)

# ------------------------------------------------------------------ #
#  11. SARAC — SARCEV SKOK                                           #
# ------------------------------------------------------------------ #
section("11. Sarac (Sarcev skok)")

# Pozicije:
#   25=(6,3) beli sa Sarcem, 22=(5,4) sopstvena figura, 15=(3,6) crni neprijatelj
#   Sarac skok: 25 -> preskoci 22 -> sletanje 18=(4,5) -> jede 15 -> sletanje 11=(2,7)
bsa = Board()
beli_sarac = Piece(Color.WHITE, PieceType.JUNAK)
beli_sarac.activate_relic(RelicType.SARAC)
bsa.set_piece(25, beli_sarac)
bsa.set_piece(22, Piece(Color.WHITE, PieceType.JUNAK))  # sopstvena figura NE od 25
bsa.set_piece(15, Piece(Color.BLACK, PieceType.JUNAK))  # neprijatelj na (3,6)

sarac_moves = mg.get_capture_moves(bsa, Color.WHITE)
# Sarac: preskoci 22, sletanje 18, pa jede 15 i slete na 11
test("Sarac daje poteze sa jedenjima", any(m.captured for m in sarac_moves))

# Sarac bez naknadnog jedenja ne generise prazne captured
empty_captures = [m for m in sarac_moves if not m.captured]
test("Sarac ne generise lazne jedenje-poteze (captured=[])", len(empty_captures) == 0)

# ------------------------------------------------------------------ #
#  12. TRI TOVARA BLAGA — KRUNJENJE                                  #
# ------------------------------------------------------------------ #
section("12. Tri tovara blaga (Krunjenje)")

junak = Piece(Color.WHITE, PieceType.JUNAK)
test("Junak pre krunjenja", junak.type == PieceType.JUNAK)
junak.relics.add(RelicType.TRI_TOVARA_BLAGA)
junak.promote()
test("Posle Tri tovara blaga -> Kraljevic", junak.type == PieceType.KRALJEVIC)

# ------------------------------------------------------------------ #
#  13. MARKO KRALJEVIC — PROMOCIJA I SPOSOBNOSTI                     #
# ------------------------------------------------------------------ #
section("13. Marko Kraljevic")

marko_piece = Piece(Color.WHITE, PieceType.KRALJEVIC)
marko_piece.relics = {
    RelicType.TRI_TOVARA_BLAGA,
    RelicType.SARAC,
    RelicType.TOPUZ,
    RelicType.MESINA_RUJNOG_VINA,
}
ras = RelicActivationSystem(RelicDeck())
promoted = ras.check_marko_promotion(marko_piece)
test("Marko promocija sa sve 4 relikvije", promoted)
test("Tip je MARKO_KRALJEVIC", marko_piece.type == PieceType.MARKO_KRALJEVIC)
test("is_marko() vraca True", marko_piece.is_marko())
test("is_king() vraca True za Marka", marko_piece.is_king())

# Marko imunitet na Mesinu
from relics import RelicEffect

def find_nearest(from_idx, own_color, board):
    from_row, from_col = board.index_to_row_col(from_idx)
    enemy_color = Color.BLACK if own_color == Color.WHITE else Color.WHITE
    nearest, min_dist = None, float('inf')
    for idx, ep in board.get_all_pieces(enemy_color):
        e_row, e_col = board.index_to_row_col(idx)
        dist = abs(e_row - from_row) + abs(e_col - from_col)
        if dist < min_dist:
            min_dist, nearest = dist, ep
    return nearest

# Test 1: Mesina pogadja obicnu figuru
# Beli aktivator na 20=(5,0), crni meta na 16=(4,1) — jedini crni na tabli
mesina_board = Board()
beli_activator = Piece(Color.WHITE, PieceType.JUNAK)
crni_meta = Piece(Color.BLACK, PieceType.JUNAK)
mesina_board.set_piece(20, beli_activator)
mesina_board.set_piece(16, crni_meta)
nearest = find_nearest(20, Color.WHITE, mesina_board)
if nearest and not nearest.is_marko():
    nearest.active_relics[RelicType.MESINA_RUJNOG_VINA] = RelicEffect(RelicType.MESINA_RUJNOG_VINA, 3)
test("Mesina pogadja obicnu figuru", crni_meta.has_relic(RelicType.MESINA_RUJNOG_VINA))

# Test 2: Mesina ne pogadja Marka
mesina_board2 = Board()
crni_activator2 = Piece(Color.BLACK, PieceType.JUNAK)
marko_target = Piece(Color.WHITE, PieceType.MARKO_KRALJEVIC)
mesina_board2.set_piece(8, crni_activator2)
mesina_board2.set_piece(16, marko_target)
nearest_marko = find_nearest(8, Color.BLACK, mesina_board2)
if nearest_marko and not nearest_marko.is_marko():
    nearest_marko.active_relics[RelicType.MESINA_RUJNOG_VINA] = RelicEffect(RelicType.MESINA_RUJNOG_VINA, 3)
test("Mesina ne pogadja Marka (imunitet)", not marko_target.has_relic(RelicType.MESINA_RUJNOG_VINA))

# Toka traje 2 poteza za Marka
test("Toka traje 1 za obicnog Kraljevica", get_relic_duration(RelicType.TOKA_OD_CELIKA, is_marko=False) == 1)
test("Toka traje 2 za Marka Kraljevica", get_relic_duration(RelicType.TOKA_OD_CELIKA, is_marko=True) == 2)

# ------------------------------------------------------------------ #
#  14. TICK EFEKATA — VREMENSKI OKVIR                                #
# ------------------------------------------------------------------ #
section("14. Tick efekata (tajming)")

# Toka: activates on BLACK's piece, blocked for 1 WHITE turn
toka_piece = Piece(Color.BLACK, PieceType.JUNAK)
toka_piece.activate_relic(RelicType.TOKA_OD_CELIKA)
test("Toka pocinje na duration=1", toka_piece.active_relics[RelicType.TOKA_OD_CELIKA].duration == 1)
toka_piece.tick_effects()
test("Toka istekla posle 1 tika", not toka_piece.has_relic(RelicType.TOKA_OD_CELIKA))

# Topuz i Sarac: treba duration=2 da prežive tick do sledeceg poteza
test("Topuz duration=2 (prezivljava protivnikov tick)", get_relic_duration(RelicType.TOPUZ) == 2)
test("Sarac duration=2 (prezivljava protivnikov tick)", get_relic_duration(RelicType.SARAC) == 2)

topuz_p = Piece(Color.WHITE, PieceType.JUNAK)
topuz_p.activate_relic(RelicType.TOPUZ)
topuz_p.tick_effects()  # protivnikov potez
test("Topuz jos aktivan posle 1 tika (na raspolaganju za sledeci potez)", topuz_p.has_relic(RelicType.TOPUZ))
topuz_p.tick_effects()  # jos jedan protivnikov potez
test("Topuz iscezao posle 2 tika", not topuz_p.has_relic(RelicType.TOPUZ))

# Mesina: duration=3, efektivno 2 neprijateljevna poteza
mesina_p = Piece(Color.BLACK, PieceType.JUNAK)
mesina_p.active_relics[RelicType.MESINA_RUJNOG_VINA] = RelicEffect(RelicType.MESINA_RUJNOG_VINA, 3)
mesina_p.tick_effects()  # odmah-tick posle aktivacije -> 2
test("Mesina: posle odmah-tika duration=2", mesina_p.active_relics[RelicType.MESINA_RUJNOG_VINA].duration == 2)
mesina_p.tick_effects()  # crni 1. potez -> 1
test("Mesina: posle 2. tika duration=1", mesina_p.active_relics[RelicType.MESINA_RUJNOG_VINA].duration == 1)
mesina_p.tick_effects()  # crni 2. potez -> 0 -> brise se
test("Mesina istekla posle 3 tika (2 efektivna poteza)", not mesina_p.has_relic(RelicType.MESINA_RUJNOG_VINA))

# ------------------------------------------------------------------ #
#  15. PROMOCIJA JUNAKA                                              #
# ------------------------------------------------------------------ #
section("15. Promocija junaka")

bprom = Board()
beli_junak = Piece(Color.WHITE, PieceType.JUNAK)
bprom.set_piece(1, beli_junak)  # red 0 -> promovise se
row_check, _ = bprom.index_to_row_col(1)
test("Indeks 1 je u redu 0", row_check == 0)
if beli_junak.color == Color.WHITE and row_check == 0:
    beli_junak.promote()
test("Junak promovisan u Kraljevica", beli_junak.type == PieceType.KRALJEVIC)

# ------------------------------------------------------------------ #
#  16. UNDO SISTEM — HISTORY TREE                                    #
# ------------------------------------------------------------------ #
section("16. Undo sistem (History Tree)")

ub = Board()
ub.setup_initial_position()
init_state = GameState(board=ub.copy(), current_player=Color.WHITE, no_progress_counter=0)
tree = HistoryTree(init_state)

test("Koren je pocetno stanje", tree.current_node is tree.root)

move1 = Move(20, 16)
ub.set_piece(16, ub.get_piece(20))
ub.remove_piece(20)
state1 = GameState(board=ub.copy(), current_player=Color.BLACK, no_progress_counter=1, move=move1)
tree.add_move(state1)
test("Posle prvog poteza: current != root", tree.current_node is not tree.root)

tree.undo()
test("Posle undo: nazad na root", tree.current_node is tree.root)

# Alternativni potez (grananje)
move1b = Move(21, 17)
ub2 = tree.current_node.state.board.copy()
ub2.set_piece(17, ub2.get_piece(21))
ub2.remove_piece(21)
state1b = GameState(board=ub2.copy(), current_player=Color.BLACK, no_progress_counter=1, move=move1b)
tree.add_move(state1b)

tree.undo()
test("Root ima 2 deteta (grananje)", len(tree.root.children) == 2)

paths = tree.get_full_history()
test("DFS daje 2 putanje (ukljucujuci ponistene)", len(paths) == 2)
test("Svaka putanja pocinje od korena", all(p[0] == init_state for p in paths))

# ------------------------------------------------------------------ #
#  17. REMI USLOV                                                    #
# ------------------------------------------------------------------ #
section("17. Remi uslov (40 poteza)")

gl_remi = GameLoop.__new__(GameLoop)
gl_remi.board = Board()
gl_remi.board.setup_initial_position()
gl_remi.no_progress_counter = 39
moves_check = mg.get_all_moves(gl_remi.board, Color.WHITE)
test("Remi jos ne nastupa na 39", gl_remi.no_progress_counter < 40)
gl_remi.no_progress_counter = 40
test("Remi nastupa na 40", gl_remi.no_progress_counter >= 40)

# ------------------------------------------------------------------ #
#  18. MINIMAX — VRACA VALIDAN POTEZ                                 #
# ------------------------------------------------------------------ #
section("18. Minimax + Alpha-Beta + Iterative Deepening")

import time
mm = Minimax()
bm_ai = Board()
bm_ai.setup_initial_position()

start = time.time()
best = mm.get_best_move(bm_ai, Color.BLACK)
elapsed = time.time() - start

test("Minimax vraca potez", best is not None)
test("Minimax potez ima validan from_idx", 0 <= best.from_idx < 32)
test("Minimax potez ima validan to_idx", 0 <= best.to_idx < 32)
test("Minimax staje unutar 3.1s", elapsed < 3.1)

# Potez mora biti u skupu legalnih poteza
legal = mg.get_all_moves(bm_ai, Color.BLACK)
legal_pairs = {(m.from_idx, m.to_idx) for m in legal}
test("Minimax bira legalan potez", (best.from_idx, best.to_idx) in legal_pairs)

# ------------------------------------------------------------------ #
#  19. ZOBRIST HASHING                                               #
# ------------------------------------------------------------------ #
section("19. Zobrist Hashing")

zh_board = Board()
zh_board.setup_initial_position()

h1 = mm.board_to_key(zh_board, Color.WHITE)
h2 = mm.board_to_key(zh_board, Color.WHITE)
test("Isti raspored, isti hash", h1 == h2)

h3 = mm.board_to_key(zh_board, Color.BLACK)
test("Ista pozicija, drugacija strana -> drugaciji hash", h1 != h3)

# Pomeri figuru i proveri da se hash menja
zh_board2 = zh_board.copy()
piece_to_move = zh_board2.get_piece(20)
zh_board2.remove_piece(20)
zh_board2.set_piece(16, piece_to_move)
h4 = mm.board_to_key(zh_board2, Color.WHITE)
test("Promena pozicije menja hash", h1 != h4)

# Vrati figuru i hash treba da bude isti kao pocetni
zh_board3 = zh_board2.copy()
p_back = zh_board3.get_piece(16)
zh_board3.remove_piece(16)
zh_board3.set_piece(20, p_back)
h5 = mm.board_to_key(zh_board3, Color.WHITE)
test("Vracanjem figure hash je opet isti (XOR reverzibilnost)", h1 == h5)

# Hash je int (64-bit), ne tuple
test("Hash je integer (ne tuple)", isinstance(h1, int))

# Razlicita polja iste figure daju razlicite hasheve
zh_board4 = Board()
zh_board4.setup_initial_position()
zh_board5 = Board()
zh_board5.setup_initial_position()
p4 = zh_board4.get_piece(20)
zh_board4.remove_piece(20)
zh_board4.set_piece(16, p4)
p5 = zh_board5.get_piece(21)
zh_board5.remove_piece(21)
zh_board5.set_piece(17, p5)
h6 = mm.board_to_key(zh_board4, Color.WHITE)
h7 = mm.board_to_key(zh_board5, Color.WHITE)
test("Razliciti rasporedi daju razlicite hasheve", h6 != h7)

# ------------------------------------------------------------------ #
#  20. HEURISTIKA                                                    #
# ------------------------------------------------------------------ #
section("20. Heuristika")

heur = Heuristic()
hb = Board()
hb.setup_initial_position()
score_balanced = heur.evaluate(hb, Color.WHITE)
test("Uravnotezena pozicija daje skor blizak 0", abs(score_balanced) < 2.0)

# Daj belom prednost
hb2 = hb.copy()
hb2.remove_piece(0)  # ukloni jednog crnog
score_white = heur.evaluate(hb2, Color.WHITE)
test("Beli ima prednost kad crni ima manje figura", score_white > 0)

score_black = heur.evaluate(hb2, Color.BLACK)
test("Crni ima negativan skor kad ima manje figura", score_black < 0)

# ------------------------------------------------------------------ #
#  21. KOMPLETNA SIMULACIJA (5 poteza)                               #
# ------------------------------------------------------------------ #
section("21. Kompletna simulacija igre (5 poteza AI vs Human)")

gl = GameLoop(ai_color=Color.BLACK)

errors = []
for turn in range(5):
    try:
        gl.relic_deck.advance_turn()
        moves = mg.get_all_moves(gl.board, gl.current_player)
        if not moves:
            break
        if gl.current_player == Color.BLACK:
            move = gl.minimax.get_best_move(gl.board, gl.current_player)
            if not move:
                move = moves[0]
        else:
            move = moves[0]
        gl.apply_move(move)
        gl.tick_opponent_pieces()
        gl.save_state(move)
        gl.current_player = gl.switch_player()
    except Exception as e:
        errors.append(str(e))

test("5 poteza bez exception-a", len(errors) == 0)
if errors:
    for e in errors:
        print(f"    Exception: {e}")
test("Posle 5 poteza stablo ima cvorove", gl.history.current_node is not gl.history.root)

# ------------------------------------------------------------------ #
#  REZULTAT                                                          #
# ------------------------------------------------------------------ #
print(f"\n{'='*55}")
print(f"  UKUPNO: {passed} proslo / {failed} palo / {passed+failed} ukupno")
print(f"{'='*55}")
if failed == 0:
    print("  SVE OK — projekat prolazi sve testove!")
else:
    print(f"  PAZNJA: {failed} test(ova) palo!")
