import pathlib
from typing import Any, ClassVar

import textual
from textual import app as textual_app
from textual import binding, containers, reactive, validation, widgets

from wordall import game
from wordall.games import wordle
from wordall.tui import (
    alphabet_displays,
    guess_input,
    guesses_displays,
    target_displays,
)


class ValidGuessWord(validation.Validator):
    def __init__(self, game_: game.Game) -> None:
        self.game_ = game_

    def validate(self, value: str) -> validation.ValidationResult:
        """Check a string is equal to its reverse."""
        if self.game_.is_valid_word(value.upper()):
            return self.success()
        else:
            return self.failure("Invalid guess")


class UnfocusableScrollableContainer(containers.ScrollableContainer, can_focus=False):
    pass


class StatusDisplay(widgets.Static):
    game_state_to_message: ClassVar[dict[game.GameState, str]] = {
        game.GameState.GUESSING: "Make a guess.",
        game.GameState.FAILED: "You lost, too bad.",
        game.GameState.SUCCEEDED: "Congratulations, you won!",
    }

    game_: reactive.Reactive[game.Game | None] = reactive.reactive(None)

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        return self.game_state_to_message[self.game_.game_state]


class WordallApp(textual_app.App[None]):
    BINDINGS: ClassVar[list[binding.BindingType]] = [
        binding.Binding("ctrl+n", "new_game", "New Game")
    ]

    CSS_PATH = "app.tcss"

    game_: reactive.Reactive[game.Game | None] = reactive.reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game_ = self.get_game()

    def get_game(self) -> game.Game:
        # TODO: Should probably be an injected factory
        return wordle.WordleGame(pathlib.Path("dict_long.txt"), 5, target_word_length=4)

    def compose(self) -> textual_app.ComposeResult:
        assert self.game_ is not None

        yield widgets.Header()
        with UnfocusableScrollableContainer():
            yield guesses_displays.WordleGuessesDisplay().data_bind(WordallApp.game_)
            yield guess_input.GuessInput(
                max_length=self.game_.max_guess_word_length,
                validators=ValidGuessWord(self.game_),
            )
            yield alphabet_displays.WordleAlphabetDisplay().data_bind(WordallApp.game_)
            yield widgets.Label("New Game Started.", id="game_messages")
            yield StatusDisplay().data_bind(WordallApp.game_)
        yield widgets.Footer()

    @textual.on(widgets.Input.Submitted, "GuessInput")
    def guess_word(self, event: widgets.Input.Submitted) -> None:
        assert self.game_ is not None
        assert self.game_.game_state == game.GameState.GUESSING

        label = self.query_exactly_one("#game_messages", widgets.Label)

        if event.validation_result is not None and not event.validation_result.is_valid:
            label.update(f"Invalid guess: {event.value}")
            return

        try:
            game_ended = self.game_.guess_word(event.value.upper())
        except (
            game.InvalidGuessWordError
        ) as e:  # pragma: no cover  # Not possible normally
            label.update(f"ERROR: {e}")
            return

        label.update(f"Guessed: {event.value}")
        self.mutate_reactive(WordallApp.game_)
        event.input.clear()

        if game_ended:
            container = self.query_exactly_one(UnfocusableScrollableContainer)
            container.mount(
                target_displays.WordleTargetDisplay().data_bind(WordallApp.game_)
            )
            event.input.disabled = True
            self.is_game_over = True

    def action_new_game(self) -> None:
        self.game_ = self.get_game()
        self.refresh(recompose=True)
