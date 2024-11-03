import pytest
import pytest_mock

from wordall.games import numberle


class TestInit:
    @pytest.mark.parametrize(
        ("target_word_length", "expected_range"), [(3, 1000), (5, 100000)]
    )
    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        target_word_length: int,
        expected_range: int,
    ) -> None:
        mock_randrange = mocker.patch("random.randrange")
        mock_randrange.return_value = expected_range - 1

        numberle_game = numberle.NumberleGame(
            guess_limit=3, target_word_length=target_word_length
        )

        mock_randrange.assert_called_once_with(expected_range)
        assert int(numberle_game.target) == mock_randrange.return_value

    def test_fills_target_zeroes(self, mocker: pytest_mock.MockerFixture) -> None:
        mock_randrange = mocker.patch("random.randrange")
        mock_randrange.return_value = 1

        numberle_game = numberle.NumberleGame(guess_limit=3, target_word_length=5)

        assert numberle_game.target == "00001"


class TestIsValidWord:
    def test_accepts_valid_word(
        self, numberle_game_instance_5_digit: numberle.NumberleGame
    ) -> None:
        assert numberle_game_instance_5_digit.is_valid_word("97531")

    def test_rejects_invalid_word(
        self, numberle_game_instance_5_digit: numberle.NumberleGame
    ) -> None:
        assert not numberle_game_instance_5_digit.is_valid_word("ABCDE")

    def test_rejects_mixed_invalid_word(
        self, numberle_game_instance_5_digit: numberle.NumberleGame
    ) -> None:
        assert not numberle_game_instance_5_digit.is_valid_word("1234A")

    def test_rejects_wrong_length_word(
        self, numberle_game_instance_5_digit: numberle.NumberleGame
    ) -> None:
        assert not numberle_game_instance_5_digit.is_valid_word("123")
