import pathlib
from typing import cast
from unittest import mock

import pytest
import pytest_mock
from rich import text
from textual import widgets

from wordall import game as game_module
from wordall.games import wordle
from wordall.tui import alphabet_displays, guesses_displays, target_displays
from wordall.tui import app as app_module
from wordall.tui import guess_input as guess_input_module


# This patching is a hack to choose the game options needed for testing, because there's
# no proper way to inject a game/game factory yet
@pytest.fixture
def app_with_wordle_game(
    mocker: pytest_mock.MockerFixture,
    mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],  # noqa: ARG001
) -> app_module.WordallApp:
    def get_game(self: app_module.WordallApp, game_key: str) -> wordle.WordleGame:  # noqa: ARG001
        return wordle.WordleGame(
            pathlib.Path("/a/b/c"), guess_limit=5, target_word_length=5
        )

    mocker.patch("wordall.tui.app.WordallApp.get_game", get_game)
    return app_module.WordallApp()


@pytest.fixture
def app_with_wordle_game_no_limit(
    mocker: pytest_mock.MockerFixture,
    mock_valid_dictionary_file: tuple[mock.MagicMock, list[str]],  # noqa: ARG001
) -> app_module.WordallApp:
    def get_game(self: app_module.WordallApp, game_key: str) -> wordle.WordleGame:  # noqa: ARG001
        return wordle.WordleGame(
            pathlib.Path("/a/b/c"), guess_limit=None, target_word_length=5
        )

    mocker.patch("wordall.tui.app.WordallApp.get_game", get_game)
    return app_module.WordallApp()


@pytest.mark.asyncio
class TestTextEntry:
    async def test_input_focused_at_start(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        async with app.run_test():
            assert app.query_exactly_one(guess_input_module.GuessInput).has_focus

    async def test_text_entered_shown(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        async with app.run_test() as pilot:
            guess_input = app.query_exactly_one(guess_input_module.GuessInput)
            await pilot.press("A")
            assert guess_input.value == "A"
            await pilot.press("B", "C", "D")
            assert guess_input.value == "ABCD"

    async def test_text_entered_uppercased(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        async with app.run_test() as pilot:
            guess_input = app.query_exactly_one(guess_input_module.GuessInput)
            await pilot.press("a", "b", "c", "d")
            assert guess_input.value == "ABCD"

    async def test_invalid_word_not_highlighted(
        self,
        app_with_wordle_game: app_module.WordallApp,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        app = app_with_wordle_game
        is_valid_word_mock = mocker.patch(
            "wordall.games.wordle.WordleGame.is_valid_word"
        )
        is_valid_word_mock.return_value = False

        async with app.run_test() as pilot:
            await pilot.press("A", "B", "C", "D")
            assert not app.query_exactly_one(guess_input_module.GuessInput).is_valid
            is_valid_word_mock.assert_called_with("ABCD")
            await pilot.press("E")
            assert not app.query_exactly_one(guess_input_module.GuessInput).is_valid
            is_valid_word_mock.assert_called_with("ABCDE")

    async def test_valid_word_highlighted(
        self,
        app_with_wordle_game: app_module.WordallApp,
        mocker: pytest_mock.MockerFixture,
    ) -> None:
        app = app_with_wordle_game
        is_valid_word_mock = mocker.patch(
            "wordall.games.wordle.WordleGame.is_valid_word"
        )
        is_valid_word_mock.return_value = True

        async with app.run_test() as pilot:
            await pilot.press("A", "B", "C", "D", "E")
            assert app.query_exactly_one(guess_input_module.GuessInput).is_valid
            is_valid_word_mock.assert_called_with("ABCDE")


@pytest.mark.asyncio
class TestGuessSubmission:
    async def test_invalid_guess_rejected(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)

        async with app.run_test() as pilot:
            assert "ABCDE" not in game.word_dictionary
            await pilot.press("A", "B", "C", "D", "E", "enter")

            assert len(game.guesses) == 0
            label = app.query_exactly_one("#game_messages", widgets.Label)
            label_renderable = label.render()
            assert isinstance(label_renderable, text.Text)
            assert "invalid" in str(label_renderable).lower()

    async def test_valid_guess_displayed(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        async with app.run_test() as pilot:
            guess_widgets = app.query(guesses_displays.GuessFromListDisplay)

            assert "BREAD" in game.word_dictionary
            await pilot.press("B", "R", "E", "A", "D", "enter")

            assert len(game.guesses) == 1
            assert game.guesses[0].guess_word == "BREAD"
            guess_renderable = guess_widgets[0].render()
            assert isinstance(guess_renderable, text.Text)
            assert " ".join("BREAD") in str(guess_renderable)

            label = app.query_exactly_one("#game_messages", widgets.Label)
            label_renderable = label.render()
            assert isinstance(label_renderable, text.Text)
            assert "guessed" in str(label_renderable).lower()

            assert "CHIPS" in game.word_dictionary
            await pilot.press("C", "H", "I", "P", "S", "enter")

            assert len(game.guesses) == 2
            assert game.guesses[1].guess_word == "CHIPS"
            guess_renderable = guess_widgets[1].render()
            assert isinstance(guess_renderable, text.Text)
            assert " ".join("CHIPS") in str(guess_renderable)

    async def test_valid_guess_displayed_when_no_guess_limit(
        self, app_with_wordle_game_no_limit: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game_no_limit
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        async with app.run_test() as pilot:
            guesses_widget = app.query_exactly_one(
                guesses_displays.GuessesFromListDisplay
            )
            assert len(guesses_widget.children) == 0

            assert "BREAD" in game.word_dictionary
            await pilot.press("B", "R", "E", "A", "D", "enter")

            assert len(guesses_widget.children) == 1
            guess_renderable = guesses_widget.children[0].render()
            assert isinstance(guess_renderable, text.Text)
            assert " ".join("BREAD") in str(guess_renderable)

            assert "CHIPS" in game.word_dictionary
            await pilot.press("C", "H", "I", "P", "S", "enter")

            assert len(guesses_widget.children) == 2
            guess_renderable = guesses_widget.children[1].render()
            assert isinstance(guess_renderable, text.Text)
            assert " ".join("CHIPS") in str(guess_renderable)

    async def test_valid_guess_letter_statuses_shown(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        guess_letter_state_to_style = (
            guesses_displays.GuessFromListDisplay.guess_letter_state_to_style
        )

        async with app.run_test() as pilot:
            guess_widgets = app.query(guesses_displays.GuessFromListDisplay)

            assert "BREAD" in game.word_dictionary
            await pilot.press("B", "R", "E", "A", "D", "enter")

            guess_renderable = guess_widgets[0].render()
            assert isinstance(guess_renderable, text.Text)
            rendered_guess_letters = guess_renderable.split(" ")

            for rendered_letter, (guess_letter, guess_letter_state) in zip(
                rendered_guess_letters,
                game.guesses[0].guess_letter_states,
                strict=True,
            ):
                assert str(rendered_letter) == guess_letter
                assert len(rendered_letter.spans) == 1
                span = rendered_letter.spans[0]
                assert span.start == 0
                assert span.end == 1
                assert span.style == guess_letter_state_to_style[guess_letter_state]

    async def test_valid_guess_updates_alphabet_states(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        alphabet_letter_state_to_style = (
            alphabet_displays.AlphabetLetterStateDisplay.alphabet_letter_state_to_style
        )

        async with app.run_test() as pilot:
            alphabet_widget = app.query_exactly_one(
                alphabet_displays.AlphabetLetterStateDisplay
            )

            assert "BREAD" in game.word_dictionary
            await pilot.press("B", "R", "E", "A", "D", "enter")

            alphabet_renderable = alphabet_widget.render()
            assert isinstance(alphabet_renderable, text.Text)
            rendered_alphabet_letters = alphabet_renderable.split(" ")

            for rendered_letter, (alphabet_letter, alphabet_letter_state) in zip(
                rendered_alphabet_letters, game.alphabet_states.items(), strict=True
            ):
                expected_style = alphabet_letter_state_to_style[alphabet_letter_state]

                assert str(rendered_letter) == alphabet_letter
                assert len(rendered_letter.spans) == 1
                span = rendered_letter.spans[0]
                assert span.start == 0
                assert span.end == 1
                assert span.style == expected_style

    async def test_correct_guess_ends_game(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        async with app.run_test() as pilot:
            await pilot.press("A", "P", "P", "L", "E", "enter")

            assert game.game_state == game_module.GameState.SUCCEEDED
            assert app.query_exactly_one(guess_input_module.GuessInput).disabled
            target_display = app.query_exactly_one(target_displays.TargetDisplay)
            assert target_display.visible
            target_renderable = target_display.render()
            assert isinstance(target_renderable, str)
            assert "APPLE" in target_renderable

    async def test_incorrect_guesses_end_game(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        game = cast(wordle.WordleGame, app.game_)
        assert "APPLE" in game.word_dictionary
        game.target = "APPLE"

        async with app.run_test() as pilot:
            for _ in range(5):
                await pilot.press("B", "R", "E", "A", "D", "enter")

            assert game.game_state == game_module.GameState.FAILED
            assert app.query_exactly_one(guess_input_module.GuessInput).disabled
            target_display = app.query_exactly_one(target_displays.TargetDisplay)
            assert target_display.visible
            target_renderable = target_display.render()
            assert isinstance(target_renderable, str)
            assert "APPLE" in target_renderable


@pytest.mark.asyncio
class TestNewGame:
    async def test_ctrl_n_starts_new_game(
        self, app_with_wordle_game: app_module.WordallApp
    ) -> None:
        app = app_with_wordle_game
        old_game = app.game_

        async with app.run_test() as pilot:
            await pilot.press("ctrl+n")
            assert app.game_ is not old_game
