import sys
from storage.board_parser import BoardParser
from storage.board_printer import BoardPrinter
from engin.game_engine import GameEngine
from input.controller import Controller

def run_game_from_text(input_text: str):
    lines = input_text.strip().split("\n")
    board_lines = []
    command_lines = []
    
    in_commands = False
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
        if cleaned_line.startswith("Commands:"):
            in_commands = True
            continue
        if cleaned_line.startswith("Board:"):
            continue
            
        if not in_commands:
            board_lines.append(cleaned_line)
        else:
            command_lines.append(cleaned_line)

    board_text = "\n".join(board_lines)
    
    # 1. טיפול בשגיאות טעינת הלוח בהתאם לדרישות האתר
    try:
        board = BoardParser.parse(board_text)
    except ValueError as e:
        err_msg = str(e)
        if "Inconsistent row lengths" in err_msg:
            print("ERROR ROW_WIDTH_MISMATCH")
        elif "Unknown piece token" in err_msg or "Invalid piece token" in err_msg:
            print("ERROR UNKNOWN_TOKEN")
        else:
            print("ERROR")
        return

    # אתחול הרכיבים
    engine = GameEngine(board)
    controller = Controller(engine)
    
    # 2. הרצת פקודות כולל פקודות לחיצה (click)
    for cmd in command_lines:
        parts = cmd.strip().split()
        if not parts:
            continue
            
        cmd_type = parts[0].lower()
        
        if cmd_type == "print" and len(parts) > 1 and parts[1].lower() == "board":
            print(BoardPrinter.print_board(board))
        elif cmd_type == "click":
            try:
                x = int(parts[1])
                y = int(parts[2])
                controller.click(x, y)
            except (IndexError, ValueError):
                pass
        else:
            engine.execute_command(cmd)

def main():
    input_data = sys.stdin.read()
    if input_data.strip():
        run_game_from_text(input_data)

if __name__ == "__main__":
    main()