from config.multiplayer_settings import EloSettings, MultiplayerSettings, PasswordSettings
from services.auth_service import AuthError, AuthService
from services.elo_calculator import EloCalculator
from services.game_result_service import GameResultService
from storage.user_repository import UserRepository


def settings(tmp_path):
    return MultiplayerSettings(
        database_path=str(tmp_path / "users.sqlite3"),
        elo=EloSettings(starting_rating=1200, k_factor=32.0, rating_divisor=400.0, base=10.0),
        password=PasswordSettings(algorithm="sha256", iterations=1000, salt_bytes=16, derived_key_bytes=32),
        session_token_bytes=16,
    )


def test_registration_hashes_password_and_assigns_1200(tmp_path):
    config = settings(tmp_path)
    repository = UserRepository(config.database_path)
    repository.initialize()
    user = AuthService(repository, config).register("michal", "secret")
    assert user.rating == 1200
    assert user.password_hash != "secret"
    assert repository.get_by_username("michal").password_salt


def test_login_uses_secure_verification_and_returns_token(tmp_path):
    config = settings(tmp_path)
    repository = UserRepository(config.database_path)
    repository.initialize()
    auth = AuthService(repository, config)
    auth.register("white", "correct-password")
    user, token = auth.login("white", "correct-password")
    assert auth.user_for_token(token) == user
    try:
        auth.login("white", "wrong-password")
        assert False, "wrong password must not log in"
    except AuthError as error:
        assert str(error) == "invalid_credentials"


def test_elo_formula_and_rated_result():
    calculator = EloCalculator(EloSettings(starting_rating=1200, k_factor=32.0, rating_divisor=400.0, base=10.0))
    assert calculator.expected_score(1200, 1200) == 0.5
    assert calculator.rated_pair(1200, 1200, 1.0) == (1216, 1184)
    assert calculator.rated_pair(1200, 1200, 0.5) == (1200, 1200)


def test_result_service_updates_ratings_and_stats(tmp_path):
    config = settings(tmp_path)
    repository = UserRepository(config.database_path)
    repository.initialize()
    auth = AuthService(repository, config)
    white, black = auth.register("white", "password"), auth.register("black", "password")
    GameResultService(repository, EloCalculator(config.elo)).record(white, black, "win")
    assert repository.get_by_username("white").wins == 1
    assert repository.get_by_username("white").rating == 1216
    assert repository.get_by_username("black").losses == 1
