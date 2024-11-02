from typing import Any

from rich import text
from textual.app import RenderResult
from textual.widgets import Input
from textual.widgets._input import _InputRenderable


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
