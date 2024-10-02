import pathlib
from typing import Any
from unittest import mock

import pytest
import pytest_mock

from wordall import wordall


@pytest.fixture
def mock_valid_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(
        ["APPLE", "BREAD", "CHIPS", "DONUTS", "EGGS"], mocker
    )


@pytest.fixture
def mock_valid_empty_line_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(
        ["", "APPLE", "BREAD", "", "CHIPS", "DONUTS", "EGGS", ""], mocker
    )


@pytest.fixture
def mock_invalid_character_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper(["APPLE", "BREA8", "CHIPS"], mocker)


@pytest.fixture
def mock_empty_dictionary_file(
    mocker: pytest_mock.MockerFixture,
) -> tuple[mock.MagicMock, list[str]]:
    return _mock_dictionary_file_helper([], mocker)


def _mock_dictionary_file_helper(
    word_list: list[str], mocker: pytest_mock.MockerFixture
) -> tuple[mock.MagicMock, list[str]]:
    word_list_data = "\n".join(word_list)

    # Pathlib uses an open *method*, so to be able to inspect the Path object that
    # open() was called on we need to ensure self is passed to it, which requires
    # binding to the instance. Wrapping the mock object in a function allows this to
    # happen.
    open_mock = mocker.mock_open(read_data=word_list_data)

    def open_mock_wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        return open_mock(self, *args, **kwargs)

    mocker.patch("pathlib.Path.open", open_mock_wrapper)
    return open_mock, word_list


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
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, file_word_list = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordall.WordleGame(dictionary_file_path, 1)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == set(file_word_list)

    def test_loads_word_dictionary_with_length(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordall.WordleGame(dictionary_file_path, 1, word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_skips_empty_lines_in_dictionary(
        self,
        mock_valid_empty_line_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_empty_line_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = wordall.WordleGame(dictionary_file_path, 1, word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_raises_exception_on_non_alphabet_dictionary_word(
        self,
        mock_invalid_character_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(wordall.InvalidDictionaryFileError):
            wordall.WordleGame(pathlib.Path("/a/b/c"), 1)

    def test_raises_exception_on_empty_dictionary(
        self,
        mock_empty_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(wordall.InvalidDictionaryFileError):
            wordall.WordleGame(pathlib.Path("/a/b/c"), 1)

    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        _, file_word_list = mock_valid_dictionary_file

        mock_choice = mocker.patch("random.choice")

        wordle_game = wordall.WordleGame(pathlib.Path("/a/b/c"), 0)

        mock_choice.assert_called_once_with(list(set(file_word_list)))
        assert wordle_game.target == mock_choice.return_value


class TestWordleGuessWord:
    @pytest.fixture
    def wordle_game_instance(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> wordall.WordleGame:
        return wordall.WordleGame(pathlib.Path("/a/b/c"), 3)

    @pytest.fixture
    def wordle_game_instance_5_letter(
        self, mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]]
    ) -> wordall.WordleGame:
        return wordall.WordleGame(pathlib.Path("/a/b/c"), 3, word_length=5)

    def test_game_continues_when_incorrect_word(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        return_value = wordle_game_instance.guess_word("BREAD")

        assert not return_value
        expected_guess = wordall.Guess("BREAD", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess]
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

    def test_game_ends_when_correct_word(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        return_value = wordle_game_instance.guess_word("APPLE")

        assert return_value
        expected_guess = wordall.Guess("APPLE", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess]
        assert wordle_game_instance.game_state == wordall.GameState.SUCCEEDED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_games_ends_when_guess_limit_reached(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3
        assert wordle_game_instance.game_state == wordall.GameState.GUESSING

        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        return_value = wordle_game_instance.guess_word("BREAD")

        assert return_value
        expected_guess = wordall.Guess("BREAD", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess] * 3
        assert wordle_game_instance.game_state == wordall.GameState.FAILED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_raises_exception_when_game_already_failed(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        with pytest.raises(wordall.GameAlreadyFinishedError):
            wordle_game_instance.guess_word("BREAD")

    def test_raises_exception_when_game_already_succeeded(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word("APPLE")
        with pytest.raises(wordall.GameAlreadyFinishedError):
            wordle_game_instance.guess_word("BREAD")

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

    def test_raises_exception_for_empty_word_guess(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        with pytest.raises(wordall.InvalidGuessWordError):
            wordle_game_instance.guess_word("")

    def test_raises_exception_for_wrong_length_word_guess(
        self, wordle_game_instance_5_letter: wordall.WordleGame
    ) -> None:
        with pytest.raises(wordall.InvalidGuessWordError):
            wordle_game_instance_5_letter.guess_word("DONUTS")

    def test_updates_alphabet_letter_states_found(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("AAAAA")
        wordle_game_instance.guess_word("AAAAA")

        expected_alphabet_state = {
            c: wordall.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["A"] = wordall.AlphabetLetterState.FOUND
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

        wordle_game_instance.word_dictionary.add("XXXXA")
        wordle_game_instance.guess_word("XXXXA")

        expected_alphabet_state["X"] = wordall.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_found_one_of_two(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XPXXX")
        wordle_game_instance.guess_word("XPXXX")

        expected_alphabet_state = {
            c: wordall.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["P"] = wordall.AlphabetLetterState.FOUND
        expected_alphabet_state["X"] = wordall.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_unused(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XXXXX")
        wordle_game_instance.guess_word("XXXXX")

        expected_alphabet_state = {
            c: wordall.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["X"] = wordall.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_elsewhere(
        self, wordle_game_instance: wordall.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XXXXA")
        wordle_game_instance.guess_word("XXXXA")

        expected_alphabet_state = {
            c: wordall.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["A"] = wordall.AlphabetLetterState.FOUND_ELSEWHERE
        expected_alphabet_state["X"] = wordall.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

        wordle_game_instance.word_dictionary.add("AXXXX")
        wordle_game_instance.guess_word("AXXXX")

        expected_alphabet_state["A"] = wordall.AlphabetLetterState.FOUND
        assert wordle_game_instance.alphabet_states == expected_alphabet_state


class TestGuess:
    def test_equality(self) -> None:
        assert wordall.Guess("APPLE", "BREAD") == wordall.Guess("APPLE", "BREAD")

    def test_inequality_different_guess(self) -> None:
        assert wordall.Guess("APPLE", "BREAD") != wordall.Guess("PEARS", "BREAD")

    def test_inequality_different_target(self) -> None:
        assert wordall.Guess("APPLE", "BREAD") != wordall.Guess("APPLE", "CAKES")

    def test_inequality_swapped(self) -> None:
        assert wordall.Guess("APPLE", "BREAD") != wordall.Guess("BREAD", "APPLE")

    def test_inequality_different_type(self) -> None:
        assert wordall.Guess("APPLE", "BREAD") != "APPLE"

    def test_repr(self) -> None:
        assert (
            repr(wordall.Guess("APPLE", "BREAD"))
            == "Guess(guess_word='APPLE', target_word='BREAD')"
        )

    def test_guess_all_correct(self) -> None:
        guess_word_ = "APPLE"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("A", wordall.GuessLetterState.CORRECT),
            ("P", wordall.GuessLetterState.CORRECT),
            ("P", wordall.GuessLetterState.CORRECT),
            ("L", wordall.GuessLetterState.CORRECT),
            ("E", wordall.GuessLetterState.CORRECT),
        ]

    def test_guess_all_incorrect(self) -> None:
        guess_word_ = "SHOOT"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("S", wordall.GuessLetterState.INCORRECT),
            ("H", wordall.GuessLetterState.INCORRECT),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("T", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_elsewhere(self) -> None:
        guess_word_ = "PALER"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("A", wordall.GuessLetterState.ELSEWHERE),
            ("L", wordall.GuessLetterState.ELSEWHERE),
            ("E", wordall.GuessLetterState.ELSEWHERE),
            ("R", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_some_elsewhere(self) -> None:
        guess_word_ = "PALER"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("A", wordall.GuessLetterState.ELSEWHERE),
            ("L", wordall.GuessLetterState.ELSEWHERE),
            ("E", wordall.GuessLetterState.ELSEWHERE),
            ("R", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_double_letter_one_elsewhere(self) -> None:
        guess_word_ = "POPOP"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.CORRECT),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_double_letter_both_elsewhere(self) -> None:
        guess_word_ = "POBOP"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("B", wordall.GuessLetterState.INCORRECT),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.ELSEWHERE),
        ]

    def test_guess_longer(self) -> None:
        guess_word_ = "ABPOPPEE"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("A", wordall.GuessLetterState.CORRECT),
            ("B", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.CORRECT),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("P", wordall.GuessLetterState.INCORRECT),
            ("E", wordall.GuessLetterState.ELSEWHERE),
            ("E", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_shorter(self) -> None:
        guess_word_ = "POPP"
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", wordall.GuessLetterState.ELSEWHERE),
            ("O", wordall.GuessLetterState.INCORRECT),
            ("P", wordall.GuessLetterState.CORRECT),
            ("P", wordall.GuessLetterState.INCORRECT),
        ]

    def test_guess_empty(self) -> None:
        guess_word_ = ""
        target_word = "APPLE"
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == []

    def test_target_empty(self) -> None:
        guess_word_ = "OK"
        target_word = ""
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("O", wordall.GuessLetterState.INCORRECT),
            ("K", wordall.GuessLetterState.INCORRECT),
        ]

    def test_both_empty(self) -> None:
        guess_word_ = ""
        target_word = ""
        guess = wordall.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == []
