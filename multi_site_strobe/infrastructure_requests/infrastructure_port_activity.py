#!/usr/bin/env python3

import json
import argparse
import subprocess
import requests
import re
import os
import sys
import datetime
from dateutil.relativedelta import relativedelta

from infrastructure_request_helpers import (
    run_infrastructure_request_specific_timestamp_twine,
    create_log_folder,
    run_infrastructure_request_specific_timestamp,
    get_ports,
    open_txt_file_and_return_content,
    move_file,
    create_latest_dir
)


# racks is an array. ie: ["WASH"]
# Start time in string. ie: `1w`, `1d`, etc
def busy_switch_ports(racks, start_time):
    # Set the workdir to be the path to multi_site_strobe, assuming this folder stays at this level.
    workdir = os.getenv("WORKDIR")
    fabric_token_path = os.getenv("FABRIC_TOKEN_LOCATION")
    if workdir is None:
        raise EnvironmentError("The environment variable 'WORKDIR' is not set.")
    if fabric_token_path is None:
        raise EnvironmentError("The environment variable 'FABRIC_TOKEN_LOCATION' is not set.")
    # Current time
    log_folder = f"{workdir}/infrastructure_requests/logs"
    create_log_folder(log_folder)
    result = []

    if len(racks) < 1:  # If we pass an empty list we run it for all the racks in json_records

        directory = f"{workdir}/json_records/"
        file_names = os.listdir(directory)

        stripped_names = [
            f.replace("_records.json", "") for f in file_names if f.endswith("_records.json")
        ]

        print("Racks that will be tested are: ", stripped_names)
        racks = stripped_names

    for rack in racks:
        try:
            port_var, list_of_ports = get_ports(workdir, rack)
            query_port_in = {
                "query": f"rate(ifHCInOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{start_time}]) + "
                f"rate(ifHCOutOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{start_time}])"
            }
            query_url = "https://infrastructure-metrics.fabric-testbed.net/query"
            query_port_in_json = query_port_in
            # print("WHAT2")
            port_data = json.loads(
                run_infrastructure_request_specific_timestamp(
                    rack, query_url, query_port_in_json, list_of_ports, log_folder
                )
            )
            result.append({"rack": rack, "port_data": port_data})
        except ValueError as e:
            print(f"Value error: {e}")
            # print(traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    return result


# Give racks as an array and steps as a string. Like "5m", "30s", etc
def get_time_series(racks, step, time_period):
    # Set the workdir to be the path to multi_site_strobe, assuming this folder stays at this level.
    workdir = os.getenv("WORKDIR")
    fabric_token_path = os.getenv("FABRIC_TOKEN_LOCATION")
    if workdir is None:
        raise EnvironmentError("The environment variable 'WORKDIR' is not set.")
    if fabric_token_path is None:
        raise EnvironmentError("The environment variable 'FABRIC_TOKEN_LOCATION' is not set.")
    # Current time
    now = datetime.datetime.now()
    
    
    # Get the unit for the time period. ie: d, m, y
    time_unit = time_period[-1] # The last letter is the unit
    
    time_period_values = int(time_period[:-1]) # Everything but the last letter is the values
    time_delta = relativedelta(months=12)
    interval_length = 10 * 24 * 60 * 60
    if time_unit == 'd':
        time_delta = relativedelta(days=time_period_values)
        interval_length = 24 * 60 * 60 # 1 hour intervals
    elif time_unit == 'm':
        time_delta = relativedelta(months=time_period_values)
        interval_length = 10 * 24 * 60 * 60 # 10 day intervals
    elif time_unit == 'y':
        time_delta = relativedelta(years=time_period_values)
        interval_length = 10 * 24 * 60 * 60 # 10 day intervals
    else:
        raise ValueError(f"Invalid time unit '{time_unit}'. Please use 'd' for days and 'm' for months, and then 'y' for years")
    # Find the time relative to the time_period passed in
    time_period_ago = now - time_delta
    print("We are querying from ", time_period_ago)
    # convert to timestamp
    timestamp_now = now.timestamp()
    timestamp_prev = time_period_ago.timestamp()
    log_folder = f"{workdir}/infrastructure_requests/logs"
    create_log_folder(log_folder)
    result = []

    if len(racks) < 1:  # If we pass an empty list we run it for all the racks in json_records

        directory = f"{workdir}/json_records/"
        file_names = os.listdir(directory)

        stripped_names = [
            f.replace("_records.json", "") for f in file_names if f.endswith("_records.json")
        ]

        print("Racks that will be tested are: ", stripped_names)
        racks = stripped_names
    
    for i, rack in enumerate(racks):
        try:
            port_var, list_of_ports = get_ports(workdir, rack)

            # Initialize an empty list to hold results for this rack
            total_data_for_rack = {"tx": {}, "rx": {}}
            # There is a limit to how many results we can get back from prometheus/infrastructure
            # So we have to batch the requests and results
            # Start with the "prev" timestamp and loop through intervals of 15 days until 3 months
            interval_start = timestamp_prev
            #interval_length = 10 * 24 * 60 * 60  # 10 days in seconds

            interval_end = interval_start + interval_length
            counter = 1
            # Calculate number of rounds (intervals)
            # Convert timestamp to human-readable format (e.g., January 14, 2024)
            # print("TESTIN")
            first_day = True
            while interval_end <= timestamp_now:
                # print(f"Round {counter} of {rounds}")
                readable_date_start = datetime.datetime.fromtimestamp(interval_start).strftime(
                    "%B %d, %Y"
                )
                readable_date_end = datetime.datetime.fromtimestamp(interval_end).strftime(
                    "%B %d, %Y"
                )
                #counter += 1
                # print("COUNTER", counter)

                # label_replace(rate(ifHCInUcastPkts{rack="rutg", ifName="HundredGigE0/0/0/0"}[5m]), "query", "ifHCInUcastPkts", "", "")
                # or
                # label_replace(rate(ifHCOutOctets{rack="rutg", ifName="HundredGigE0/0/0/0"}[5m]), "query", "ifHCOutOctets", "", "")
                tx_query_port_in = {
                    #'query': f"rate(ifHCOutUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}])",
                    "query": f"""
label_replace(rate(ifHCOutUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCOutUcastPkts', '', '') 
or label_replace(rate(ifOutUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifOutUcastPkts', '', '')
or label_replace(rate(ifHCOutBroadcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCOutBroadcastPkts', '', '') 
or label_replace(rate(ifOutBroadcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifOutBroadcastPkts', '', '')
or label_replace(rate(ifHCOutMulticastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCOutMulticastPkts', '', '') 
or label_replace(rate(ifOutMulticastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifOutMulticastPkts', '', '')
or label_replace(rate(ifHCOutOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCOutOctets', '', '') 
or label_replace(rate(ifOutOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifOutOctets', '', '')
""",
                    "start": interval_start,
                    "end": interval_end,
                    "step": 300,
                }

                rx_query_port_in = {
                    #'query': f"rate(ifHCInOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}])",
                    #'query': f"rate(ifHCInUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}])",
                    "query": f"""
label_replace(rate(ifHCInUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCInUcastPkts', '', '') 
or label_replace(rate(ifInUcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifInUcastPkts', '', '')
or label_replace(rate(ifHCInBroadcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCInBroadcastPkts', '', '') 
or label_replace(rate(ifInBroadcastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifInBroadcastPkts', '', '')
or label_replace(rate(ifHCInMulticastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCInMulticastPkts', '', '') 
or label_replace(rate(ifInMulticastPkts{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifInMulticastPkts', '', '')
or label_replace(rate(ifHCInOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifHCInOctets', '', '') 
or label_replace(rate(ifInOctets{{job='data-sw', rack='{rack.lower()}', {port_var}}}[{step}]), 'query', 'ifInOctets', '', '')
""",
                    "start": interval_start,
                    "end": interval_end,
                    "step": 300,
                }
                query_url = "https://infrastructure-metrics.fabric-testbed.net/query_range"
                # tx_query_port_in_json = json.dumps(tx_query_port_in)
                # rx_query_port_in_json = json.dumps(rx_query_port_in)
                tx_port_data = json.loads(
                    run_infrastructure_request_specific_timestamp(
                        rack, query_url, tx_query_port_in, list_of_ports, log_folder, "tx"
                    )
                )
                rx_port_data = json.loads(
                    run_infrastructure_request_specific_timestamp(
                        rack, query_url, rx_query_port_in, list_of_ports, log_folder, "rx"
                    )
                )
                
                #print("ARE WE HERE", rx_port_data)

                if (tx_port_data or rx_port_data) and first_day:
                    if len(tx_port_data.items()) is not len(rx_port_data.items()):
                        print("tx and rx ports have different lengths")
                    first_day = False
                    # print("TX", tx_port_data.keys())
                    tx_values = list(tx_port_data.items())
                    first_port, first_port_data = tx_values[0]
                    # Get the time from the first record in the list
                    first_time = first_port_data[0]["time"]
                    formatted_datetime_utc = datetime.datetime.utcfromtimestamp(
                        first_time
                    ).strftime("%Y-%m-%d %H:%M")
                    print(
                        f"For rack {rack} the first values we find go are(utc time): {formatted_datetime_utc}"
                    )
                if not tx_port_data and not rx_port_data and not first_day:
                    print(
                        f"For rack {rack}, between {readable_date_start} and {readable_date_end} there is no data"
                    )
                elif len(total_data_for_rack["tx"]) < 1:  # First round, just add the data
                    for port, tx_value in tx_port_data.items(): # Only run over tx_port for efficientcy. tx and rx should be same
                        total_data_for_rack["tx"][port] = tx_value
                        total_data_for_rack["rx"][port] = rx_port_data.get(port, [])
                else:
                    # For the next rounds, append the result
                    for port, tx_value in tx_port_data.items():
                        # Append tx values
                        if port in total_data_for_rack["tx"]:
                            total_data_for_rack["tx"][port].extend(tx_value)
                        else:
                            total_data_for_rack["tx"][port] = [tx_value]

                        # Append rx values
                        if port in total_data_for_rack["rx"]:
                            total_data_for_rack["rx"][port].extend(rx_port_data.get(port, []))
                        else:
                            total_data_for_rack["rx"][port] = [rx_port_data.get(port, [])]
                # print("INTERVAL", interval_end, "interval_start", timestamp_now)
                # Add 5 minutes to start timestamp so we don't get overlapping values on the boundries
                interval_start = interval_end + 300
                interval_end = interval_start + interval_length

            result.append({"rack": rack, "port_data": total_data_for_rack})
        except ValueError as e:
            print(f"Value error: {e}")
            # print(traceback.format_exc())
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    return result


# Print out racks that break the threshold
def get_threshold(step_time, threshold, log_folder, twine_log_folder):
    workdir = os.getenv("WORKDIR")
    fabric_token_path = os.getenv("FABRIC_TOKEN_LOCATION")
    if workdir is None:
        raise EnvironmentError("The environment variable 'WORKDIR' is not set.")
    if fabric_token_path is None:
        raise EnvironmentError("The environment variable 'FABRIC_TOKEN_LOCATION' is not set.")
    racks = []
    if not twine_log_folder:
        print("twine_log_folder has not been specified, finding the latest run from twine.")
        content = open_txt_file_and_return_content(f"{workdir}/utils/sites_used_last_experiment")
        racks = content.split()
        create_latest_dir("latest")
        for site in racks:
            move_file(site, workdir)  
        twine_log_folder = "latest"    
    else:
        file_names = os.listdir(twine_log_folder)
        print("Racks that will be tested are: ", file_names)
        racks = file_names

    
    # Current time
    log_folder = f"{workdir}/infrastructure_requests/logs"
    create_log_folder(log_folder)
    threshold_result = []
    # print("TESTING")
    for rack in racks:
        threshold_result.append(run_infrastructure_request_specific_timestamp_twine(
            rack, step_time, threshold, log_folder, twine_log_folder
        ))

    return "Look at specific log files for each rack"


def main():
    terminal_parser = argparse.ArgumentParser(description="Parse the racks to use")
    terminal_parser.add_argument(
        "-r",
        "--racks",  # argument
        nargs="+",  # allow for lists
        default=[],
        help="List of racks to query",
    )
    terminal_parser.add_argument(
        "-s_t", "--start_time", default="1w", help="When to start querying from"  # argument
    )

    args = terminal_parser.parse_args()
    print("Racks selected are test", args.racks)
    busy_switch_ports(args.racks, args.start_time)


if __name__ == "__main__":
    main()
