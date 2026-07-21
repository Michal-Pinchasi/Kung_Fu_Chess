"""Pure, configurable ELO mathematics."""


class EloCalculator:
    def __init__(self, settings):
        self.settings = settings

    def expected_score(self, rating_a: int, rating_b: int) -> float:
        return 1.0 / (1.0 + self.settings.base ** ((rating_b - rating_a) / self.settings.rating_divisor))

    def new_rating(self, rating: int, opponent_rating: int, actual_score: float) -> int:
        expected = self.expected_score(rating, opponent_rating)
        return round(rating + self.settings.k_factor * (actual_score - expected))

    def rated_pair(self, first_rating: int, second_rating: int, first_score: float) -> tuple[int, int]:
        second_score = 1.0 - first_score
        return (self.new_rating(first_rating, second_rating, first_score),
                self.new_rating(second_rating, first_rating, second_score))
