import pytest
from model.position import Position
from input.board_mapper import BoardMapper

def test_pixel_to_cell_mapping():
    # בדיקה שקואורדינטות בתוך הריבוע הראשון ממופות לשורה 0, עמודה 0
    assert BoardMapper.pixel_to_cell(50, 50, width=8, height=8) == Position(0, 0)
    
    # בדיקה ש-x=150 (עמודה 1) ו-y=50 (שורה 0) ממופים נכון
    assert BoardMapper.pixel_to_cell(150, 50, width=8, height=8) == Position(0, 1)
    
    # בדיקה ש-x=50 (עמודה 0) ו-y=150 (שורה 1) ממופים נכון
    assert BoardMapper.pixel_to_cell(50, 150, width=8, height=8) == Position(1, 0)

def test_outside_board_clicks():
    # לחיצה במיקום שלילי היא מחוץ ללוח
    assert BoardMapper.pixel_to_cell(-10, 50, width=8, height=8) is None
    
    # לחיצה מעבר לגבולות הלוח (מעבר ל-800 פיקסלים בלוח של 8X8)
    assert BoardMapper.pixel_to_cell(850, 400, width=8, height=8) is None