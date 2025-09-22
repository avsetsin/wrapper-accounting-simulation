from scripts.utils.formatting import bold, light_gray, yellow


def print_line(length: int):
    print(light_gray("─" * length))


def print_joined(*args):
    print(" ".join(args))


def print_title(title: str):
    print()
    print(bold(title))
