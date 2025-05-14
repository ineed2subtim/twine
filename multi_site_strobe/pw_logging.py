import os

log_selected_mode = 0
NONE = "NONE"
INFO = "INFO"
DEBUG = "DEBUG"


log_dict = {"NONE": 0, "INFO": 1, "DEBUG": 2}

def set_log_mode(mode):
    global log_selected_mode
    if mode not in log_dict.keys():
        print("Invalid logging mode selected, setting logging to INFO")
        log_selected_mode = 1
        return
    log_selected_mode = log_dict[mode]

def log(curr_mode, output_string):
    global log_selected_mode
    if curr_mode not in log_dict.keys():
        return
    if log_dict[curr_mode] <= log_selected_mode:
        print(output_string)
