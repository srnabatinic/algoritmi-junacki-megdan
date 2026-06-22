from enum import Enum
from collections import deque

class RelicType(Enum):
    TOKA_OD_CELIKA = "Toka od čelika"           # Oklop
    MESINA_RUJNOG_VINA = "Mešina rujnog vina"   # Pogled ispod obрva
    TOPUZ = "Topuž"                              # Razorni udarac
    SARAC = "Šarac"                              # Šarčev skok
    TRI_TOVARA_BLAGA = "Tri tovara blaga"       # Krunjenje


class RelicEffect:
    """Sistemski efekt - svojstvo koje je dodata figuri"""
    
    def __init__(self, relic_type, duration):
        self.relic_type = relic_type
        self.duration = duration  # koliko poteza traje
    
    def tick(self):
        """Smanji trajanje - zove se na kraju tuđeg poteza"""
        self.duration -= 1
    
    def is_active(self):
        return self.duration > 0
    
    def __repr__(self):
        return f"{self.relic_type.value}(traje {self.duration})"


class RelicDeck:
    """Deque sa relikviјama - Carev Drum"""
    
    # Predefinisan redosled relikviјa koji kružno ulaze
    RELIC_CYCLE = [
        RelicType.TOKA_OD_CELIKA,
        RelicType.MESINA_RUJNOG_VINA,
        RelicType.TOPUZ,
        RelicType.SARAC,
        RelicType.TRI_TOVARA_BLAGA,
    ]
    
    def __init__(self):
        self.deck = deque()
        self.cycle_index = 0
    
    def advance_turn(self):
        """Na početku svakog poteza, ubaci novu relikviјu na front; kapacitet 5."""
        new_relic = self.RELIC_CYCLE[self.cycle_index]
        self.deck.appendleft(new_relic)
        if len(self.deck) > 5:
            self.deck.pop()  # Ispusti najstariji (rear) ako prelazimo kapacitet
        self.cycle_index = (self.cycle_index + 1) % len(self.RELIC_CYCLE)
    
    def get_front(self):
        """Uzmi relikviјu sa frontu (može se aktivirati)"""
        return self.deck[0] if self.deck else None
    
    def get_rear(self):
        """Uzmi relikviјu sa kraja (može se aktivirati)"""
        return self.deck[-1] if self.deck else None
    
    def activate_front(self):
        """Aktiviraj front i ukloni ga iz deck-a"""
        if self.deck:
            relic = self.deck.popleft()
            return relic
        return None
    
    def activate_rear(self):
        """Aktiviraj rear i ukloni ga iz deck-a"""
        if self.deck:
            relic = self.deck.pop()
            return relic
        return None
    
    def __repr__(self):
        return f"RelicDeck({list(self.deck)})"


def get_relic_duration(relic_type, is_marko=False):
    """Vrati koliko poteza traje efekat relikviјe"""
    durations = {
        RelicType.TOKA_OD_CELIKA: 2 if is_marko else 1,  # Oklop: 1 protivnički potez (2 za Marka)
        RelicType.MESINA_RUJNOG_VINA: 3,  # Koleb: 3 da preživi odmah-tick, efektivno 2 neprijateljeva poteza
        RelicType.TOPUZ: 2,    # Razorni udarac: 2 da preživi protivnikov tick pre sledećeg sopstvenog poteza
        RelicType.SARAC: 2,    # Šarčev skok: 2 da preživi protivnikov tick pre sledećeg sopstvenog poteza
        RelicType.TRI_TOVARA_BLAGA: -1,  # Krunisanje: trajno (promocija je ireverzibilna)
    }
    return durations.get(relic_type, 1)
