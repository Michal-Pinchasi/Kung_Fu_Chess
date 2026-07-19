class Layout:
    """
    Single source of truth for all UI geometry.

    BOARD_X / BOARD_Y     : top-left corner of the board image on the window.
    BOARD_SIZE            : board image is scaled to this size (pixels).
    BOARD_BORDER          : measured border width inside the board image.
                            The actual playing squares start at
                            (BOARD_X + BOARD_BORDER, BOARD_Y + BOARD_BORDER).
    SQUARE_SIZE           : size of one chess square in pixels
                            (= (BOARD_SIZE - 2 * BOARD_BORDER) / 8).
    """

    WINDOW_WIDTH  = 1600
    WINDOW_HEIGHT = 900

    BOARD_SIZE   = 800
    BOARD_X      = 250
    BOARD_Y      = 50

    # Measured from board.jpg at 800×800:
    # First square boundary at x=80, last at x=640 → 8 squares × 80px
    BOARD_BORDER  = 80          # pixels from board edge to first square
    SQUARE_SIZE   = 80          # pixels per square  (= (800 - 2*80) / 8)

    # Move-history side panels (white on the left, black on the right).
    WHITE_PANEL_X = 25
    WHITE_PANEL_Y = BOARD_Y
    BLACK_PANEL_X = BOARD_X + BOARD_SIZE + 25
    BLACK_PANEL_Y = BOARD_Y

    MOVE_PANEL_WIDTH  = 200
    MOVE_PANEL_HEIGHT = BOARD_SIZE

    MOVE_TEXT_X_OFFSET    = 10
    MOVE_TEXT_Y_OFFSET    = 45
    MOVE_TEXT_LINE_HEIGHT = 20
    MOVE_TEXT_COLOR       = (255, 255, 255, 255)
    MOVE_FONT_SIZE        = 0.45

    # Score line at the bottom of each move-history panel.
    SCORE_FONT_SIZE      = 0.7
    SCORE_TEXT_COLOR     = (0, 215, 255, 255)   # gold — stands out from the move list
    SCORE_TEXT_THICKNESS = 2
    SCORE_BOTTOM_MARGIN  = 35                    # px from the panel's bottom edge
