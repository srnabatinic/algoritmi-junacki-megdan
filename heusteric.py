from piece import Color, PieceType

class Heuristic:

    MATERIAL_VALUES = {
        PieceType.JUNAK: 1.0,
        PieceType.KRALJEVIC: 3.5,
        PieceType.MARKO_KRALJEVIC: 6.5,
    }

    POSITION_WEIGHTS = [
        0.0, 0.3, 0.0, 0.3,
        0.3, 0.0, 0.3, 0.0,
        0.0, 0.5, 0.0, 0.5,
        0.5, 0.0, 0.7, 0.0,
        0.0, 0.7, 0.0, 0.5,
        0.5, 0.0, 0.5, 0.0,
        0.0, 0.3, 0.0, 0.3,
        0.3, 0.0, 0.3, 0.0,
    ]

    def evaluate(self, board, color) -> float:
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        score = 0
        score += self.material_score(board, color)
        score += self.position_score(board, color)
        score += self.advancement_score(board, color)
        score += self.formation_score(board, color)
        score += self.endgame_score(board, color, opponent)
        return score

    def evaluate_with_mobility(self, board, color):
        from move_generator import MoveGenerator
        mg = MoveGenerator()
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        base = self.evaluate(board, color)
        my_moves = len(mg.get_all_moves(board, color))
        opp_moves = len(mg.get_all_moves(board, opponent))
        mobility = (my_moves - opp_moves) * 0.05
        return base + mobility, {
            "materijal": self.material_score(board, color),
            "pozicija": self.position_score(board, color),
            "napredovanje": self.advancement_score(board, color),
            "formacija": self.formation_score(board, color),
            "završnica": self.endgame_score(board, color, opponent),
            "mobilnost": mobility,
            "ukupno": base + mobility
        }

    def material_score(self, board, color):
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        def count(clr):
            score = 0
            for _, piece in board.get_all_pieces(clr):
                score += self.MATERIAL_VALUES.get(piece.type, 0)
            return score
        return count(color) - count(opponent)

    def position_score(self, board, color):
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        def count(clr):
            return sum(self.POSITION_WEIGHTS[idx] for idx, _ in board.get_all_pieces(clr))
        return count(color) - count(opponent)

    def advancement_score(self, board, color):
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        def count(clr):
            score = 0
            for idx, piece in board.get_all_pieces(clr):
                if piece.type != PieceType.JUNAK:
                    continue
                row, _ = board.index_to_row_col(idx)
                # Za bele: više napredovanja prema redu 0 = bolje
                # Za crne: više napredovanja prema redu 7 = bolje
                # Normalizuj tako da su oba tima simetrična
                if clr == Color.WHITE:
                    advancement = (7 - row) / 7.0  # 0 (red 7) do 1 (red 0)
                else:
                    advancement = row / 7.0  # 0 (red 0) do 1 (red 7)
                score += advancement * 0.5
            return score
        return count(color) - count(opponent)

    def formation_score(self, board, color):
        """Boduje figuri ako ima drugih figuri u zajednickoj poziciji (ne samo na ledjima)"""
        opponent = Color.BLACK if color == Color.WHITE else Color.WHITE
        score = 0
        for idx, piece in board.get_all_pieces(color):
            neighbors = board.get_diagonal_neighbors(idx)
            # Proverite sve 4 smjera - ne samo ledje
            for dir_name in ["NW", "NE", "SW", "SE"]:
                neighbor_idx = neighbors.get(dir_name)
                if neighbor_idx is not None:
                    neighbor_piece = board.get_piece(neighbor_idx)
                    if neighbor_piece and neighbor_piece.color == color:
                        score += 0.1
        
        opp_score = 0
        for idx, piece in board.get_all_pieces(opponent):
            neighbors = board.get_diagonal_neighbors(idx)
            for dir_name in ["NW", "NE", "SW", "SE"]:
                neighbor_idx = neighbors.get(dir_name)
                if neighbor_idx is not None:
                    neighbor_piece = board.get_piece(neighbor_idx)
                    if neighbor_piece and neighbor_piece.color == opponent:
                        opp_score += 0.1
        
        return score - opp_score

    def endgame_score(self, board, color, opponent):
        my_count = len(board.get_all_pieces(color))
        opp_count = len(board.get_all_pieces(opponent))
        
        # Ako nema više figura, igra je gotova
        if my_count == 0:
            return -100
        if opp_count == 0:
            return 100
        
        # U završnici, budi agresivniji
        piece_diff = my_count - opp_count
        base_score = piece_diff * 2.0
        
        # Ako si u većini, kažnjava ako nemaš dovoljno king/marko figuri
        if my_count > opp_count:
            my_kings = sum(1 for _, p in board.get_all_pieces(color) if p.is_king())
            if my_kings == 0:
                base_score -= 1.5
        
        # Ako si u manjini, pokušaj da napraviš king
        if opp_count > my_count:
            my_kings = sum(1 for _, p in board.get_all_pieces(color) if p.is_king())
            if my_kings > 0:
                base_score += 2.0
        
        return base_score
