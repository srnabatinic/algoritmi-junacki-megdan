import time
from heusteric import Heuristic
from move_generator import MoveGenerator
from piece import Color, PieceType

class Minimax:
    
    def __init__(self):
        self.heuristic = Heuristic()
        self.mg = MoveGenerator()
        self.transposition_table = {}
        self.time_limit = 3.0
        self.start_time = None

        # Zobrist Hashing — za svaki mogući (polje, boja, tip) trojac
        # čuvamo jedan nasumičan 64-bitni broj.
        # Seed=42 garantuje iste brojeve pri svakom pokretanju.
        import random
        rng = random.Random(42)
        self.zobrist_table = {
            (sq, color, ptype): rng.getrandbits(64)
            for sq in range(32)
            for color in ['W', 'B']
            for ptype in ['J', 'K', 'KM']
        }
        self.zobrist_black_to_move = rng.getrandbits(64)
    
    def get_best_move(self, board, color):
        """
        Iterative deepening — krećemo od dubine 1 i povećavamo dok ne istekne vreme.
        Uvek čuvamo rezultat poslednje ZAVRŠENE dubine.
        Ako dubina 6 istekne na pola, koristimo rezultat dubine 5.
        """
        self.start_time = time.time()
        # Resetuj transposition table na početku svakog poteza
        # jer staro stanje table više nije relevantno
        self.transposition_table = {}
        
        best_move = None
        best_score = float('-inf')
        depth = 1
        
        while not self.is_time_up():
            score, move = self.minimax(
                board, depth,
                float('-inf'), float('inf'),
                True, color
            )
            
            # Prihvatamo rezultat samo ako je dubina ZAVRŠENA pre isteka vremena
            # Ako je vreme isteklo tokom ove dubine, rezultat može biti nepouzdan
            if not self.is_time_up() and move is not None:
                best_score = score
                best_move = move
            
            depth += 1
        
        return best_move
    
    def minimax(self, board, depth, alpha, beta, maximizing, color):
        """
        Rekurzivni Minimax sa Alpha-Beta odsecanjem.
        
        board      — trenutno stanje table
        depth      — koliko poteza još gledamo unapred
        alpha      — najbolji score koji MAX može garantovati (počinje -inf)
        beta       — najbolji score koji MIN može garantovati (počinje +inf)
        maximizing — True ako je na potezu AI (MAX), False ako je protivnik (MIN)
        color      — boja AI igrača (ne menja se tokom rekurzije, uvek je to "naš" igrač)
        """
        # Ako je vreme isteklo, odmah se vrati — ne nastavljamo pretragu
        if self.is_time_up():
            return self.heuristic.evaluate(board, color), None
        
        # Koji igrač je trenutno na potezu u ovom čvoru stabla
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        current_color = color if maximizing else opponent
        
        # Proveri transposition table — da li smo već videli ovu poziciju
        # na dovoljnoj dubini? Ako da, ne moramo ponovo računati.
        board_key = self.board_to_key(board, current_color)
        if board_key in self.transposition_table:
            entry = self.transposition_table[board_key]
            if entry['depth'] >= depth:
                return entry['score'], entry['move']
        
        # Generiši sve legalne poteze za trenutnog igrača
        moves = self.mg.get_all_moves(board, current_color)
        
        # Dno rekurzije: dubina 0, nema poteza, ili isteklo vreme
        # Ovde heuristika procenjuje koliko je pozicija dobra za nas
        if depth == 0 or not moves:
            return self.heuristic.evaluate(board, color), None
        
        # Sortiraj poteze — bolji potezi prvo = više alpha-beta odsecanja
        moves = self.order_moves(moves, board)
        best_move = None
        
        if maximizing:
            # MAX čvor — mi biramo potez koji maksimizuje naš score
            best_score = float('-inf')
            for move in moves:
                # Simuliraj potez na kopiji table — original ostaje nepromenjen
                new_board = self.make_move(board, move)
                
                # Rekurzivno evaluiraj poziciju nakon ovog poteza
                # Sledeći nivo je MIN (protivnikov potez)
                score, _ = self.minimax(new_board, depth - 1, alpha, beta, False, color)
                
                if score > best_score:
                    best_score = score
                    best_move = move
                
                # Ažuriraj alpha — najbolje što MAX može garantovati do sada
                alpha = max(alpha, best_score)
                
                # Beta odsecanje: MIN nikad neće dozvoliti da dođemo ovde
                # jer već ima bolju opciju negde drugde — prestani sa pretragom
                if beta <= alpha:
                    break
        else:
            # MIN čvor — protivnik bira potez koji minimizuje naš score
            best_score = float('inf')
            for move in moves:
                new_board = self.make_move(board, move)
                
                # Sledeći nivo je MAX (naš potez)
                score, _ = self.minimax(new_board, depth - 1, alpha, beta, True, color)
                
                if score < best_score:
                    best_score = score
                    best_move = move
                
                # Ažuriraj beta — najbolje što MIN može garantovati do sada
                beta = min(beta, best_score)
                
                # Alpha odsecanje: MAX nikad neće birati ovu granu
                # jer već ima bolju opciju — prestani sa pretragom
                if beta <= alpha:
                    break
        
        # Sačuvaj rezultat u transposition table za buduće pozive
        self.transposition_table[board_key] = {
            'score': best_score,
            'move': best_move,
            'depth': depth
        }
        
        return best_score, best_move
    
    def order_moves(self, moves, board):
        """
        Sortira poteze od najboljeg ka najgorem pre pretrage.
        Što su bolji potezi na početku liste, više alpha-beta odsecanja se aktivira
        i manje čvorova moramo da evaluiramo — direktno ubrzava Minimax.
        
        Prioriteti:
        1. Jedenja (i više jedenja u lancu = bolje)
        2. Kraljevići (jača figura = vrednije kretanje)
        3. Potezi prema centru table
        """
        def move_priority(move):
            score = 0
            
            # Jedenja su uvek prioritet — više pojedenih figura = veći bonus
            if move.captured:
                score += 10 + len(move.captured) * 5
            
            # Kraljevići i Marko Kraljevič imaju prednost
            piece = board.get_piece(move.from_idx)
            if piece:
                if piece.type == PieceType.MARKO_KRALJEVIC:
                    score += 5
                elif piece.type == PieceType.KRALJEVIC:
                    score += 3
            
            # Potezi prema centru su generalno bolji
            row, col = board.index_to_row_col(move.to_idx)
            center_bonus = 3.5 - abs(col - 3.5)
            score += center_bonus * 0.5
            
            return score
        
        return sorted(moves, key=move_priority, reverse=True)

    def board_to_key(self, board, current_color):
        """
        Zobrist Hashing — jedinstven 64-bitni ključ za transposition table.

        Princip: za svaku figuru na tabli XOR-ujemo njen nasumičan broj
        (dodeljen u __init__). XOR je reverzibilan, što znači da isti
        raspored figura uvek daje isti hash, bez obzira na redosled dodavanja.
        Na kraju XOR-ujemo broj za stranu koja je na potezu.
        """
        h = 0
        for sq, piece in enumerate(board.board):
            if piece:
                h ^= self.zobrist_table[(sq, piece.color.value, piece.type.value)]
        if current_color.value == 'B':
            h ^= self.zobrist_black_to_move
        return h
    
    def make_move(self, board, move):
        """
        Primenjuje potez na KOPIJU table i vraća tu kopiju.
        Original tabla ostaje nepromenjena — ovo je ključno za Minimax
        jer moramo moći da se "vratimo" nakon simulacije.
        """
        # Napravi nezavisnu kopiju — deepcopy u Board.copy() osigurava
        # da izmene na new_board ne utiču na originalni board
        new_board = board.copy()
        
        # Brišemo captured PRE pomeranja — bitno za Topuz gde je to_idx == captured[0]
        if move.captured:
            for idx in move.captured:
                new_board.remove_piece(idx)

        piece = new_board.get_piece(move.from_idx)
        new_board.remove_piece(move.from_idx)
        new_board.set_piece(move.to_idx, piece)
        
        # Proveri promociju na kopiji
        self._check_promotion(new_board, move.to_idx)
        
        return new_board
    
    def _check_promotion(self, board, index):
        """
        Proverava i izvršava promociju na datoj tabli.
        Privatna metoda — koristi se samo unutar make_move.
        """
        piece = board.get_piece(index)
        if piece and piece.type == PieceType.JUNAK:
            row, _ = board.index_to_row_col(index)
            if (piece.color == Color.WHITE and row == 0) or \
               (piece.color == Color.BLACK and row == 7):
                piece.promote()
    
    def is_time_up(self):
        """Proverava da li je isteklo 3 sekunde za razmišljanje."""
        return time.time() - self.start_time >= self.time_limit