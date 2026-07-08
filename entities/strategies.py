def _path_is_clear(from_pos, to_pos, board) -> bool:
    """בודק שכל המשבצות בין from_pos ל-to_pos (לא כולל הקצוות) ריקות."""
    row_step = 0 if from_pos.row == to_pos.row else (1 if to_pos.row > from_pos.row else -1)
    col_step = 0 if from_pos.col == to_pos.col else (1 if to_pos.col > from_pos.col else -1)

    cur_row = from_pos.row + row_step
    cur_col = from_pos.col + col_step

    while (cur_row, cur_col) != (to_pos.row, to_pos.col):
        if board.get_piece(cur_row, cur_col) != ".":
            return False
        cur_row += row_step
        cur_col += col_step

    return True


def king_move_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    return delta_row <= 1 and delta_col <= 1


def rook_move_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    if from_pos.row != to_pos.row and from_pos.col != to_pos.col:
        return False
    if board is None:
        return True
    return _path_is_clear(from_pos, to_pos, board)


def bishop_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    if delta_row != delta_col:
        return False
    if board is None:
        return True
    return _path_is_clear(from_pos, to_pos, board)


def queen_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    return rook_move_strategy(from_pos, to_pos, board) or bishop_strategy(from_pos, to_pos, board)


def knight_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    # פרש קופץ מעל כלים — אין בדיקת מסלול
    delta_row = abs(from_pos.row - to_pos.row)
    delta_col = abs(from_pos.col - to_pos.col)
    return (delta_row == 2 and delta_col == 1) or (delta_row == 1 and delta_col == 2)


def pawn_strategy(from_pos, to_pos, board=None, piece=None) -> bool:
    """
    חוקי תנועה מלאים לרגלי:
    - לבן זז למעלה (row -= 1), שחור זז למטה (row += 1)
    - קדימה (אותה עמודה): חוקי רק אם היעד ריק
    - אלכסון (עמודה שכנה): חוקי רק אם ביעד יש כלי אויב
    """
    if piece is None or board is None:
        return False

    direction = -1 if piece.color == "w" else 1
    row_diff = to_pos.row - from_pos.row
    col_diff = abs(to_pos.col - from_pos.col)

    # חייב לזוז בדיוק שורה אחת בכיוון הנכון
    if row_diff != direction:
        return False

    target = board.get_piece(to_pos.row, to_pos.col)

    if col_diff == 0:
        # תנועה קדימה — חוקית רק אם היעד ריק
        return target == "."

    if col_diff == 1:
        # אכילה באלכסון — חוקית רק אם יש כלי אויב ביעד
        return (target != "." and hasattr(target, 'color') and target.color != piece.color)

    return False


# מפת האסטרטגיות המקשרת בין האות של הכלי לפונקציית החישוב שלו
STRATEGIES_MAP = {
    "K": king_move_strategy,
    "R": rook_move_strategy,
    "B": bishop_strategy,
    "Q": queen_strategy,
    "N": knight_strategy,
    "P": pawn_strategy,
}