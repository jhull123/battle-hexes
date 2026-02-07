class Terrain:
    def __init__(self, name: str, hex_color: str):
        self._name = name
        self._hex_color = hex_color

    @property
    def name(self) -> str:
        return self._name

    @property
    def hex_color(self) -> str:
        return self._hex_color

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Terrain({self.name})"
