import pathlib
from typing import Any
from unittest import mock

import pytest
import pytest_mock

from wordall import game


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


@pytest.fixture
def wordle_game_instance(
    mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],  # noqa: ARG001
) -> game.WordleGame:
    return game.WordleGame(pathlib.Path("/a/b/c"), 3)


@pytest.fixture
def wordle_game_instance_5_letter(
    mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],  # noqa: ARG001
) -> game.WordleGame:
    return game.WordleGame(pathlib.Path("/a/b/c"), 3, target_word_length=5)


class TestIsWordInAlphabet:
    @pytest.fixture
    def non_abstract_game(self, mocker: pytest_mock.MockerFixture) -> game.Game:
        # Patch Game so that we can directly create an instance without needing a
        # subclass
        mocker.patch.multiple(game.Game, __abstractmethods__=set())
        game_ = game.Game()  # type: ignore # Mypy thinks this is still abstract
        return game_

    def test_is_in_alphabet(self, non_abstract_game: game.Game) -> None:
        assert non_abstract_game.is_word_in_alphabet("BAED")

    def test_not_in_alphabet(self, non_abstract_game: game.Game) -> None:
        assert not non_abstract_game.is_word_in_alphabet("AB1")


class TestWordleGameInit:
    def test_loads_word_dictionary(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, file_word_list = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = game.WordleGame(dictionary_file_path, 1)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == set(file_word_list)

    def test_loads_word_dictionary_with_length(
        self,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = game.WordleGame(dictionary_file_path, 1, target_word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_skips_empty_lines_in_dictionary(
        self,
        mock_valid_empty_line_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        open_mock, _ = mock_valid_empty_line_dictionary_file
        dictionary_file_path = pathlib.Path("/a/b/c")

        wordle_game = game.WordleGame(dictionary_file_path, 1, target_word_length=5)

        open_mock.assert_called_once_with(dictionary_file_path)
        assert wordle_game.word_dictionary == {"APPLE", "BREAD", "CHIPS"}

    def test_raises_exception_on_non_alphabet_dictionary_word(
        self,
        mock_invalid_character_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(game.InvalidDictionaryFileError):
            game.WordleGame(pathlib.Path("/a/b/c"), 1)

    def test_raises_exception_on_empty_dictionary(
        self,
        mock_empty_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        with pytest.raises(game.InvalidDictionaryFileError):
            game.WordleGame(pathlib.Path("/a/b/c"), 1)

    def test_selects_random_target(
        self,
        mocker: pytest_mock.MockerFixture,
        mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],
    ) -> None:
        _, file_word_list = mock_valid_dictionary_file

        mock_choice = mocker.patch("random.choice")

        wordle_game = game.WordleGame(pathlib.Path("/a/b/c"), 0)

        mock_choice.assert_called_once_with(list(set(file_word_list)))
        assert wordle_game.target == mock_choice.return_value


class TestWordleGuessWord:
    def test_game_continues_when_incorrect_word(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == game.GameState.GUESSING

        return_value = wordle_game_instance.guess_word("BREAD")

        assert not return_value
        expected_guess = game.Guess("BREAD", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess]
        assert wordle_game_instance.game_state == game.GameState.GUESSING

    def test_game_ends_when_correct_word(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.game_state == game.GameState.GUESSING

        return_value = wordle_game_instance.guess_word("APPLE")

        assert return_value
        expected_guess = game.Guess("APPLE", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess]
        assert wordle_game_instance.game_state == game.GameState.SUCCEEDED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_games_ends_when_guess_limit_reached(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3
        assert wordle_game_instance.game_state == game.GameState.GUESSING

        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        return_value = wordle_game_instance.guess_word("BREAD")

        assert return_value
        expected_guess = game.Guess("BREAD", "APPLE")
        assert wordle_game_instance.guesses == [expected_guess] * 3
        assert wordle_game_instance.game_state == game.GameState.FAILED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    def test_raises_exception_when_game_already_failed(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        wordle_game_instance.guess_word("BREAD")
        with pytest.raises(game.GameAlreadyFinishedError):
            wordle_game_instance.guess_word("BREAD")

    def test_raises_exception_when_game_already_succeeded(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.guesses == []
        assert wordle_game_instance.guess_limit == 3

        wordle_game_instance.guess_word("APPLE")
        with pytest.raises(game.GameAlreadyFinishedError):
            wordle_game_instance.guess_word("BREAD")

    def test_raises_exception_for_non_alphabet_guess(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        with pytest.raises(game.InvalidGuessWordError):
            wordle_game_instance.guess_word("ABCD5")

    def test_raises_exception_for_invalid_word_guess(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        with pytest.raises(game.InvalidGuessWordError):
            wordle_game_instance.guess_word("BREAG")

    def test_raises_exception_for_empty_word_guess(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        with pytest.raises(game.InvalidGuessWordError):
            wordle_game_instance.guess_word("")

    def test_raises_exception_for_wrong_length_word_guess_length_supplied(
        self, wordle_game_instance_5_letter: game.WordleGame
    ) -> None:
        with pytest.raises(game.InvalidGuessWordError):
            wordle_game_instance_5_letter.guess_word("DONUTS")

    def test_raises_exception_for_wrong_length_word_guess_length_not_supplied(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        with pytest.raises(game.InvalidGuessWordError):
            wordle_game_instance.guess_word("DONUTS")

    def test_updates_alphabet_letter_states_found(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("AAAAA")
        wordle_game_instance.guess_word("AAAAA")

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["A"] = game.AlphabetLetterState.FOUND
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

        wordle_game_instance.word_dictionary.add("XXXXA")
        wordle_game_instance.guess_word("XXXXA")

        expected_alphabet_state["X"] = game.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_found_one_of_two(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XPXXX")
        wordle_game_instance.guess_word("XPXXX")

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["P"] = game.AlphabetLetterState.FOUND
        expected_alphabet_state["X"] = game.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_unused(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XXXXX")
        wordle_game_instance.guess_word("XXXXX")

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["X"] = game.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_elsewhere(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("XXXXA")
        wordle_game_instance.guess_word("XXXXA")

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["A"] = game.AlphabetLetterState.FOUND_ELSEWHERE
        expected_alphabet_state["X"] = game.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

        wordle_game_instance.word_dictionary.add("AXXXX")
        wordle_game_instance.guess_word("AXXXX")

        expected_alphabet_state["A"] = game.AlphabetLetterState.FOUND
        assert wordle_game_instance.alphabet_states == expected_alphabet_state

    def test_updates_alphabet_letter_states_second_of_double_correct(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"

        wordle_game_instance.word_dictionary.add("EXXXE")
        wordle_game_instance.guess_word("EXXXE")

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED
            for c in wordle_game_instance.ALPHABET
        }
        expected_alphabet_state["E"] = game.AlphabetLetterState.FOUND
        expected_alphabet_state["X"] = game.AlphabetLetterState.UNUSED
        assert wordle_game_instance.alphabet_states == expected_alphabet_state


class TestWordleIsValidWord:
    def test_accepts_valid_word(self, wordle_game_instance: game.WordleGame) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.is_valid_word("APPLE")

    def test_rejects_invalid_word(self, wordle_game_instance: game.WordleGame) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert not wordle_game_instance.is_valid_word("ABCDE")

    def test_rejects_wrong_length_word(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert not wordle_game_instance.is_valid_word("CAR")

    def test_accepts_valid_word_specific_length(
        self, wordle_game_instance_5_letter: game.WordleGame
    ) -> None:
        assert wordle_game_instance_5_letter.is_valid_word("APPLE")

    def test_rejects_invalid_word_specific_length(
        self, wordle_game_instance_5_letter: game.WordleGame
    ) -> None:
        assert not wordle_game_instance_5_letter.is_valid_word("ABCDE")

    def test_rejects_wrong_length_word_specific_length(
        self, wordle_game_instance_5_letter: game.WordleGame
    ) -> None:
        assert not wordle_game_instance_5_letter.is_valid_word("CAR")


class TestWordleMaxGuessWordLength:
    def test_correct_when_length_not_set(
        self, wordle_game_instance: game.WordleGame
    ) -> None:
        assert "APPLE" in wordle_game_instance.word_dictionary
        wordle_game_instance.target = "APPLE"
        assert wordle_game_instance.max_guess_word_length == 5

    def test_correct_when_length_set(
        self, wordle_game_instance_5_letter: game.WordleGame
    ) -> None:
        assert wordle_game_instance_5_letter.max_guess_word_length == 5


class TestGuess:
    def test_equality(self) -> None:
        assert game.Guess("APPLE", "BREAD") == game.Guess("APPLE", "BREAD")

    def test_inequality_different_guess(self) -> None:
        assert game.Guess("APPLE", "BREAD") != game.Guess("PEARS", "BREAD")

    def test_inequality_different_target(self) -> None:
        assert game.Guess("APPLE", "BREAD") != game.Guess("APPLE", "CAKES")

    def test_inequality_swapped(self) -> None:
        assert game.Guess("APPLE", "BREAD") != game.Guess("BREAD", "APPLE")

    def test_inequality_different_type(self) -> None:
        assert game.Guess("APPLE", "BREAD") != "APPLE"

    def test_repr(self) -> None:
        assert (
            repr(game.Guess("APPLE", "BREAD"))
            == "Guess(guess_word='APPLE', target_word='BREAD')"
        )

    def test_guess_all_correct(self) -> None:
        guess_word_ = "APPLE"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("A", game.GuessLetterState.CORRECT),
            ("P", game.GuessLetterState.CORRECT),
            ("P", game.GuessLetterState.CORRECT),
            ("L", game.GuessLetterState.CORRECT),
            ("E", game.GuessLetterState.CORRECT),
        ]

    def test_guess_all_incorrect(self) -> None:
        guess_word_ = "SHOOT"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("S", game.GuessLetterState.INCORRECT),
            ("H", game.GuessLetterState.INCORRECT),
            ("O", game.GuessLetterState.INCORRECT),
            ("O", game.GuessLetterState.INCORRECT),
            ("T", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_elsewhere(self) -> None:
        guess_word_ = "PALER"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", game.GuessLetterState.ELSEWHERE),
            ("A", game.GuessLetterState.ELSEWHERE),
            ("L", game.GuessLetterState.ELSEWHERE),
            ("E", game.GuessLetterState.ELSEWHERE),
            ("R", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_some_elsewhere(self) -> None:
        guess_word_ = "PALER"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", game.GuessLetterState.ELSEWHERE),
            ("A", game.GuessLetterState.ELSEWHERE),
            ("L", game.GuessLetterState.ELSEWHERE),
            ("E", game.GuessLetterState.ELSEWHERE),
            ("R", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_double_letter_one_elsewhere(self) -> None:
        guess_word_ = "POPOP"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", game.GuessLetterState.ELSEWHERE),
            ("O", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.CORRECT),
            ("O", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_double_letter_both_elsewhere(self) -> None:
        guess_word_ = "POBOP"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", game.GuessLetterState.ELSEWHERE),
            ("O", game.GuessLetterState.INCORRECT),
            ("B", game.GuessLetterState.INCORRECT),
            ("O", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.ELSEWHERE),
        ]

    def test_guess_longer(self) -> None:
        guess_word_ = "ABPOPPEE"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("A", game.GuessLetterState.CORRECT),
            ("B", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.CORRECT),
            ("O", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.ELSEWHERE),
            ("P", game.GuessLetterState.INCORRECT),
            ("E", game.GuessLetterState.ELSEWHERE),
            ("E", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_shorter(self) -> None:
        guess_word_ = "POPP"
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("P", game.GuessLetterState.ELSEWHERE),
            ("O", game.GuessLetterState.INCORRECT),
            ("P", game.GuessLetterState.CORRECT),
            ("P", game.GuessLetterState.INCORRECT),
        ]

    def test_guess_empty(self) -> None:
        guess_word_ = ""
        target_word = "APPLE"
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == []

    def test_target_empty(self) -> None:
        guess_word_ = "OK"
        target_word = ""
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == [
            ("O", game.GuessLetterState.INCORRECT),
            ("K", game.GuessLetterState.INCORRECT),
        ]

    def test_both_empty(self) -> None:
        guess_word_ = ""
        target_word = ""
        guess = game.Guess(guess_word_, target_word)

        assert guess.target_word == target_word
        assert guess.guess_word == guess_word_
        assert guess.guess_letter_states == []
