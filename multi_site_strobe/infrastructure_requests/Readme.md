### Using Infrastructure testing


The following functionality relies on you already having set up Twine, since you need the token file, and the enviroment from setting that up. A quick test if this is done is to print out the environment variables on your system: ```printenv```, then for this we need to see `WORKDIR` and `FABRIC_TOKEN_LOCATION` in that output. All the bandwidth data are as bits/s, so if you compare it with the information from the `infrastructure-metrics` website then remember to adjust, since that is shown as Bytes/s.
```
$ printenv | grep -e FABRIC_TOKEN_LOCATION -e WORKDIR
```

Files of interest: <br>
```
infrastructure_query.py
```

dependencies: 
```
    pip install requests
```

#### Entrypoint for testing or running the scripts

The scripts can either be run by importing them elsewhere as described in their specific sections below, or they can be run through the terminal. The script to run them would be ```./infrastructure_query.py --mode threshold```, substitute `threshold` with `busy_ports` or `time_series` based on what you want to run. If you don't want to run with the default variables then please edit `infrastructure_query.py` to serve your benefit. `infrastructure_query.py` is also a great resource for finding an example on how to call the different functions.

#### Finding the busyness of a port over the last x time:

If using it from a python file, you have to import the function <br>
```
from infrastructure_port_activity import busy_switch_ports
```

You can call the function <br>
```
busy_switch_ports(["WASH"], "90d")
```
Here the  first argument is the racks you want to test, the second is the timeframe you want to test. Which is basically the time until this very second. It can be `60s`, `1m`, `10m`, `1h`, `1d`, `30d`, `90d`, `1w`, `4w`, and so on. <br>

`m` means minute, `h` means hour, `d` means days and `w` means weaks. The lowest we can use is `1m` for 1 minute or the equivalent `60s`. The upper limit depends on rack. An example is: setting it to `90d` as we do above gives us the data from 90 days ago until today at the same time. <br>

If using it from the command line, you need to run it as:
```
$ python3 infrastructure_query.py --mode busy_ports
```
This returns an array where each rack specified in the request above is a seperate element.
An example return is: 
```
[{'rack': 'WASH', 'port_data': [{'HundredGigE0/0/0/15': 2}]}, {'rack': 'RUTG', 'port_data': [{'HundredGigE0/0/0/11': 24207129453.178673}]}]
```
It will also create a log file inside `infrastructure_request/logs/*`

#### Find the activity timeseries for the ports of racks

The results from this request will by default get saved to the `combined_results_racks.json` file in the infrastructure_requests logs folder. The name and location of this can be changed inside the `infrastructure_query.py` file.

You have to import the function ```from infrastructure_port_activity import get_time_series```
You can call the function ```get_time_series(["WASH"], "5m")``` where the  first argument is the racks you want to test, the second is the step for the query. This functionality is WIP, so currently assume 5 minutes is the default.

This finds the timeseries for the specific rack and timeframe for the last 1 years. That means that if you pass in `5m` then you will get all the rack information for based on 5 minute intervals for the last 1 year.

This returns an array where each rack specified in the request above is a seperate element.
An example return is(note the `...` means more data of the same form): 
`[
    {
        "rack": "RUTG",
        "port_data": {
            "tx": {
                "HundredGigE0/0/0/0": [
                    {
                        "time": 1708987603.626,
                        "ifHCOutBroadcastPkts": 0.0,
                        "ifHCOutMulticastPkts": 0.025322533333333338,
                        "ifHCOutOctets": 27.179519111111116,
                        "ifHCOutUcastPkts": 0.0,
                        "ifOutBroadcastPkts": 0.0,
                        "ifOutMulticastPkts": 0.025322533333333338,
                        "ifOutOctets": 27.179519111111116,
                        "ifOutUcastPkts": 0.0
                    },
                    ...
                ]
                ...
            }
            ...
        }
        ...
    }
    ...
]
`
It will also create a log file inside `infrastructure_request/logs/*` However this log is still a WIP, since it currently only provides the last few timeseries instead of the entire thing, but it does provide a good way to test if the output is as you expect.

Please also be mindful that this can take a while and may also create quite large files, so if testing many racks then a trick can be to batch them instead of all at once


#### Find if a port throughput exceeds a given threshold:


This is a system that checks the bandwidth for ports of specified sites during the time that twine is running. <br>
The user should run it, if they want to know if any site has generated traffic that exceeds the tcpdump performance threshold of 6Gbps. This would imply that packets were dropped, and the whole traffic picture was not attainable during this time. <br>

How it works: <br>
1. First you have to run twine.

To run the function from Python files you have to import the function
```
from infrastructure_port_activity import get_threshold
```

You can then call the function
```
get_threshold(racks, step_time,  threshold, log_folder, twine_log_folder)
```
where the  first argument is the racks you want to test, the second is the step for the query. The third is the threshold you want to check against, the forth is the log_folder where you want to save the log onto, the fifth is the twine_log_folder, if you want to grab the twine logs from a specific folder. 

if no twine_log_folder has been specified by the user the threshold mode takes the result from the latest run from twine, finding the sites from `utils/sites_used_last_experiment` and then finding the twine results from the main `multi_site_strobe` for those specific sites.

The step_time functionality is WIP, so currently assume 5 minutes is the default. <br>

If using it from the commandline, run as follows:
```
$ python3 infrastructure_query.py --mode threshold

```

The output will be printed to the terminal, and will be as below: <br>
```
# If threshold was not exceeded
Start printing ports where the threshold was exceeded for rack ATLA:


Finished printing the ports that were exceeded for rack: ATLA:

# If the threshold was exceeded
Start printing ports where the threshold was exceeded for rack STAR:
                                                                                                                                                                                                                                      HundredGigE0/0/0/1 on site STAR and at time 2024-11-22_01-26-48 went over the threshold of 6000000000.0 bps and had the value 60794384275.02 bps
HundredGigE0/0/0/1 on site STAR and at time 2024-11-22_01-31-48 went over the threshold of 6000000000.0 bps and had the value 57975446345.13 bps                                                                                      HundredGigE0/0/0/1 on site STAR and at time 2024-11-22_01-36-48 went over the threshold of 6000000000.0 bps and had the value 61531407716.77 bps

Finished printing the ports that were exceeded for rack: STAR:
```

##### Behind the scenes:
What happens is that, the script reads the json_records files for the sites specified inside the request or `infrastructure_query.py` if you run it through the script file, to find the specific ports for that site to query. Then it looks through the top level folders for those same sites for the `startup_log.txt` file where it finds time related information to bound the request. Then it uses the ports and the time to create a bounded request towards `infrastructure-metrics` to get the combined `tx+rx` bandwidth as bps for each port at 1 minute intervals. If the bps is higher than the specified threshold in step 3 then it will print out information about it.

##### Testing
A systematic approach has been made to ensure the code reflects the real data. The capabilities of the system was tested by pinging from and to a specific site and measuring the requests that get's sent out and received. This is not a perfect science since it's a global systen.
Check the data from this program against the data from hitting the system directly using the grafana interface.

##### Notes:

Minimum Step Size: The smallest chunk of time you can get data for is 60 seconds. You can get data for longer periods, like 1.5 minutes , 2 minutes, 5 minutes, or even 30 minutes, but not for shorter periods.

Checking Periods: If your chosen step size is 1 minute, then if your program runs for a specific time, like 10 minutes, you can get data for the whole 10-minute period. However, if you need data for a time period that isn’t a multiple of the minimum interval (like 9.5 minutes), you will miss the last part of the period. Of course, if you know that that's the period you are checking then you can adjust the step size to fit the 9.5 minutes aslong as you don't go lower than 1 minute.


##### Known issues:
As new sites get added and more sites gets updated, the following information may be outdated, but at the time of testing: The sites `STAR`, `UTAH`, `DALL`, `GPN`, `CLEM`, `LEARN`, `NEWY`, `CIEN`, `SCM` doesn't currently have the functionality to support this since they don't expose the information for the query.
