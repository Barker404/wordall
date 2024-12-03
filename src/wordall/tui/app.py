import dataclasses
import pathlib
from typing import Any, ClassVar

import textual
from textual import app as textual_app
from textual import binding, containers, reactive, validation, widgets

from wordall import game as game_module
from wordall import word_dictionary_loaders
from wordall.games import numberle, wordle
from wordall.tui import (
    alphabet_displays,
    guess_input,
    guesses_displays,
    target_displays,
)


@dataclasses.dataclass
class GameRegistryEntry:
    game_class: type[game_module.Game]
    guesses_display_class: type[guesses_displays.GuessesDisplay[Any]] = (
        guesses_displays.GuessesDisplay
    )
    alphabet_display_class: type[alphabet_displays.AlphabetDisplay[Any]] = (
        alphabet_displays.AlphabetDisplay
    )
    target_display_class: type[target_displays.TargetDisplay[Any]] = (
        target_displays.TargetDisplay
    )


GAME_REGISTRY = {
    "wordle": GameRegistryEntry(
        game_class=wordle.WordleGame,
        guesses_display_class=guesses_displays.GuessesFromListDisplay,
        alphabet_display_class=alphabet_displays.AlphabetLetterStateDisplay,
        target_display_class=target_displays.SingleTargetDisplay,
    ),
    "numberle": GameRegistryEntry(
        game_class=numberle.NumberleGame,
        guesses_display_class=guesses_displays.GuessesFromListDisplay,
        alphabet_display_class=alphabet_displays.AlphabetLetterStateDisplay,
        target_display_class=target_displays.SingleTargetDisplay,
    ),
}


class WordallApp(textual_app.App[None]):
    BINDINGS: ClassVar[list[binding.BindingType]] = [
        binding.Binding("ctrl+n", "new_game", "New Game")
    ]

    CSS_PATH = "app.tcss"

    game_: reactive.Reactive[game_module.Game | None] = reactive.reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game_key = "wordle"
        self.game_ = self.get_game(self.game_key)

    def get_game(self, game_key: str) -> game_module.Game:
        # TODO: Obviously still needs work to load args/kwargs properly and use game
        # class from registry
        if game_key == "wordle":
            scowl_path = (
                pathlib.Path(__file__).parent.parent
                / "resources/scowl-2020.12.07/final"
            ).resolve()
            return wordle.WordleGame(
                word_dictionary_loaders.ScowlWordListLoader(
                    scowl_path,
                    70,
                ),
                guess_limit=6,
                target_word_length=5,
            )
        elif game_key == "numberle":
            return numberle.NumberleGame(guess_limit=5, target_word_length=5)
        else:
            raise ValueError()

    def compose(self) -> textual_app.ComposeResult:
        assert self.game_ is not None

        yield widgets.Header()
        with UnfocusableScrollableContainer():
            yield (
                GAME_REGISTRY[self.game_key]
                .guesses_display_class()
                .data_bind(WordallApp.game_)
            )
            yield guess_input.GuessInput(
                max_length=self.game_.max_guess_word_length,
                validators=ValidGuessWord(self.game_),
            )
            yield (
                GAME_REGISTRY[self.game_key]
                .alphabet_display_class()
                .data_bind(WordallApp.game_)
            )
            yield widgets.Label("New Game Started.", id="game_messages")
            yield StatusDisplay().data_bind(WordallApp.game_)
        yield widgets.Footer()

    @textual.on(widgets.Input.Submitted, "GuessInput")
    def guess_word(self, event: widgets.Input.Submitted) -> None:
        assert self.game_ is not None
        assert self.game_.game_state == game_module.GameState.GUESSING

        label = self.query_exactly_one("#game_messages", widgets.Label)

        if event.validation_result is not None and not event.validation_result.is_valid:
            label.update(f"Invalid guess: {event.value}")
            return

        try:
            game_ended = self.game_.guess_word(event.value.upper())
        except (
            game_module.InvalidGuessWordError
        ) as e:  # pragma: no cover  # Not possible normally
            label.update(f"ERROR: {e}")
            return

        label.update(f"Guessed: {event.value}")
        self.mutate_reactive(WordallApp.game_)
        event.input.clear()

        if game_ended:
            container = self.query_exactly_one(UnfocusableScrollableContainer)
            container.mount(
                GAME_REGISTRY[self.game_key]
                .target_display_class()
                .data_bind(WordallApp.game_)
            )
            event.input.disabled = True
            self.is_game_over = True

    def action_new_game(self) -> None:
        self.game_ = self.get_game(self.game_key)
        self.refresh(recompose=True)


class UnfocusableScrollableContainer(containers.ScrollableContainer, can_focus=False):
    pass


class StatusDisplay(widgets.Static):
    game_state_to_message: ClassVar[dict[game_module.GameState, str]] = {
        game_module.GameState.GUESSING: "Make a guess.",
        game_module.GameState.FAILED: "You lost, too bad.",
        game_module.GameState.SUCCEEDED: "Congratulations, you won!",
    }

    game_: reactive.Reactive[game_module.Game | None] = reactive.reactive(None)

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        return self.game_state_to_message[self.game_.game_state]


class ValidGuessWord(validation.Validator):
    def __init__(self, game_: game_module.Game) -> None:
        self.game_ = game_

    def validate(self, value: str) -> validation.ValidationResult:
        """Check a string is equal to its reverse."""
        if self.game_.is_valid_word(value.upper()):
            return self.success()
        else:
            return self.failure("Invalid guess")
