import pathlib
from collections import abc as collections_abc
from typing import Any
from unittest import mock

import pytest
import pytest_mock

from wordall import wordall


@pytest.fixture
def mock_valid_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, set[str]]:
    return _mock_dictionary_file_helper(["APPLE", "BREAD", "CHIPS"], mocker)


@pytest.fixture
def mock_invalid_character_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, set[str]]:
    return _mock_dictionary_file_helper(["APPLE", "BREA8", "CHIPS"], mocker)


@pytest.fixture
def mock_empty_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, set[str]]:
    return _mock_dictionary_file_helper([], mocker)


def _mock_dictionary_file_helper(
    word_list: collections_abc.Iterable[str], mocker: pytest_mock.MockerFixture
) -> tuple[mock.MagicMock, set[str]]:
    word_list_data = "\n".join(word_list)

    # Pathlib uses an open *method*, so to be able to inspect the Path object that
    # open() was called on we need to ensure self is passed to it, which requires
    # binding to the instance. Wrapping the mock object in a function allows this to
    # happen.
    open_mock = mocker.mock_open(read_data=word_list_data)

    def open_mock_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        return open_mock(self, *args, **kwargs)

    mocker.patch("pathlib.Path.open", open_mock_wrapper)
    return open_mock, set(word_list)


class TestIsWordInAlphabet:
    @pytest.fixture
    def non_abstract_game(self, mocker: pytest_mock.MockerFixture) -> wordall.Game:
        # Patch Game so that we can directly create an instance without needing a
        # subclass
        mocker.patch.multiple(wordall.Game, __abstractmethods__=set())
        game = wordall.Game()  # type: ignore # Mypy thinks this is still abstract
        return game

    def test_is_in_alphabet(self, non_abstract_game: wordall.Game) -> None:
        assert non_abstract_game.is_word_in_alphabet("BAED")

    def test_not_in_alphabet(self, non_abstract_game: wordall.Game) -> None:
        assert not non_abstract_game.is_word_in_alphabet("AB1")


class TestWordleGameInit:
    def test_loads_word_dictionary(
        self,
        mock_valid_dictionary_file: tuple[
            mock.MagicMock, collections_abc.Iterable[str]
        ],
    ) -> None:
        open_mock, word_dictionary = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordall.WordleGame(dictionary_file_path, 0)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == word_dictionary

    def test_raises_exception_on_non_alphabet_dictionary_word(
        self,
        mock_invalid_character_dictionary_file: tuple[
            mock.MagicMock, collections_abc.Iterable[str]
        ],
    ) -> None:
        with pytest.raises(wordall.InvalidDictionaryFileError):
            wordall.WordleGame(pathlib.Path("/a/b/c"), 0)

    def test_raises_exception_on_empty_dictionary(
        self,
        mock_empty_dictionary_file: tuple[
            mock.MagicMock, collections_abc.Iterable[str]
        ],
    ) -> None:
        with pytest.raises(wordall.InvalidDictionaryFileError):
            wordall.WordleGame(pathlib.Path("/a/b/c"), 0)

    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_valid_dictionary_file: tuple[
            mock.MagicMock, collections_abc.Iterable[str]
        ],
    ) -> None:
        _, word_dictionary = mock_valid_dictionary_file

        mock_choice = mocker.patch("random.choice")

        wordle_game = wordall.WordleGame(pathlib.Path("/a/b/c"), 0)

        mock_choice.assert_called_once_with(list(word_dictionary))
        assert wordle_game.target == mock_choice.return_value


class TestWordleGuessWord:
    @pytest.fixture
    def wordle_game_instance(
        self,
        mock_valid_dictionary_file: tuple[
            mock.MagicMock, collections_abc.Iterable[str]
        ],
    ) -> wordall.WordleGame:
        return wordall.WordleGame(pathlib.Path("/a/b/c"), 3)

    def test_game_continues_when_incorrect_word(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        word_list = list(wordle_game_instance.word_dictionary)
        wordle_game_instance.target = word_list[0]
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        return_value = wordle_game_instance.guess_word(word_list[1])

        assert not return_value
        assert wordle_game_instance.guesses == [word_list[1]]
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

    def test_game_ends_when_correct_word(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        word_list = list(wordle_game_instance.word_dictionary)
        wordle_game_instance.target = word_list[0]
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        return_value = wordle_game_instance.guess_word(word_list[0])

        assert return_value
        assert wordle_game_instance.guesses == [word_list[0]]
        assert wordle_game_instance.game_state == wordall.GameState.SUCCEEDED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_games_ends_when_guess_limit_reached(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        word_list = list(wordle_game_instance.word_dictionary)
        wordle_game_instance.target = word_list[0]
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        wordle_game_instance.guess_word(word_list[1])
        wordle_game_instance.guess_word(word_list[1])
        return_value = wordle_game_instance.guess_word(word_list[1])

        assert return_value
        assert wordle_game_instance.guesses == [word_list[1]] * 3
        assert wordle_game_instance.game_state == wordall.GameState.FAILED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_raises_exception_when_game_already_failed(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        word_list = list(wordle_game_instance.word_dictionary)
        wordle_game_instance.target = word_list[0]
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word(word_list[1])
        wordle_game_instance.guess_word(word_list[1])
        wordle_game_instance.guess_word(word_list[1])
        with pytest.raises(wordall.GameAlreadyFinishedError):
            wordle_game_instance.guess_word(word_list[1])

    def test_raises_exception_when_game_already_succeeded(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        word_list = list(wordle_game_instance.word_dictionary)
        wordle_game_instance.target = word_list[0]
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word(word_list[0])
        with pytest.raises(wordall.GameAlreadyFinishedError):
            wordle_game_instance.guess_word(word_list[1])

    def test_raises_exception_for_non_alphabet_guess(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        with pytest.raises(wordall.InvalidGuessWordError):
            wordle_game_instance.guess_word("ABCD5")

    def test_raises_exception_for_invalid_word_guess(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        with pytest.raises(wordall.InvalidGuessWordError):
            wordle_game_instance.guess_word("BREAG")
