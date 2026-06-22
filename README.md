# Junački megdan ♟️

Strateška igra na tabli zasnovana na srpskoj epici — napredna varijanta igre Dame
sa sistemom relikvija, Carevim drumom i AI protivnikom.

Projekat rađen u okviru predmeta Algoritmi i strukture podataka.

## Tehnologije
- Python 3
- Tkinter (grafički interfejs, ugrađena Python biblioteka)

## Struktura projekta
- `main.py` — pokretanje aplikacije
- `gui.py` — grafički interfejs (Tkinter)
- `game_loop.py` — glavna petlja igre
- `board.py` — logika table (1D niz od 32 elementa)
- `piece.py` — figure (Junak, Kraljevic, Marko Kraljevic)
- `move_generator.py` — generisanje validnih poteza
- `minimax.py` — Minimax algoritam sa Alpha-Beta odsecanjem
- `heusteric.py` — heuristika za ocenu stanja igre
- `relics.py` — sistem relikvija i Carev drum (Deque)
- `game_state.py` — GameState objekat za Undo sistem (Stek)
- `history_tree.py` — N-arno stablo istorije poteza
- `board_events.py` — eventi na tabli (Brazde)
- `display.py` — prikaz table

## Algoritmi i strukture podataka
- Minimax sa Alpha-Beta odsecanjem i Iterative Deepening (3s limit)
- Zobrist Hashing + Transposition Table (optimizacija)
- Deque — Carev drum (kapacitet 5 relikvija)
- Stek — Undo sistem
- N-arno stablo — istorija i reprodukcija partije

## Kako pokrenuti
1. Nema dodatnih zavisnosti — Tkinter dolazi uz Python
2. Pokreni igru:
   python gui.py

## Testovi
Projekat sadrži automatske testove:
   python test_sve.py