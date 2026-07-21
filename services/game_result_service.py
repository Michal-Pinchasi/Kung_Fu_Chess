"""Coordinates one completed game without embedding SQL or ELO math in the server."""


class GameResultService:
    _SCORES = {"win": 1.0, "draw": 0.5, "loss": 0.0}

    def __init__(self, repository, calculator):
        self.repository = repository
        self.calculator = calculator

    def record(self, first, second, first_outcome: str):
        first_score = self._SCORES[first_outcome]
        second_outcome = {"win": "loss", "loss": "win", "draw": "draw"}[first_outcome]
        first_rating, second_rating = self.calculator.rated_pair(first.rating, second.rating, first_score)
        self.repository.update_game_result(first, second, first_rating, second_rating, first_outcome, second_outcome)
        return first_rating, second_rating
