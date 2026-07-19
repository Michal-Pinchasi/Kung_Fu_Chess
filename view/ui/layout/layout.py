class Layout:
    """
    Single source of truth for all UI geometry.
    """

    WINDOW_WIDTH  = 1600
    WINDOW_HEIGHT = 900

    # Board settings
    BOARD_SIZE    = 800
    BOARD_X       = 250
    BOARD_Y       = 50
    
    # Board logic constants
    BOARD_ROWS    = 8
    BOARD_COLS    = 8
    BOARD_BORDER  = 80
    SQUARE_SIZE   = 80 # (= (800 - 2*80) / 8)
    
    # UI derived constants
    SQUARE_CENTER_OFFSET = SQUARE_SIZE // 2

    # Move-history side panels
    WHITE_PANEL_X = 25
    WHITE_PANEL_Y = BOARD_Y
    BLACK_PANEL_X = BOARD_X + BOARD_SIZE + 25
    BLACK_PANEL_Y = BOARD_Y

    MOVE_PANEL_WIDTH  = 200
    MOVE_PANEL_HEIGHT = BOARD_SIZE

    MOVE_TEXT_X_OFFSET      = 10
    MOVE_TEXT_Y_OFFSET      = 45
    MOVE_TEXT_LINE_HEIGHT   = 20
    MOVE_TEXT_COLOR         = (255, 255, 255, 255)
    MOVE_FONT_SIZE          = 0.45

    # Panel styling — shared by the move list and the score line
    PANEL_BACKGROUND_COLOR  = (50, 50, 50, 255)
    PANEL_BACKGROUND_ALPHA  = 0.7
    PANEL_BORDER_COLOR      = (200, 200, 200, 255)
    PANEL_BORDER_THICKNESS  = 2
    PANEL_SEPARATOR_MARGIN  = 5
    SEPARATOR_LINE_HEIGHT   = 1
    MOVE_TITLE_FONT_SIZE    = 0.6
    MOVE_TITLE_Y_OFFSET     = 15
    MOVE_SEPARATOR_Y_OFFSET = 25
    MOVE_TEXT_THICKNESS     = 1

    # Score line
    SCORE_FONT_SIZE       = 0.7
    SCORE_TEXT_COLOR      = (0, 215, 255, 255)
    SCORE_TEXT_THICKNESS  = 2
    SCORE_BOTTOM_MARGIN   = 35
    SCORE_SEPARATOR_GAP   = 20