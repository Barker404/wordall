from unittest import mock

import pytest_mock

from wordall.games import wordle


class TestGameInit:
    def test_loads_word_dictionary(
        self, mock_valid_dictionary_word_loader_5_letter: mock.MagicMock
    ) -> None:
        loader_mock = mock_valid_dictionary_word_loader_5_letter
        wordle_game = wordle.WordleGame(loader_mock, target_word_length=5)

        loader_mock.get_word_dictionary.assert_called_once_with(
            word_transform_function=str.upper,
            word_filter_function=mock.ANY,
        )
        assert (
            wordle_game.word_dictionary == loader_mock.get_word_dictionary.return_value
        )

    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_valid_dictionary_word_loader_5_letter: mock.MagicMock,
    ) -> None:
        mock_choice = mocker.patch("random.choice")
        mock_choice.return_value = "APPLE"

        wordle_game = wordle.WordleGame(
            mock_valid_dictionary_word_loader_5_letter, target_word_length=5
        )

        assert len(mock_choice.call_args_list) == 1
        assert len(mock_choice.call_args_list[0].args) == 1
        assert set(mock_choice.call_args_list[0].args[0]) == {"APPLE", "BREAD", "CHIPS"}
        assert wordle_game.target == mock_choice.return_value


class TestIsValidWord:
    def test_accepts_valid_word(
        self, wordle_game_instance_5_letter: wordle.WordleGame
    ) -> None:
        assert wordle_game_instance_5_letter.is_valid_word("APPLE")

    def test_rejects_invalid_word(
        self, wordle_game_instance_5_letter: wordle.WordleGame
    ) -> None:
        assert not wordle_game_instance_5_letter.is_valid_word("ABCDE")

    def test_rejects_wrong_length_word(
        self, wordle_game_instance_5_letter: wordle.WordleGame
    ) -> None:
        assert not wordle_game_instance_5_letter.is_valid_word("EGGS")
