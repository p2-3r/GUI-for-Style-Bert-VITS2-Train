import datetime

def now():
    return datetime.datetime.now()

def printtime():
    l = f"{now().hour:02}:{now().minute:02}:{now().second:02}"
    j = Color.change(l, Color.GREEN)
    return j

class Color:

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    END = "\033[0m"

    @classmethod
    def change(self, content, color):
        if color is None:
            return content
        return color + content + self.END

class Template():
    def __init__(self, *, info_content="INFO", info_color=Color.BLUE, content_color=None) -> None:
        self.info_content = info_content
        self.info_color = info_color
        self.content_color = content_color

    def __call__(self, content:str):
        info = Color.change(self.info_content, self.info_color)
        recontent = Color.change(content, self.content_color)
        print(f"{info}|{printtime()}|{recontent}")

class Existing():
    info = Template(info_content="INFO", info_color=Color.BLUE)
    warn = Template(info_content="WARNING", info_color=Color.YELLOW)
    complete = Template(info_content="COMPLETE", info_color=Color.YELLOW)
    error = Template(info_content="ERROR", info_color=Color.RED)