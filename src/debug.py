from assassyn.frontend import *

DEBUG = False

def set_debug_mode(mode: bool):
    global DEBUG
    DEBUG = mode

def debug_log(*args, **kwargs):
    if DEBUG:
        log(*args, **kwargs)