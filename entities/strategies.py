def king_move_strategy(from_pos, to_pos) -> bool:
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    return delta_row <= 1 and delta_col <= 1

def rook_move_strategy(from_pos, to_pos) -> bool:
    return from_pos.row == to_pos.row or from_pos.col == to_pos.col

def bishop_strategy(from_pos, to_pos) -> bool:
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    return delta_row == delta_col

def queen_strategy(from_pos, to_pos) -> bool:
    return rook_move_strategy(from_pos, to_pos) or bishop_strategy(from_pos, to_pos)

def knight_strategy(from_pos, to_pos) -> bool:
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    return (delta_row == 2 and delta_col == 1) or (delta_row == 1 and delta_col == 2)

# מפת האסטרטגיות המקשרת בין האות של הכלי לפונקציית החישוב שלו
STRATEGIES_MAP = {
    "K": king_move_strategy,
    "R": rook_move_strategy,
    "B": bishop_strategy,
    "Q": queen_strategy,
    "N": knight_strategy,
}