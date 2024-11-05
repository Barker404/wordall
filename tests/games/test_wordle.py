import pathlib
from unittest import mock

import pytest
import pytest_mock

from wordall.games import wordle


class TestGameInit:
    def test_loads_word_dictionary(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordle.WordleGame(dictionary_file_path, target_word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_skips_empty_lines_in_dictionary(
        self,
        mock_valid_empty_line_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_empty_line_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordle.WordleGame(dictionary_file_path, target_word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_raises_exception_on_non_alphabet_dictionary_word(
        self,
        mock_invalid_character_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(wordle.InvalidDictionaryFileError):
            wordle.WordleGame(pathlib.Path("/a/b/c"))

    def test_raises_exception_on_empty_dictionary(
        self,
        mock_empty_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(wordle.InvalidDictionaryFileError):
            wordle.WordleGame(pathlib.Path("/a/b/c"))

    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        _, file_word_list = mock_valid_dictionary_file

        mock_choice = mocker.patch("random.choice")

        wordle_game = wordle.WordleGame(pathlib.Path("/a/b/c"), target_word_length=5)

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
