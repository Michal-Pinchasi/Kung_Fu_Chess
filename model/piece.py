class Piece:
    def __init__(self, id: str, kind, color):
        self.id = id          # המזהה הייחודי של הכלי (למשל: "w_pawn1")
        self.kind = kind      # סוג הכלי (ROOK, PAWN וכדומה)
        self.color = color    # צבע הכלי (WHITE, BLACK)
        self.state = "idle"   # מצב הכלי (idle או moving)
        self.cell = None      # המיקום הנוכחי שלו על הלוח