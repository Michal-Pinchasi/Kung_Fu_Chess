import sys
from serializer import TextBoardSerializer
from engine import GameEngine

def main():
    # 1. קריאת כל הקלט
    input_data = sys.stdin.read()
    if not input_data.strip():
        return

    # 2. בניית הלוח הראשוני (איטרציה 1)
    board = TextBoardSerializer.parse(input_data)
    engine = GameEngine(board)

    # 3. חילוץ והרצת הפקודות דרך ה-Engine
    lines = input_data.split("\n")
    in_commands_section = False
    
    for line in lines:
        line_stripped = line.strip()
        if line_stripped.startswith("Commands:"):
            in_commands_section = True
            continue
        if in_commands_section and line_stripped:
            # ה-Engine לוקח אחריות מלאה על הפקודה!
            engine.execute_command(line_stripped)

if __name__ == "__main__":
    main()