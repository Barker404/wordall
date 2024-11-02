from typing import ClassVar, Generic, TypeVar

from rich import text
from textual import app as textual_app
from textual import reactive, widgets

from wordall import game

T = TypeVar("T", bound=game.Game)


class AlphabetDisplay(widgets.Static, Generic[T]):
    game_: reactive.Reactive[T | None] = reactive.reactive(None)


# This would be better as a protocol, but there's no typing.Intersection to have it also
# be typed as a Game subclass
GameWithAlphabetLetterStates = game.SingleWordleLikeBaseGame


class AlphabetLetterStateDisplay(AlphabetDisplay[GameWithAlphabetLetterStates]):
    alphabet_letter_state_to_style: ClassVar[dict[game.AlphabetLetterState, str]] = {
        game.AlphabetLetterState.FOUND: "black on dark_green",
        game.AlphabetLetterState.FOUND_ELSEWHERE: "black on yellow",
        game.AlphabetLetterState.UNUSED: "white on black",
        game.AlphabetLetterState.NOT_GUESSED: "black on white",
    }

    game_: reactive.Reactive[GameWithAlphabetLetterStates | None] = reactive.reactive(
        None
    )

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None
        # Not sure mypy can reach here
        assert isinstance(self.game_, GameWithAlphabetLetterStates)

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
