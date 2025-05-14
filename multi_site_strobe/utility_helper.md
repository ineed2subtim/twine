# Utility helper files
All utility files are stored in utils/

1. **combine_results.sh** :- Consolidate results across sites into one top level directory. Useful for mapping files to each Twine run.
```
$ ./combine_results.sh twine_run_date		# Will create a top level directory that holds results from Twine's run on sites mentioned in sites variable.
							# By default it will use the sites run in the last experiment. If you want to give different sites, please uncomment the line mentioned inside the script
```
2. **check_completion.sh** :- Check completion status of Twine on each site. Useful to get a quick summary of successes and failures
```
$ ./check_completion.sh   	# Uses sites from last Twine run, and creates a summary of fails/succeeds
				# By default it will use the sites run in the last experiment. If you want to give different sites, please uncomment the line mentioned inside the script
```
Here is a sample output: <br>
```
$ ./check_completion.sh

RUTG GATECH MASS in combined_results
SITE RUTG terminated successfully
SITE GATECH terminated successfully
SITE MASS terminated successfully
3 sites succeeded
0 sites had a graceful_degradation
0 sites FAILED
0 sites IN PROGRESS

```

3. **check_errors.sh** :- Check errors and print upto last 15 lines of error message. Useful to look at errors across sites
```
$ ./check_errors.sh   		# Uses sites from last Twine run, and prints errors
				# By default it will use the sites run in the last experiment. If you want to give different sites, please uncomment the line mentioned inside the script
```
Below is a sample output: <br>
```
$ ./check_errors.sh

RUTG GATECH MASS in combined_results
RUTG: No error
GATECH: No error
MASS: No error

```

4. **delete_allslices.sh** := Forcefully delete Twine slices from each site, as mentioned in sites variable. <br>
This is used in the event that the user is unable to start a new slice upon submit, as the previous slice may still be active. <br>
This could happen if the Twine program terminated abruptly after creating a slice. <br>
 
```
$ ./delete_allslices.sh		# By default it will use the sites run in the last experiment. If you want to give different sites, please uncomment the line mentioned inside the script
```

5. **find_switchport.sh** := Create a map, between the listener NIC ports and the switch ports, that were mirrored for the entire sampling period <br>
find_switchport.sh depends on 'match_switchport.py' program. Please make certain that it is present in the utils directory before running it. <br>
An example usage is shown below: <br>

```
$ ./combine_results.sh experiment_run1		# First create a top level directory (experiment_run1 in this example) for the records in the last run
$ ./find_switchport.sh experiment_run1		# Will take care of untarring the compressed archives of the experiment; creating a node for each VM used; 
						# Creates a map for each port on the listener node and stores it in p1_mirrorinfo.txt and p2_mirrorinfo.txt 
```

The output structure of p1_mirrorinfo.txt and p2_mirrorinfo.txt is:
```
$ cat p1_mirrorinfo.txt

Information displaying which switch port was mirrored to node0 port p1

No match on pcap_10_08_2024_17:39:08
Full match on pcap_10_08_2024_17:44:28: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_17:49:48: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_17:55:09: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:00:29: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:05:49: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:11:09: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:16:29: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:21:49: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:27:09: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:32:29: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:37:49: Port mirrored is FourHundredGigE0/0/0/24
Full match on pcap_10_08_2024_18:43:09: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_18:48:29: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_18:53:49: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_18:59:10: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:04:30: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:09:50: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:15:10: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:20:30: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:25:50: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:31:10: Port mirrored is HundredGigE0/0/0/6
Full match on pcap_10_08_2024_19:36:30: Port mirrored is HundredGigE0/0/0/6
No match on pcap_10_08_2024_19:41:50

```

**No match** implies no switch ports were being mirrored to the listener port during that time <br>
**Full match** implies that switch port(mentioned in the line) was being mirrored to the listener port during that full time <br>

Here is an output from another site <br>
```
$ cat p1_mirrorinfo.txt

Information displaying which switch port was mirrored to node0 port p1

No match on pcap_10_08_2024_17:39:56
Full match on pcap_10_08_2024_17:45:17: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_17:50:37: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_17:55:57: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:01:17: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:06:37: Port mirrored is HundredGigE0/0/0/14
No match on pcap_10_08_2024_18:11:58
Full match on pcap_10_08_2024_18:17:18: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:22:38: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:27:58: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:33:19: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:38:39: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:43:59: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:49:19: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_18:54:40: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:00:00: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:05:20: Port mirrored is HundredGigE0/0/0/14
Partial match on first 14.792293548583984 seconds on pcap_10_08_2024_19:10:40: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:16:00: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:21:21: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:26:41: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:32:01: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:37:21: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:42:42: Port mirrored is HundredGigE0/0/0/14
Full match on pcap_10_08_2024_19:48:02: Port mirrored is HundredGigE0/0/0/14

```
**Partial match** on first/last 'n' seconds implies that a switch port (mentioned in the end of the line) was being mirrored to the listener port for a portion of the listening time <br>

6. **dev_utils/** := Meant for developer debugging, the user can ignore this folder.
