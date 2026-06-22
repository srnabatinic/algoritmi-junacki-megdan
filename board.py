from piece import Color, Piece, PieceType
import copy

class Board:
    
    ACTIVE_SQUARES = 32
    
    def __init__(self):
        self.board = [None] * self.ACTIVE_SQUARES
    
    def row_col_to_index(self, row, col):
        if (row + col) % 2 == 1:
            return (row * 4) + (col // 2)
        return None
    
    def index_to_row_col(self, index):
        row = index // 4
        col = (index % 4) * 2 + ((row + 1) % 2)
        return row, col
    
    def get_piece(self, index):
        return self.board[index]

    def set_piece(self, index, piece):
        self.board[index] = piece
    
    def setup_initial_position(self):
        for i in range(12):
            self.board[i] = Piece(Color.BLACK, PieceType.JUNAK)
        for i in range(20, 32):
            self.board[i] = Piece(Color.WHITE, PieceType.JUNAK)
            
    def remove_piece(self, index):
        self.board[index] = None
    
    def is_valid_index(self, index):
        return 0 <= index < 32

    def get_all_pieces(self, color):
        return [(i, piece) for i, piece in enumerate(self.board) 
                if piece and piece.color == color]

    def copy(self):
        new_board = Board()
        new_board.board = [copy.deepcopy(piece) for piece in self.board]
        return new_board
    
    def get_diagonal_neighbors(self, index):
        row, col = self.index_to_row_col(index)
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        neighbors = {}
        dir_names = ["NW", "NE", "SW", "SE"]
        
        for (dr, dc), name in zip(directions, dir_names):
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                neighbor_index = self.row_col_to_index(new_row, new_col)
                if neighbor_index is not None:
                    neighbors[name] = neighbor_index
            else:
                neighbors[name] = None
        
        return neighbors
    
    def is_brazda(self, index):
        return self.index_to_row_col(index) in [(3, 0), (4, 7)]