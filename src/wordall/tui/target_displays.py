from typing import Generic, TypeVar

from textual import app as textual_app
from textual import reactive, widgets

from wordall import game

T = TypeVar("T", bound=game.Game)


class TargetDisplay(widgets.Static, Generic[T]):
    game_: reactive.Reactive[T | None] = reactive.reactive(None)


# This would be better as a protocol, but there's no typing.Intersection to have it also
# be typed as a Game subclass
GameWithSingleTarget = game.SingleWordleLikeBaseGame


class SingleTargetDisplay(TargetDisplay[GameWithSingleTarget]):
    game_: reactive.Reactive[GameWithSingleTarget | None] = reactive.reactive(None)

    def render(self) -> textual_app.RenderResult:
        assert self.game_ is not None

        return f"The correct answer was: {self.game_.target}."
