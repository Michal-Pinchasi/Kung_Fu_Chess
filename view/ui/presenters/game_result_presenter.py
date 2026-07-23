"""Converts authoritative network results into overlay renderer arguments."""


class GameResultPresenter:
    def __init__(self, renderer):
        self._renderer = renderer

    def draw(self, frame, client) -> None:
        if not client.game_result:
            return
        outcome = client.game_result["outcome"]
        winner = client.game_result.get("winner")
        if outcome == "draw":
            self._renderer.draw_match_result(
                frame, None, None, is_draw=True
            )
            return
        winner_name, winner_color = self._winner(client, outcome, winner)
        self._renderer.draw_match_result(frame, winner_name, winner_color)

    @staticmethod
    def _winner(client, outcome, winner):
        if winner:
            return winner["username"], winner["color"]
        if outcome == "win":
            color = "WHITE" if client.color == "w" else "BLACK"
            return client.username, color
        opponent = client.opponent or {"username": "OPPONENT"}
        color = "BLACK" if client.color == "w" else "WHITE"
        return opponent["username"], color
