ANSI_RED = "\x1b[31m"
ANSI_GREEN = "\x1b[32m"
ANSI_YELLOW = "\x1b[33m"
ANSI_BLUE = "\x1b[34m"
ANSI_MAGENTA = "\x1b[35m"
ANSI_CYAN = "\x1b[36m"
ANSI_GRAY = "\x1b[37m"
ANSI_RESET = "\x1b[0m"

def red(string):
    return f"{ANSI_RED}{string}{ANSI_RESET}"

def green(string):
    return f"{ANSI_GREEN}{string}{ANSI_RESET}"

def yellow(string):
    return f"{ANSI_YELLOW}{string}{ANSI_RESET}"

def blue(string):
    return f"{ANSI_BLUE}{string}{ANSI_RESET}"

def magenta(string):
    return f"{ANSI_MAGENTA}{string}{ANSI_RESET}"

def cyan(string):
    return f"{ANSI_CYAN}{string}{ANSI_RESET}"

def gray(string):
    return f"{ANSI_GRAY}{string}{ANSI_RESET}"
