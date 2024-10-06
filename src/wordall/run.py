import pathlib
from typing import Any, ClassVar, cast

from rich import text
from textual.app import App, ComposeResult, RenderResult
from textual.containers import ScrollableContainer
from textual.reactive import Reactive, reactive
from textual.widgets import Footer, Header, Input, Label, Static

from wordall import game


class WordallApp(App[None]):
    game_: Reactive[game.Game | None] = reactive(None)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.game_ = self.get_game()

    def get_game(self) -> game.Game:
        # TODO: Should probably be an injected factory
        return game.WordleGame(pathlib.Path("dict_long.txt"), 5, target_word_length=4)

    def compose(self) -> ComposeResult:
        yield Header()
        with UnfocusableScrollableContainer():
            yield WordleGuessesDisplay().data_bind(WordallApp.game_)
            yield WordleAlphabetDisplay().data_bind(WordallApp.game_)
            yield GuessInput().data_bind(WordallApp.game_)
            yield Label()
            yield StatusDisplay().data_bind(WordallApp.game_)
        yield Footer()


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
    game_: Reactive[game.Game | None] = reactive(None)

    def on_mount(self) -> None:
        self.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        assert self.game_ is not None

        # TODO: This is a bit awkward, can we do it without relying on knowledge of the
        # parent app? Maybe this can be implemented on the app, or a specific message
        # can be sent up after the guess?
        label = self.app.query_exactly_one(Label)

        try:
            self.game_.guess_word(event.value.upper())
        except game.InvalidGuessWordError as e:
            label.update(f"ERROR: {e}")
            return

        label.update(f"Guessed {event.value}")
        self.app.mutate_reactive(WordallApp.game_)
        self.clear()


class StatusDisplay(Static):
    game_: Reactive[game.Game | None] = reactive(None)

    def render(self) -> RenderResult:
        assert self.game_ is not None

        return f"The game state is {self.game_.game_state.name}"


if __name__ == "__main__":
    app = WordallApp()
    app.run()
