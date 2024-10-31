import pytest
import pytest_mock

from wordall import game


class TestGameIsWordInAlphabet:
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


class TestSingleWordleLikeBaseGameGuessWord:
    """
    Tests functionality of SingleWordleLikeBaseGame's guess_word across different
    subclasses which do no modify this functionality to avoid repetition in their own
    tests. Tests use a common pattern with request.getfixturevalue to dynamically get
    a fixture for the subclass's game instance.
    """

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "incorrect_word"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "BREAD"),
            ("numberle_game_instance_5_digit", "12345", "98765"),
        ],
    )
    def test_game_continues_when_incorrect_word(
        self,
        game_fixture_name: str,
        target_word: str,
        incorrect_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        assert game_instance.is_valid_word(target_word)
        game_instance.target = target_word
        assert game_instance.guesses == []
        assert game_instance.game_state == game.GameState.GUESSING

        return_value = game_instance.guess_word(incorrect_word)

        assert not return_value
        expected_guess = game.Guess(incorrect_word, target_word)
        assert game_instance.guesses == [expected_guess]
        assert game_instance.game_state == game.GameState.GUESSING

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word"),
        [
            ("wordle_game_instance_5_letter", "APPLE"),
            ("numberle_game_instance_5_digit", "12345"),
        ],
    )
    def test_game_ends_when_correct_word(
        self,
        game_fixture_name: str,
        target_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        assert game_instance.is_valid_word(target_word)
        game_instance.target = target_word
        assert game_instance.guesses == []
        assert game_instance.game_state == game.GameState.GUESSING

        return_value = game_instance.guess_word(target_word)

        assert return_value
        expected_guess = game.Guess(target_word, target_word)
        assert game_instance.guesses == [expected_guess]
        assert game_instance.game_state == game.GameState.SUCCEEDED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "incorrect_word"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "BREAD"),
            ("numberle_game_instance_5_digit", "12345", "98765"),
        ],
    )
    def test_games_ends_when_guess_limit_reached(
        self,
        game_fixture_name: str,
        target_word: str,
        incorrect_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        assert game_instance.is_valid_word(target_word)
        game_instance.target = target_word
        assert game_instance.guesses == []
        assert game_instance.guess_limit == 3
        assert game_instance.game_state == game.GameState.GUESSING

        game_instance.guess_word(incorrect_word)
        game_instance.guess_word(incorrect_word)
        return_value = game_instance.guess_word(incorrect_word)

        assert return_value
        expected_guess = game.Guess(incorrect_word, target_word)
        assert game_instance.guesses == [expected_guess] * 3
        assert game_instance.game_state == game.GameState.FAILED  # type: ignore[comparison-overlap] # False positive, https://github.com/python/mypy/issues/17317

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "incorrect_word"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "BREAD"),
            ("numberle_game_instance_5_digit", "12345", "98765"),
        ],
    )
    def test_raises_exception_when_game_already_failed(
        self,
        game_fixture_name: str,
        target_word: str,
        incorrect_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        assert game_instance.is_valid_word(target_word)
        game_instance.target = target_word
        assert game_instance.guesses == []
        assert game_instance.guess_limit == 3

        game_instance.guess_word(incorrect_word)
        game_instance.guess_word(incorrect_word)
        game_instance.guess_word(incorrect_word)
        with pytest.raises(game.GameAlreadyFinishedError):
            game_instance.guess_word(incorrect_word)

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word"),
        [
            ("wordle_game_instance_5_letter", "APPLE"),
            ("numberle_game_instance_5_digit", "12345"),
        ],
    )
    def test_raises_exception_when_game_already_succeeded(
        self,
        game_fixture_name: str,
        target_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        assert game_instance.is_valid_word(target_word)
        game_instance.target = target_word
        assert game_instance.guesses == []
        assert game_instance.guess_limit == 3

        game_instance.guess_word(target_word)
        with pytest.raises(game.GameAlreadyFinishedError):
            game_instance.guess_word(target_word)

    @pytest.mark.parametrize(
        ("game_fixture_name", "invalid_guess_word"),
        [
            ("wordle_game_instance_5_letter", "ABCD5"),
            ("wordle_game_instance_5_letter", "BREAG"),
            ("wordle_game_instance_5_letter", "DONUTS"),
            ("wordle_game_instance_5_letter", ""),
            ("numberle_game_instance_5_digit", "1234A"),
            ("numberle_game_instance_5_digit", "123456"),
            ("numberle_game_instance_5_digit", ""),
        ],
    )
    def test_raises_exception_for_invalid_word_guess(
        self,
        game_fixture_name: str,
        invalid_guess_word: str,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )

        with pytest.raises(game.InvalidGuessWordError):
            game_instance.guess_word(invalid_guess_word)

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "guess_word", "found_letter"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "AAAAA", "A"),
            ("numberle_game_instance_5_digit", "12345", "11111", "1"),
        ],
    )
    def test_updates_alphabet_letter_states_found(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word: str,
        found_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter which is correctly found
        (and no other letters are guessed).
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word)

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED for c in game_instance.ALPHABET
        }
        expected_alphabet_state[found_letter] = game.AlphabetLetterState.FOUND
        assert game_instance.alphabet_states == expected_alphabet_state

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "guess_word", "found_letter"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "XPXXX", "P"),
            ("numberle_game_instance_5_digit", "12211", "92999", "2"),
        ],
    )
    def test_updates_alphabet_letter_states_found_one_of_two(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word: str,
        found_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter where only the first of
        two instances is found.
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word)

        assert (
            game_instance.alphabet_states[found_letter]
            == game.AlphabetLetterState.FOUND
        )

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "guess_word", "unused_letter"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "XXXXX", "X"),
            ("numberle_game_instance_5_digit", "12345", "99999", "9"),
        ],
    )
    def test_updates_alphabet_letter_states_unused(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word: str,
        unused_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter which is unused (and no
        other letters are guessed).
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word)

        expected_alphabet_state = {
            c: game.AlphabetLetterState.NOT_GUESSED for c in game_instance.ALPHABET
        }
        expected_alphabet_state[unused_letter] = game.AlphabetLetterState.UNUSED
        assert game_instance.alphabet_states == expected_alphabet_state

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "guess_word", "elsewhere_letter"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "XXXXA", "A"),
            ("numberle_game_instance_5_digit", "12345", "99991", "1"),
        ],
    )
    def test_updates_alphabet_letter_states_elsewhere(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word: str,
        elsewhere_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter which is used elsewhere.
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word)

        assert (
            game_instance.alphabet_states[elsewhere_letter]
            == game.AlphabetLetterState.FOUND_ELSEWHERE
        )

    @pytest.mark.parametrize(
        (
            "game_fixture_name",
            "target_word",
            "guess_word_1",
            "guess_word_2",
            "found_letter",
        ),
        [
            ("wordle_game_instance_5_letter", "APPLE", "XXXXA", "AXXXX", "A"),
            ("numberle_game_instance_5_digit", "12345", "99991", "19999", "1"),
        ],
    )
    def test_updates_alphabet_letter_states_elsewhere_then_found(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word_1: str,
        guess_word_2: str,
        found_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter which is first guessed
        in the wrong position then guessed correctly.
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word_1)
        assert (
            game_instance.alphabet_states[found_letter]
            == game.AlphabetLetterState.FOUND_ELSEWHERE
        )

        game_instance.guess_word(guess_word_2)
        assert (
            game_instance.alphabet_states[found_letter]
            == game.AlphabetLetterState.FOUND
        )

    @pytest.mark.parametrize(
        ("game_fixture_name", "target_word", "guess_word", "found_letter"),
        [
            ("wordle_game_instance_5_letter", "APPLE", "EXXXE", "E"),
            ("numberle_game_instance_5_digit", "12345", "59995", "5"),
        ],
    )
    def test_updates_alphabet_letter_states_second_instance_in_guess_correct(
        self,
        game_fixture_name: str,
        target_word: str,
        guess_word: str,
        found_letter: str,
        request: pytest.FixtureRequest,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        """
        Tests the alphabet letter state is updated for a letter which is included twice
        in a guess but only the second instance is correct.
        """
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        mocker.patch.object(game_instance, "is_valid_word").return_value = True
        game_instance.target = target_word

        game_instance.guess_word(guess_word)

        assert (
            game_instance.alphabet_states[found_letter]
            == game.AlphabetLetterState.FOUND
        )


class TestSingleWordleLikeBaseGameMaxGuessWordLength:
    """
    Tests functionality of SingleWordleLikeBaseGame's max_guess_word_length across
    different subclasses which do no modify this functionality to avoid repetition in
    their own tests. Tests use a common pattern with request.getfixturevalue to
    dynamically get a fixture for the subclass's game instance.
    """

    @pytest.mark.parametrize(
        ("game_fixture_name", "expected_max_length"),
        [
            ("wordle_game_instance_5_letter", 5),
            ("numberle_game_instance_5_digit", 5),
        ],
    )
    def test_correct_value(
        self,
        game_fixture_name: str,
        expected_max_length: int,
        request: pytest.FixtureRequest,
    ) -> None:
        game_instance: game.SingleWordleLikeBaseGame = request.getfixturevalue(
            game_fixture_name
        )
        assert game_instance.max_guess_word_length == expected_max_length


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
