from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    hex: str
    name: str


COLORS: list[Color] = [
    Color("EEEEEE", "White"),
    Color("222222", "Black"),
    Color("19E753", "Green"),
    Color("E2DB13", "Yellow"),
    Color("2CE6E6", "Cyan"),
    Color("0A3EE2", "Blue"),
    Color("7514ED", "Purple"),
    Color("CF11D2", "Magenta"),
    Color("D02525", "Red"),
    Color("DF7F00", "Orange"),
]


class ColorGenerator:
    _color_index: int

    def __init__(self) -> None:
        self._color_index = -1

    def reset(self):
        self._color_index = -1

    def next_color(self) -> Color:
        self._color_index += 1

        return COLORS[self._color_index % len(COLORS)]
