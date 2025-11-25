class ColorCycler:
    # Joyful high-vis palette
    COLORS = [
        "#29adff", # Blue
        "#ffa300", # Orange
        "#00e436", # Green
        "#ff77a8", # Pink
        "#83769c", # Purple
        "#ffcc00", # Yellow
        "#7e2553", # Dark Red
        "#008751", # Dark Green
        "#ff004d", # Red
        "#29366f", # Dark Blue
    ]
    
    _index = 0

    @classmethod
    def next_color(cls) -> str:
        color = cls.COLORS[cls._index]
        cls._index = (cls._index + 1) % len(cls.COLORS)
        return color
