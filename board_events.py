"""
Upravljanje posebnim dogadjajima na tabli:
- Brazde mehanika
- Relikviјe aktivacija
- Marko Kraljević promocija
"""

class BrazdeLocations:
    """Brazde su specijalna polja gde se aktiviraju relikviјe"""
    BRAZDE_INDICES = []  # Inicijalizuj u game_loop kada znaš board
    
    @staticmethod
    def is_brazda(index, board):
        """Proverite je li polje Brazda"""
        row, col = board.index_to_row_col(index)
        return (row, col) == (3, 0) or (row, col) == (4, 7)


class RelicActivationSystem:
    """Sistem za aktivaciju relikviјa kada figura stigne na Brazdu"""
    
    def __init__(self, relic_deck):
        self.deck = relic_deck
    
    def check_brazda_activation(self, board, piece, from_idx, to_idx):
        """
        Ako je figura završila potez na Brazdi, vrati relikviјe
        koje mogu da se aktiviraju - igrač bira front ili rear
        """
        if BrazdeLocations.is_brazda(to_idx, board):
            front = self.deck.get_front()
            rear = self.deck.get_rear()
            return (front, rear)             # Igrač može da bira između ova dva
        return None
    
    def activate_relic_on_piece(self, piece, relic_type):
        """Evidentira relikviju na figuri za Marko proveru (efekti se primenjuju u game_loop)."""
        piece.relics.add(relic_type)

    def check_marko_promotion(self, piece):
        """
        Proverava da li figura ima sve 4 relikvije za Marko promociju.
        Koristi piece.relics (sve ikad aktivirane), jer Mesina efekt odlazi na protivnika.
        """
        from relics import RelicType
        required_relics = {
            RelicType.TRI_TOVARA_BLAGA,
            RelicType.SARAC,
            RelicType.TOPUZ,
            RelicType.MESINA_RUJNOG_VINA,
        }
        if required_relics.issubset(piece.relics):
            piece.promote_to_marko()
            return True
        return False
