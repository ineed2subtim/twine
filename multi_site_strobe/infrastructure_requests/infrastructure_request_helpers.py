#!/usr/bin/env python3

import json
import requests
import re
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import shutil


# Create the log folder if it does not exist
# Delete all the files in the folder if it does exist
def create_log_folder(log_path):
    if os.path.exists(log_path):
        print("At the start of every run, clean out the log folder for any existing files")
        for file_name in os.listdir(log_path):
            file_path = os.path.join(log_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(log_path)
        print(log_path, " didn't exist, so was created")

def create_latest_dir(target_dir):
    # Create the target_dir if it doesnt exist
    os.makedirs(target_dir, exist_ok=True)
    
    # Empty out the target dir if there are files in it
    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        if os.path.isdir(item_path):  # It's a directory
            shutil.rmtree(item_path)  # Delete everything in the directory
        else:
            os.remove(item_path)  # Remove the file

def move_file(site, workdir, file_to_move="startup_log.txt", target_dir="latest"):
    os.makedirs(f"{target_dir}/{site}", exist_ok=True) # create the site directory
    # Define the full source and target file paths
    source_path = os.path.join(f"{workdir}/{site}", file_to_move)
    target_path = os.path.join(f"{target_dir}/{site}", file_to_move)
    # Check if the source file exists before moving
    if os.path.isfile(source_path):
        shutil.copy(source_path, target_path)
        print(f"File '{file_to_move}' moved successfully!")
    else:
        print(f"File '{file_to_move}' does not exist in {workdir}/{site}.")
# Open a json file and return content
def open_json_file_and_return_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print("File doesn't exist at ", file_path)
    except IOError as io:
        print("IO error", io)
    except json.JSONDecodeError as json_error:
        print("JSON decode error while opening file at :", file_path, "error: ", json_error)
    except ValueError as value_error:
        print("Value error:", value_error)
    except Exception as e:
        print("An unexpected error occurred:", e)


# Open a txt file and return content
def open_txt_file_and_return_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = file.read()
            return data
    except FileNotFoundError:
        print("File doesn't exist at ", file_path)
    # except json.JSONDecodeError:
    # print("Error with the JSON")
    except IOError as io:
        print("IO error", io)


# Get the timestamp data from the log files create by twine
def twine_info(file="test.json"):
    file_data = open_txt_file_and_return_content(file)
    start_time_pattern = r"time_tcpdump_start\s+([\d.]+)\s+seconds"
    sampling_time_pattern = r"Final experiment time:\s+([\d.]+)\s+seconds"

    time_tcpdump_start = None
    total_sampling_time = None
    if file_data is not None:
        found_start_time_string = re.search(start_time_pattern, file_data)
        found_sampling_time_string = re.search(sampling_time_pattern, file_data)
        if found_start_time_string:
            time_tcpdump_start = float(found_start_time_string.group(1))
        if found_sampling_time_string:
            total_sampling_time = time_tcpdump_start + float(found_sampling_time_string.group(1))
    return time_tcpdump_start, total_sampling_time


# Get the port info from twine
def twine_port_info(file="test.json"):
    file_data = open_json_file_and_return_content(file)
    port_names = []
    if file_data is not None:
        for port_data in file_data:
            port_names.append(port_data["cp"]["properties"]["Name"])
        return port_names


def get_ports(workdir, rack):
    port_file = f"{workdir}/json_records/{rack.upper()}_records.json"  # Get the file with the port information for the specific rack
    port_names = twine_port_info(port_file)  # Get the port information to query
    unique_ports = set(
        port.split(".")[0] for port in port_names
    )  # Find the unique ports and simplify the names
    # Exclude certain port prefixes
    port_prefixes_ignore = ("p", "Bundle")
    filtered_ports = {
        port
        for port in unique_ports
        if not any(port.startswith(prefix) for prefix in port_prefixes_ignore)
    }
    joined_ports = "|".join(filtered_ports) if filtered_ports and len(filtered_ports) > 0 else ""
    port_query_var = f"ifName=~'{joined_ports}'" if joined_ports else ""
    return port_query_var, filtered_ports


def run_infrastructure_request_specific_timestamp(
    rack, query_url, query_port_in_json, list_of_ports, log_folder, log_key=None
):
    """
    Function that checks the racks from the folder '/latest' and finds the timeframe to check the port
    bandwidth and then queries the infrastructure.
    Arguments:
    rack                  - The rack to send request about
    step                  - The step(how often we query the server for data)
    log_folder            - The folder to save the log file in

    """

    workdir = os.getenv("WORKDIR")
    if workdir is None:
        raise EnvironmentError("The environment variable 'WORKDIR' is not set.")

    result = (
        rack_request(rack, query_port_in_json, query_url, list_of_ports, log_folder, log_key)
        if log_key
        else rack_request_busy_ports(rack, query_port_in_json, query_url, list_of_ports, log_folder)
    )
    return result


def curl_request(query, query_url):
    """
    Request that takes a query and does a requests to the query_url and returns a json
    Arguments:
    rack        - Site that get's queries
    query       - Prometheus query that will be run
    start_time  - The start time bound we are querying
    end_time    - The end time bound we are querying
    step        - The step(how often we query the server for data)

    """
    try:
        fabric_token_path = os.getenv("FABRIC_TOKEN_LOCATION")
        if fabric_token_path is None:
            raise EnvironmentError("The environment variable 'FABRIC_TOKEN_LOCATION' is not set.")

        data = open_json_file_and_return_content(fabric_token_path)

        token = data["id_token"]
        # Add the token to the header
        headers = {
            "Authorization": f"fabric-token {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Add query to the data object
        data = query
        # run the post request towards the query_url
        response = requests.post(query_url, headers=headers, data=data)
        # keys = response.json()["data"]["result"][0].keys() if response.json()["data"]["result"] else []
        # if  response.json()["data"]["result"]:
        # print("RESPOSNE", response.json()["data"]["result"][0]["metric"])

        # check for success and print success or error code
        if response.status_code == 200:
            return response.json()
        else:
            print("Request failed with status code:", json.dumps(response.status_code, indent=2))
            return response.content
    except ValueError as e:
        print(f"ValueError occurred: {e}")
        sys.exit(1)  # Exit with an error code
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)  # Exit with an error code


def rack_request_busy_ports(rack, query, query_url, ports, log_folder):
    """
    Function that calls a requests towards infrastructure and adds to file $log_file
    Arguments:
    rack                  - The rack to send request about
    ports                 - The ports to get information about
    start_time            - The start time bound we are querying
    end_time              - The end time bound we are querying
    step                  - The step(how often we query the server for data)
    threshold             - The threshold that if we go over we print out the port that goes over
    log_folder            - The folder to save the log file in

    """
    # Construct and run a query to get the per port bandwidth for data going in to the rack
    log_file = f"{rack}_infrastructure_requests_logfile.json"
    # Perform a request to the infrastructure
    in_response = curl_request(query, query_url)
    # print("TESTING", in_response, query, query_url)
    in_data = (
        in_response["data"]["result"]
        if "data" in in_response and "result" in in_response["data"]
        else ""
    )

    temp_data = {}
    final_json_object = {}
    if os.path.exists(log_folder + "/" + log_file):
        with open(log_folder + "/" + log_file, "r") as file:
            final_json_object = json.load(file)
    else:
        final_json_object = {}

    json_string = None

    final_json_object["ports_in_graph_model_but_not_in_mflib"] = {}
    if "query_range" in query_url:

        if len(in_data) > 0 and "values" in in_data[0]:
            for port_data in in_data:
                values = port_data["values"]
                values = [[time, value * 8] for (time, value) in values]  # Make it into bits/s
                name = port_data["metric"]["ifDescr"]
                temp_data[name] = values

        json_string = temp_data
        final_json_object["ports_time_value"] = dict(temp_data)
    else:
        final_json_object["ports_sorted_by_sum_rx_tx_activity"] = {}
        for port_data in in_data:
            value = float(port_data["value"][1]) * 8
            name = port_data["metric"]["ifDescr"]
            temp_data[name] = value
        sorted_data = sorted(temp_data.items(), key=lambda x: x[1], reverse=True)
        json_string = sorted_data  # Try to convert to JSON
        final_json_object["ports_sorted_by_sum_rx_tx_activity"] = dict(sorted_data)
    try:
        json_string = json.dumps(json_string)
        keys = set(temp_data.keys())
        # Add some information about the ports we are querying to the log file
        if ports and len(ports) > 0 and len(ports) != len(keys):
            final_ports_set = set(ports)
            final_json_object["ports_in_graph_model_but_not_in_mflib"] = list(
                final_ports_set - keys
            )

        with open(log_folder + "/" + log_file, "w") as file:
            # Write the log object to the log file
            json.dump(final_json_object, file, indent=4)
        return json_string  # If successful, return the response
    except (TypeError, ValueError) as e:
        print("Error converting to JSON:", e)
        return {"error": "Invalid data for JSON serialization"}  # Return an error response


def time_series_formating_helper(port_data_spec, val, result):
    # Since the octet strings need to be * 8 to make them into bits/s we filter for the specific names
    if any(
        query in port_data_spec["metric"]["query"]
        for query in ["ifHCOutOctets", "ifOutOctets", "ifHCInOctets", "ifInOctets"]
    ):
        # Replace "Octets" with "bits/s" in the query string
        modified_query = port_data_spec["metric"]["query"].replace("Octets", "Bits/s")
        # Store the result, multiplying by 8 to convert to bits
        result[modified_query] = float(val) * 8
    else:
        # If not one of the target queries, store the value without modification
        result[port_data_spec["metric"]["query"]] = float(val)


def rack_request(rack, query, query_url, ports, log_folder, log_key):
    """
    Function that calls a requests towards infrastructure and adds to file $log_file
    Arguments:
    rack                  - The rack to send request about
    ports                 - The ports to get information about
    start_time            - The start time bound we are querying
    end_time              - The end time bound we are querying
    step                  - The step(how often we query the server for data)
    threshold             - The threshold that if we go over we print out the port that goes over
    log_folder            - The folder to save the log file in

    """

    # Construct and run a query to get the per port bandwidth for data going in to the rack
    log_file = f"{rack}_infrastructure_requests_logfile.json"
    # Perform a request to the infrastructure
    in_response = curl_request(query, query_url)
    in_data = (
        in_response["data"]["result"]
        if "data" in in_response and "result" in in_response["data"]
        else ""
    )

    temp_data = {}
    final_json_object = {}

    
    final_json_object = {}
    final_json_object[log_key] = {}
    final_json_object[log_key]["ports_time_value"] = {}

    json_string = None
    final_json_object["ports_in_graph_model_but_not_in_mflib"] = {}
    if "query_range" in query_url:

        if len(in_data) > 0 and "values" in in_data[0]:
            for (
                port_data_1,
                port_data_2,
                port_data_3,
                port_data_4,
                port_data_5,
                port_data_6,
                port_data_7,
                port_data_8,
            ) in zip(
                in_data[::8],
                in_data[1::8],
                in_data[2::8],
                in_data[3::8],
                in_data[4::8],
                in_data[5::8],
                in_data[6::8],
                in_data[7::8],
            ):
                times_set = set()
                for port_data in [
                    port_data_1,
                    port_data_2,
                    port_data_3,
                    port_data_4,
                    port_data_5,
                    port_data_6,
                    port_data_7,
                    port_data_8,
                ]:
                    for time, _ in port_data["values"]:
                        times_set.add(time)

                # Convert set to list and sort it
                times_list = sorted(times_set)
                values = []

                for time in times_list:

                    value1 = next((val for t, val in port_data_1["values"] if t == time), None)
                    value2 = next((val for t, val in port_data_2["values"] if t == time), None)
                    value3 = next((val for t, val in port_data_3["values"] if t == time), None)
                    value4 = next((val for t, val in port_data_4["values"] if t == time), None)
                    value5 = next((val for t, val in port_data_5["values"] if t == time), None)
                    value6 = next((val for t, val in port_data_6["values"] if t == time), None)
                    value7 = next((val for t, val in port_data_7["values"] if t == time), None)
                    value8 = next((val for t, val in port_data_8["values"] if t == time), None)

                    result = {"time": time}

                    # Check if the value exists for each port and process accordingly
                    if value1:
                        time_series_formating_helper(port_data_1, value1, result)
                    if value2:
                        time_series_formating_helper(port_data_2, value2, result)
                    if value3:
                        time_series_formating_helper(port_data_3, value3, result)
                    if value4:
                        time_series_formating_helper(port_data_4, value4, result)
                    if value5:
                        time_series_formating_helper(port_data_5, value5, result)
                    if value6:
                        time_series_formating_helper(port_data_6, value6, result)
                    if value7:
                        time_series_formating_helper(port_data_7, value7, result)
                    if value8:
                        time_series_formating_helper(port_data_8, value8, result)

                    # Append the result dictionary to the values list
                    values.append(result)
                name = port_data_1["metric"]["ifDescr"]
                temp_data[name] = values

        json_string = temp_data
        final_json_object[log_key]["ports_time_value"] = dict(temp_data)
    else:
        final_json_object["ports_sorted_by_sum_rx_tx_activity"] = {}
        for port_data in in_data:
            value = float(port_data["value"][1]) * 8
            name = port_data["metric"]["ifDescr"]
            temp_data[name] = value
        sorted_data = sorted(temp_data.items(), key=lambda x: x[1], reverse=True)
        json_string = sorted_data  # Try to convert to JSON
        final_json_object["ports_sorted_by_sum_rx_tx_activity"] = dict(sorted_data)
    try:
        json_string = json.dumps(json_string)
        keys = set(temp_data.keys())
        # Add some information about the ports we are querying to the log file
        if ports and len(ports) > 0 and len(ports) != len(keys):
            final_ports_set = set(ports)
            final_json_object["ports_in_graph_model_but_not_in_mflib"] = list(
                final_ports_set - keys
            )

        return json_string  # If successful, return the response
    except (TypeError, ValueError) as e:
        print("Error converting to JSON:", e)
        return {"error": "Invalid data for JSON serialization"}  # Return an error response


def curl_request_twine(query, query_url, start_time, end_time, step):
    """
    Request that takes a query and does a requests to the query_url and returns a json
    Arguments:
    rack        - Site that get's queries
    query       - Prometheus query that will be run
    start_time  - The start time bound we are querying
    end_time    - The end time bound we are querying
    step        - The step(how often we query the server for data)

    """
    try:
        if start_time == "None" or end_time == "None" or step == "None":
            raise ValueError(
                "start_time, end_time or step cannot be None. Check if the log files has been generated correctly."
            )
            
        # Since we currently measure the last {step} seconds[{step}s] in the request) we also need
        # to adjust the start_time
        # to account for that, since our request takes the last {step} seconds before the current timestamp, and
        # that can cause us to  measure {step} seconds before our actual desired start_time

        start_time_adjusted = str(float(start_time) + float(step))
        fabric_token_path = os.getenv("FABRIC_TOKEN_LOCATION")
        if fabric_token_path is None:
            raise EnvironmentError("The environment variable 'FABRIC_TOKEN_LOCATION' is not set.")
        
        data = open_json_file_and_return_content(fabric_token_path)

        token = data["id_token"]
        
        # Add the token to the header
        headers = {
            "Authorization": f"fabric-token {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Add query to the data object
        data = {"query": query, "start": start_time_adjusted, "end": end_time, "step": int(step)}
        # run the post request towards the query_url
        response = requests.post(query_url, headers=headers, data=data)
        # check for success and print success or error code
        if response.status_code == 200:
            return response.json()
        else:
            print("Request failed with status code:", json.dumps(response.status_code, indent=2))
            return response.content
    except ValueError as e:
        print(f"ValueError occurred: {e}")
        sys.exit(1)  # Exit with an error code
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)  # Exit with an error code


def twine_rack_request(
    rack, query_url, start_time, end_time, step, threshold, log_folder, ports
):
    if start_time is None or end_time is None or step is None:
        print("start_time, end_time and step must be provided.")
        sys.exit(1)  # Exit with an error code

    # Construct and run a query to get the per port bandwidth for data going in to the rack
    log_file = f"{rack}_infrastructure_requests_logfile.json"
    joined_ports = "|".join(ports) if ports and len(ports) > 0 else ""
    port_query_var = f"ifName=~'{joined_ports}'" if joined_ports else ""
    query_port_in = f"rate(ifHCInOctets{{job='data-sw', rack='{rack.lower()}', {port_query_var}}}[{step}s]) + rate(ifHCOutOctets{{job='data-sw', rack='{rack.lower()}', {port_query_var}}}[{step}s])"

    # Perform a request to the infrastructure
    in_response = curl_request_twine(query_port_in, query_url, start_time, end_time, step)
    in_data = (
        in_response["data"]["result"]
        if "data" in in_response and "result" in in_response["data"]
        else ""
    )
    combined_final_data = {}
    final_json_object = {}
    final_json_object["iterations"] = {}
    threshold = float(threshold)  # transform from string to int.
    # Create the object structure for our log file so that we can easily add values later
    if len(in_data) > 0 and "values" in in_data[0]:
        for i, time_data in enumerate(in_data[0]["values"]):
            final_json_object["iterations"][i] = {}
            date_obj = datetime.fromtimestamp(float(time_data[0]))
            time_as_readable_format = date_obj.strftime("%Y-%m-%d_%H-%M-%S")
            final_json_object["iterations"][i]["time"] = time_as_readable_format
    else:
        print("No data returned from query")
        sys.exit(1)
    print(f"\nStart printing ports where the threshold was exceeded for rack {rack.upper()}: \n ")

    # Go through all the ports and look for values that exceed the threshold
    for port_data in in_data:
        for index, value in enumerate(port_data["values"]):
            if float(value[1]) * 8 > threshold:
                date_obj = datetime.fromtimestamp(float(value[0]))
                time_as_readable_format = date_obj.strftime("%Y-%m-%d_%H-%M-%S")
                # We do *8 since we originally get the values as B/s, but we want them as bps instead
                print(
                    f'{port_data["metric"]["ifDescr"]} on site {rack.upper()} and at time {time_as_readable_format} went over the threshold of {threshold} bps and had the value {"%.2f" % (float(value[1])*8)} bps'
                )
            combined_final_data[index] = {}

            combined_final_data[index][port_data["metric"]["ifDescr"]] = value[1]

        # Create object to write to log file
        for index, val in enumerate(port_data["values"]):
            # We do *8 since we originally get the values as B/s, but we want them as bps instead
            final_json_object["iterations"][index][port_data["metric"]["ifDescr"]] = (
                float(val[1]) * 8
            )

    print(f"\nFinished printing the ports that were exceeded for rack: {rack.upper()}: ")

    # Add some information about the ports we are querying to the log file
    if ports and len(ports) > 0 and len(ports) != len(final_json_object["iterations"][index]) - 1:
        final_ports_set = set(ports)
        final_rx_data_set = set(final_json_object["iterations"][index])
        final_json_object["ports_in_graph_model_but_not_in_mflib"] = list(
            final_ports_set - final_rx_data_set
        )
    with open(log_folder + "/" + log_file, "w") as file:
        # Write the log object to the log file
        json.dump(final_json_object, file, indent=4)


def run_infrastructure_request_specific_timestamp_twine(
    rack, step, threshold="10000", log_folder="log", twine_log_folder="latest"
):
    """
    Function that checks the racks from the folder '/latest' and finds the timeframe to check the port
    bandwidth and then queries the infrastructure.
    Arguments:
    rack                  - The rack to send request about
    step                  - The step(how often we query the server for data)
    log_folder            - The folder to save the log file in

    """
    port_file = f"../json_records/{rack.upper()}_records.json"  # Get the file with the port information for the specific rack
    start_timestamp, end_timestamp = twine_info(
        f"{twine_log_folder}/{rack.upper()}/startup_log.txt"
    )  # Get the timestamps
    # if (start_timestamp == None or end_timestamp == None):
    #    raise Exception("Could not find start_time or end_time for rack.", rack.upper())
    port_names = twine_port_info(port_file)  # Get the port information to query
    unique_ports = set(
        port.split(".")[0] for port in port_names
    )  # Find the unique ports and simplify the names
    # Exclude certain port prefixes
    port_prefixes_ignore = ("p", "Bundle")
    filtered_ports = {
        port
        for port in unique_ports
        if not any(port.startswith(prefix) for prefix in port_prefixes_ignore)
    }
    query_url = "https://infrastructure-metrics.fabric-testbed.net/query_range"
    result = twine_rack_request(
        rack,
        query_url,
        str(start_timestamp),
        str(end_timestamp),
        str(step),
        threshold,
        log_folder,
        list(filtered_ports),
    )
    return result
