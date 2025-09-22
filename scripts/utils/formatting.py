def bold(text: str):
    return f"\033[1m{text}\033[0m"


def gray(text: str):
    return f"\033[38;5;245m{text}\033[0m"


def blue(text: str):
    return f"\033[38;5;45m{text}\033[0m"


def green(text: str):
    return f"\033[38;5;49m{text}\033[0m"


def light_gray(text: str):
    return f"\033[38;5;237m{text}\033[0m"


def yellow(text: str):
    return f"\033[38;5;226m{text}\033[0m"


def print_joined(*args):
    print(" ".join(args))
