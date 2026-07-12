from model.position import Position
from input.board_mapper import BoardMapper

class Controller:
    def __init__(self, game_engine):
        self.game_engine = game_engine
        self.selected_cell = None # שומר את ה-Position של הכלי הנבחר כרגע

    def click(self, x: int, y: int):
        """
        מטפל בלחיצת עכבר ומיישם את מדיניות הבחירה והמהלכים של המשחק.
        """
        width = self.game_engine.board.width
        height = self.game_engine.board.height
        
        # המרת הפיקסלים למיקום לוגי בעזרת ה-Mapper
        clicked_pos = BoardMapper.pixel_to_cell(x, y, width, height)

        # אם אין בחירה כרגע
        if self.selected_cell is None:
            # לחיצה מחוץ ללוח כשאין בחירה - מתעלמים
            if clicked_pos is None:
                return
            
            # בדיקה האם יש כלי במשבצת שנלחצה
            piece = self.game_engine.board.get_piece(clicked_pos.row, clicked_pos.col)
            if piece != ".":
                self.selected_cell = clicked_pos # לחיצה ראשונה על כלי - מסמנים כנבחר
        
        # אם יש כלי נבחר כרגע
        else:
            # לחיצה מחוץ ללוח כשיש כלי נבחר - מבטלת את הבחירה
            if clicked_pos is None:
                self.selected_cell = None
                return
            
            # לחיצה שנייה בתוך הלוח - שולחים בקשת מהלך ומנקים מיד את הבחירה
            self.game_engine.request_move(self.selected_cell, clicked_pos)
            self.selected_cell = None