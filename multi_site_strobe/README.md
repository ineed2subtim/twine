
# Getting Started


## Configurable parameters in multi_site_twine.sh

As a user, the following parameters can be configured:
```
1) tcpdump_filter: This stands for the filter expression that tcpdump will utilize inorder to filter packets. Default = "all"

e.g. tcpdump_filter = "tcp proto 80" will write only HTTP over TCP packets into the pcap file 
     tcpdump_filter = "all" will write all packets into the pcap file

2) listen_time: The time in seconds, that tcpdump will listen and filter for packets. 

3) wait_interval: The time in seconds, that the program will wait before restarting tcpdump to listen for packets

4) experiment_retries: This is the number of times the packet capture program will run on the listener. Between each run, it will wait for 'wait_interval' seconds

5) max_iter_per_retry: The number of times the tcpdump program will be started and stopped without any wait times. 

6) snaplen: The maximum number of bytes of the packet that will be written to the pcap file.

Example 1:
tcpdump_filter="all"
experiment_retries=15
wait_interval=60
snaplen=200
listen_time=20
max_iter_per_retry=1
```

This implies that the tcpdump capture program will write all packets to the pcap file. Each packet will be trimmed to 200 bytes depending on it's size. Tcpdump will listen for 20 seconds, then wait for 60 seconds. This listen and wait cycle will be run 15 times. <br>

A few more examples of modifying the experiment sampling time: <br>
Example 2:
```
tcpdump_filter="all"
experiment_retries=135
wait_interval=300
snaplen=200
listen_time=20
max_iter_per_retry=1

```
The above experiment sampling will take 135 * (300 + 20 * 1) = 43200 seconds = 12hrs <br>

Example 3:
```
tcpdump_filter="tcp"
experiment_retries=15
wait_interval=60
snaplen=200
listen_time=20
max_iter_per_retry=10

```
In this case, the experiment sampling time will be 15 * (60 + 20 * 10) = 3900 seconds = 65 minutes <br>

### Time considerations 

Using the parameters in Example 1, the total experiment time will be <br>
1. 80 * 15 = 1200 seconds. (sampling(a.k.a listening) time)
2. On top of this there will be a setup time of ~300 seconds (to submit the slice initially) 
3. Additional time that Twine uses to synchronize, copy, archive and download the data. We call this delay time
```
    if (total_experiment_time < 500):
        delay_factor = 1.50
    elif (total_experiment_time < 1000):
        delay_factor = 1.30
    elif (total_experiment_time < 5000):
        delay_factor = 1.15
    elif (total_experiment_time < 20000):
        delay_factor = 1.10
    else:
        delay_factor = 1.05

``` 
Therefore, the total time for this example would be ~ (1200 * 1.15) + 300 = 1680 seconds <br> 

## Run the script multi_site_twine.sh
The configurable parameters mentioned in Section 'Configurable parameters' can be modified by opening the script 'multi_site_twine.sh' and altering the values.

The FABRIC sites of interest can also specified in this script file. 
```
e.g.
sites(INDI MAX) --> implies that Twine will monitor the network dataplane of site INDI and site MAX
sites=(MICH)      --> implies that Twine will monitor the network dataplane of site MICH only 
```

Finally, to run the Twine program
```
(fabric-jupyter) bash-3.2$ ./multi_site_twine.sh
```
## Understanding the current state of the program
The Twine program runs as a background process, and if the user is running it across multiple sites at the same time, the output from multiple sites will be printed to the output screen. This might make following the flow difficult. <br>
Instead we have provided utility scripts to inform the user of the program's status. Once Twine has been started, on another terminal, the user can run: <br>
```
(fabric-jupyter) bash-3.2$ cd utils/	 		<--- Move into the utility scripts directory
(fabric-jupyter) bash-3.2$ ./check_completion.sh	 <--- This will show the current status of each SITE

# If you see any failures after running 'check_completion.sh', you can use this command
(fabric-jupyter) bash-3.2$ ./check_errors.sh	 	 <--- This will show more detail to the errors on each SITE

# Once the program has successfully completed, the user can run the following command:
(fabric-jupyter) bash-3.2$ ./combine_results.sh <experiment_result_directory>  <--- This will store the result from each SITE inside <experiment_result_directory> 

```
Once the information is available, the users can analyze the traffic on the pcap files. Please see the section **Understand output directory structure and log files** for information on the log structure <br>

For more information on these utility scripts and their output, please see below, the section **Utility helper files** <br>

# Utility helper files

[Utility helper files to aid with Twine experiments](utility_helper.md)

# Understand output directory structure and log files

Information on how the output files from Twine are organized and the log file messages can be found below: <br>
[Understand_log_file_and_opdirectories](understand_log_and_dir.md)

# Run Twine in user project mode
[Reference design to integrate twine in user topology](twine_usermode.md )

# Query Prometheus to check for throughput threshold overruns

[Tool to check for throughput overruns](infrastructure_requests/Readme.md)

# Known issues while running Twine:

A list of issues that have been observed over time. This list can be found here: <br>
[Known_twine_issues](known_twine_issues.md)

# JSON_records

The json_records/ directory contains a collection of json files, that hold switch port information on each of the SITES. <br>
These json files were derived from the FABRIC INFORMATION MODEL (FIM). <br>

