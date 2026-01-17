from assassyn.frontend import *

DEBUG = False

def debug_log(*args, **kwargs):
    if DEBUG:
        log(*args, **kwargs)