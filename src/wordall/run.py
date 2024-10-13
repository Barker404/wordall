import pathlib
from typing import Any, ClassVar, cast

from rich import text
from textual import on
from textual.app import App, ComposeResult, RenderResult
from textual.containers import ScrollableContainer
from textual.reactive import Reactive, reactive
from textual.validation import ValidationResult, Validator
from textual.widgets import Footer, Header, Input, Label, Static
from textual.widgets._input import _InputRenderable

from wordall import game


class WordallApp(App[None]):
    CSS_PATH = "run.tcss"

    game_: Reactive[game.Game | None] = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game_ = self.get_game()

    def get_game(self) -> game.Game:
        # TODO: Should probably be an injected factory
        return game.WordleGame(pathlib.Path("dict_long.txt"), 5, target_word_length=4)

    def compose(self) -> ComposeResult:
        assert self.game_ is not None

        yield Header()
        with UnfocusableScrollableContainer():
            yield WordleGuessesDisplay().data_bind(WordallApp.game_)
            yield GuessInput(
                max_length=self.game_.max_guess_word_length,
                validators=ValidGuessWord(self.game_),
            )
            yield WordleAlphabetDisplay().data_bind(WordallApp.game_)
            yield Label(id="game_messages")
            yield StatusDisplay().data_bind(WordallApp.game_)
        yield Footer()

    @on(Input.Submitted, "GuessInput")
    def guess_word(self, event: Input.Submitted) -> None:
        assert self.game_ is not None

        label = self.query_exactly_one("#game_messages", Label)

        if event.validation_result is not None and not event.validation_result.is_valid:
            label.update(f"Invalid guess: {event.value}")
            return

        try:
            game_ended = self.game_.guess_word(event.value.upper())
        except game.InvalidGuessWordError as e:
            label.update(f"ERROR: {e}")
            return

        label.update(f"Guessed: {event.value}")
        self.mutate_reactive(WordallApp.game_)
        event.input.clear()

        if game_ended:
            container = self.query_exactly_one(UnfocusableScrollableContainer)
            container.mount(WordleTargetDisplay().data_bind(WordallApp.game_))


class ValidGuessWord(Validator):
    def __init__(self, game_: game.Game) -> None:
        self.game_ = game_

    def validate(self, value: str) -> ValidationResult:
        """Check a string is equal to its reverse."""
        if self.game_.is_valid_word(value.upper()):
            return self.success()
        else:
            return self.failure("Invalid guess")


class UnfocusableScrollableContainer(ScrollableContainer, can_focus=False):
    pass


class WordleGuessesDisplay(Static):
    game_: Reactive[game.WordleGame | None] = reactive(None)

    def compose(self) -> ComposeResult:
        # At compose time reactive game has been data bound, but not yet updated to
        # match parent version. So instead we use a hack to directly access the game on
        # the app.
        game_ = cast(game.WordleGame, cast(WordallApp, self.app).game_)
        for i in range(game_.guess_limit):
            yield WordleGuessDisplay(i).data_bind(WordleGuessesDisplay.game_)


class WordleGuessDisplay(Static):
    guess_letter_state_to_style: ClassVar[dict[game.GuessLetterState, str]] = {
        game.GuessLetterState.CORRECT: "black on dark_green",
        game.GuessLetterState.ELSEWHERE: "black on yellow",
        game.GuessLetterState.INCORRECT: "white on black",
    }

    game_: Reactive[game.WordleGame | None] = reactive(None)

    def __init__(self, guess_number: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.guess_number = guess_number

    def render(self) -> RenderResult:
        assert self.game_ is not None

        separator = text.Text(" ")
        if len(self.game_.guesses) > self.guess_number:
            guess = self.game_.guesses[self.guess_number]
            return separator.join(
                self.render_guess_letter_state(c, state)
                for c, state in guess.guess_letter_states
            )
        else:
            return separator.join([text.Text("#")] * len(self.game_.target))

    @classmethod
    def render_guess_letter_state(
        cls, c: str, state: game.GuessLetterState
    ) -> text.Text:
        return text.Text(c, style=cls.guess_letter_state_to_style[state])


class WordleAlphabetDisplay(Static):
    alphabet_letter_state_to_style: ClassVar[dict[game.AlphabetLetterState, str]] = {
        game.AlphabetLetterState.FOUND: "black on dark_green",
        game.AlphabetLetterState.FOUND_ELSEWHERE: "black on yellow",
        game.AlphabetLetterState.UNUSED: "white on black",
        game.AlphabetLetterState.NOT_GUESSED: "black on white",
    }

    game_: Reactive[game.WordleGame | None] = reactive(None)

    def render(self) -> RenderResult:
        assert self.game_ is not None

        separator = text.Text(" ")
        return separator.join(
            self.render_alphabet_letter_state(c, state)
            for c, state in self.game_.alphabet_states.items()
        )

    @classmethod
    def render_alphabet_letter_state(
        cls, c: str, state: game.AlphabetLetterState
    ) -> text.Text:
        return text.Text(c, style=cls.alphabet_letter_state_to_style[state])


class GuessInput(Input):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        # Width needs to account for spacing (see InputSpacingWrapper)
        if self.max_length:
            self.styles.width = (self.max_length * 2) - 1

    def on_mount(self) -> None:
        self.focus()

    def insert_text_at_cursor(self, text: str) -> None:
        super().insert_text_at_cursor(text.upper())

    def render(self) -> RenderResult:
        if not self.value:
            return super().render()

        # For the input to match the guess displays we want to add spacing between each
        # character. Unfortunately, textual not have any way to do this at the display
        # level (e.g. CSS) and it's very difficult to modify the value used for
        # rendering by overriding methods. The Input class passes itself to a
        # _InputRenderable, which uses its value and _value, so reimplementing render()
        # is not enough. subclassing _InputRenderable would require re-implementing the
        # entire thing as it reads the value from the Input in the same method as doing
        # things like line width handling. Inserting spaces into the actual value would
        # be an alternative, but then other behaviour like deletion and cursor movement
        # needs to be changed. Instead we use a hack to wrap the GuessInput provided to
        # _InputRenderable and make it look like it has spacing in the value here only.
        return _InputRenderable(InputSpacingWrapper(self), self._cursor_visible)  # type: ignore


class InputSpacingWrapper:
    """
    A wrapper for an Input widget that passes most calls through to the underlying
    object, but intercepts some calls to modify the return values, adding spacing
    between each character of the input value.
    """

    SEPARATOR = " "

    def __init__(self, input_instance: Input):
        self._wrapped_input = input_instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._wrapped_input, name)

    @property
    def value(self) -> str:
        # Add an extra separator at the end so the cursor renders properly when at the
        # end
        value = self.SEPARATOR.join(self._wrapped_input.value)
        return value + self.SEPARATOR

    @property
    def _value(self) -> text.Text:
        # Add an extra separator at the end so the cursor renders properly when at the
        # end
        separated_value: list[text.Text] = list(self._wrapped_input._value)  # type: ignore  # noqa SLF001  # mypy doesn't know about splitting up a Text
        value = text.Text(self.SEPARATOR).join(separated_value)
        return value + text.Text(self.SEPARATOR)

    @property
    def cursor_position(self) -> int:
        # The cursor position needs to be moved along to match the spacing added
        return self._wrapped_input.cursor_position * 2


class StatusDisplay(Static):
    game_state_to_message: ClassVar[dict[game.GameState, str]] = {
        game.GameState.GUESSING: "Make a guess.",
        game.GameState.FAILED: "You lost, too bad.",
        game.GameState.SUCCEEDED: "Congratulations, you won!",
    }

    game_: Reactive[game.Game | None] = reactive(None)

    def render(self) -> RenderResult:
        assert self.game_ is not None

        return self.game_state_to_message[self.game_.game_state]


class WordleTargetDisplay(Static):
    game_: Reactive[game.WordleGame | None] = reactive(None)

    def render(self) -> RenderResult:
        assert self.game_ is not None

        return f"The correct answer was: {self.game_.target}."


if __name__ == "__main__":
    app = WordallApp()
    app.run()
