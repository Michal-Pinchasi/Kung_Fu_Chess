import sys
from serializer import TextBoardSerializer
# Git Repository URL: https://github.com/Michal-Pinchasi/Kung_Fu_Chess
def main():
    input_data = sys.stdin.read()
    if not input_data.strip():
        return

    board = TextBoardSerializer.parse(input_data)

    if "print board" in input_data:
        canonical_board = TextBoardSerializer.serialize(board)
        print(canonical_board)

if __name__ == "__main__":
    main()