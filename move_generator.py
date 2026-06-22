from piece import Color, PieceType
from board import Board
from relics import RelicType

class Move:
    def __init__(self, from_idx, to_idx, captured=None):
        self.from_idx = from_idx
        self.to_idx = to_idx
        self.captured = captured if captured is not None else []

    def __repr__(self):
        return f"Move({self.from_idx} -> {self.to_idx}, captured={self.captured})"

class MoveGenerator:
    def get_simple_moves_for_piece(self, board, piece, index):
        moves = []
        neighbors = board.get_diagonal_neighbors(index)

        if piece.is_king():
            dirs = ["NW", "NE", "SW", "SE"]
        elif piece.color == Color.WHITE:
            dirs = ["NW", "NE"]
        else:
            dirs = ["SW", "SE"]
        
        for d in dirs:
            neighbor = neighbors.get(d)
            if neighbor is not None and board.get_piece(neighbor) is None:
                moves.append(Move(index, neighbor))
        
        return moves

    def get_king_simple_moves_for_piece(self, board, piece, index):
        moves = []
        dirs = ["NW", "NE", "SW", "SE"]
        
        for d in dirs:
            current = index
            while True:
                neighbors = board.get_diagonal_neighbors(current)
                next_idx = neighbors.get(d)
                if next_idx is None:
                    break
                if board.get_piece(next_idx) is not None:
                    break
                moves.append(Move(index, next_idx))
                current = next_idx
        
        return moves

    def get_all_capture_sequences(self, board, piece, index, captured_so_far=None, has_used_skip=False):
        if captured_so_far is None:
            captured_so_far = []

        # Junak jede samo u smeru kretanja (unapred); Kraljevic u svim pravcima
        if piece.is_king():
            dirs = ["NW", "NE", "SW", "SE"]
        elif piece.color == Color.WHITE:
            dirs = ["NW", "NE"]
        else:
            dirs = ["SW", "SE"]

        sequences = []
        neighbors = board.get_diagonal_neighbors(index)
        
        # Šarčev skok - skok preko svoje figure (jednom po potezu)
        has_sarac = piece.has_relic(RelicType.SARAC)

        for d in dirs:
            mid = neighbors.get(d)
            if mid is None or mid in captured_so_far:
                continue
            mid_piece = board.get_piece(mid)
            if mid_piece is None or mid_piece.color == piece.color:
                # Šarčev skok - preskoči sopstvenu figuru
                if has_sarac and not has_used_skip and mid_piece and mid_piece.color == piece.color:
                    mid_neighbors = board.get_diagonal_neighbors(mid)
                    landing = mid_neighbors.get(d)
                    if landing is not None and board.get_piece(landing) is None:
                        # Simuliraj skok
                        original_piece = board.get_piece(index)
                        board.remove_piece(index)
                        board.set_piece(landing, piece)
                        
                        further = self.get_all_capture_sequences(
                            board, piece, landing,
                            captured_so_far=captured_so_far,
                            has_used_skip=True  # Šarac se može koristiti samo jednom
                        )
                        
                        board.set_piece(index, original_piece)
                        board.remove_piece(landing)
                        
                        # Šarac je samo za pozicioniranje — dodaj samo ako postoji nastavak jedenja
                        if further:
                            for m in further:
                                sequences.append(Move(index, m.to_idx, captured=m.captured))
                continue
            
            if mid_piece.color != piece.color:
                # Toka od čelika — zaštićena figura ne može biti pojеdena
                if mid_piece.has_relic(RelicType.TOKA_OD_CELIKA):
                    continue
                mid_neighbors = board.get_diagonal_neighbors(mid)
                landing = mid_neighbors.get(d)
                if landing is None or board.get_piece(landing) is not None:
                    continue

                new_captured = captured_so_far + [mid]

                # Privremeno simuliraj skok na tabli za rekurziju
                original_piece = board.get_piece(index)
                board.remove_piece(index)
                board.remove_piece(mid)
                board.set_piece(landing, piece)

                further = self.get_all_capture_sequences(
                    board, piece, landing,
                    captured_so_far=new_captured,
                    has_used_skip=has_used_skip
                )

                # Vrati tablu u prethodno stanje
                board.set_piece(index, original_piece)
                board.set_piece(mid, mid_piece)
                board.remove_piece(landing)

                if further:
                    for m in further:
                        sequences.append(Move(index, m.to_idx, captured=m.captured))
                else:
                    sequences.append(Move(index, landing, captured=new_captured))

        return sequences

    def get_king_capture_sequences(self, board, piece, index, captured_so_far=None):
        if captured_so_far is None:
            captured_so_far = []

        dirs = ["NW", "NE", "SW", "SE"]
        sequences = []

        for d in dirs:
            current = index
            # Traži prvu protivničku figuru u ovom pravcu
            while True:
                neighbors = board.get_diagonal_neighbors(current)
                mid = neighbors.get(d)
                if mid is None or mid in captured_so_far:
                    break
                mid_piece = board.get_piece(mid)
                if mid_piece is not None and mid_piece.color == piece.color:
                    break
                if mid_piece is None:
                    current = mid
                    continue

                # Toka od čelika — zaštićena figura ne može biti pojеdena
                if mid_piece.has_relic(RelicType.TOKA_OD_CELIKA):
                    break

                # Pronašli smo protivničku figuru — traži sva polja za sletanje
                new_captured = captured_so_far + [mid]
                original_piece = board.get_piece(index)
                board.remove_piece(index)
                board.remove_piece(mid)

                landing_cursor = mid
                while True:
                    landing_neighbors = board.get_diagonal_neighbors(landing_cursor)
                    landing = landing_neighbors.get(d)
                    if landing is None or board.get_piece(landing) is not None:
                        break

                    board.set_piece(landing, piece)
                    further = self.get_king_capture_sequences(
                        board, piece, landing,
                        captured_so_far=new_captured
                    )
                    board.remove_piece(landing)

                    if further:
                        for m in further:
                            sequences.append(Move(index, m.to_idx, captured=m.captured))
                    else:
                        sequences.append(Move(index, landing, captured=new_captured))

                    landing_cursor = landing

                board.set_piece(index, original_piece)
                board.set_piece(mid, mid_piece)
                break

        return sequences

    def get_capture_moves(self, board, color):
        all_captures = []
        for idx, piece in board.get_all_pieces(color):
            # Koleb (Mešina rujnog vina) — figura ne može da skače/jede
            if piece.has_relic(RelicType.MESINA_RUJNOG_VINA):
                continue

            # Razorni udarac - direktno jedenje
            if piece.has_relic(RelicType.TOPUZ):
                all_captures.extend(self.get_direct_captures(board, piece, idx))
            elif piece.is_king():
                all_captures.extend(self.get_king_capture_sequences(board, piece, idx))
            else:
                all_captures.extend(self.get_all_capture_sequences(board, piece, idx))

        return all_captures
    
    def get_direct_captures(self, board, piece, index):
        """Direktno jedenje bez preskakanja - Topuz efekat"""
        moves = []
        neighbors = board.get_diagonal_neighbors(index)
        
        dirs = ["NW", "NE", "SW", "SE"] if piece.is_king() else (
            ["NW", "NE"] if piece.color == Color.WHITE else ["SW", "SE"]
        )
        
        for d in dirs:
            neighbor = neighbors.get(d)
            if neighbor is not None:
                enemy = board.get_piece(neighbor)
                if enemy and enemy.color != piece.color:
                    if enemy.has_relic(RelicType.TOKA_OD_CELIKA):
                        continue  # Toka blokira direktno jedenje
                    moves.append(Move(index, neighbor, captured=[neighbor]))
        
        return moves

    def get_simple_moves(self, board, color):
        all_moves = []
        for idx, piece in board.get_all_pieces(color):
            if piece.is_king():
                all_moves.extend(self.get_king_simple_moves_for_piece(board, piece, idx))
            else:
                all_moves.extend(self.get_simple_moves_for_piece(board, piece, idx))
        return all_moves

    def get_all_moves(self, board, color):
        captures = self.get_capture_moves(board, color)
        if captures:
            return captures
        return self.get_simple_moves(board, color)