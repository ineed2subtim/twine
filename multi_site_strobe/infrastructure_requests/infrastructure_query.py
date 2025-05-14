#!/usr/bin/env python3

# Assuming the busy_switch_ports function is defined in a module named 'your_module'
from infrastructure_port_activity import get_time_series, get_threshold, busy_switch_ports
import argparse
import json

# Functions for the --mode argument


def get_threshold_init(step_time, threshold, log_folder, twine_log_folder=""):
    # Function to handle threshold mode
    print("Running Threshold Mode")
    result = get_threshold(step_time, threshold, log_folder, twine_log_folder)
    return result


def get_time_series_init(racks, start_time, time_period):
    # Function to handle time_series mode
    print("Running Time Series Mode")
    result = get_time_series(racks, start_time, time_period)
    return result


def busy_switch_ports_init(racks, new_start):
    # Function to handle busy_ports mode
    print("Running Busy Ports Mode")
    result = busy_switch_ports(racks, new_start)
    print("result", result)
    return result


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Run different modes based on --mode argument.")
    parser.add_argument(
        "--mode",
        choices=["threshold", "time_series", "busy_ports"],
        required=True,
        help="The choices of mode to run (threshold, time_series, busy_ports)",
    )
    racks = ['AMST']
    # racks = ['AMST', 'ATLA', 'BRIST', 'CERN', 'CLEM', 'DALL', 'FIU', 'GATECH', 'GPN', 'HAWI', 'INDI', 'KANS', 'LOSA', 'MASS', 'MAX', 'MICH', 'NCSA', 'NEWY', 'PRIN', 'PSC', 'RUTG', 'SALT', 'SEAT', 'STAR', 'TACC', 'TOKY', 'UCSD', 'UTAH', 'WASH']
    step_time = 60
    log_folder = "logs"
# time_series specific argument
    start_time = "5m"
    time_period = "12d"
# busy_ports specific argument
    new_start = "1d"
# threshold specific argument
    threshold = 6000000000
    twine_log_folder = "latest"

    # Parse the arguments
    args = parser.parse_args()
    result = []
    # Call the appropriate function based on the --mode argument
    if args.mode == "threshold":
        result = get_threshold_init(step_time, threshold, log_folder, twine_log_folder)
    elif args.mode == "time_series":
        result = get_time_series_init(racks, start_time, time_period)
    elif args.mode == "busy_ports":
        result = busy_switch_ports_init(racks, new_start)

    # Save the result to json file
    with open("logs/combined_results_racks.json", "w") as json_file:
        json.dump(result, json_file, indent=4)


if __name__ == "__main__":
    main()
