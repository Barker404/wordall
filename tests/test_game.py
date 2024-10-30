import pytest
import pytest_mock

from wordall import game


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
