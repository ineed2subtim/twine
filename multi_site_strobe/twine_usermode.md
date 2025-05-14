## Reference design to integrate Twine in a user experiment

**The code in singleuser_ping_example.py is derived from the example provided in  /jupyter-examples-main/fabric_examples/fablib_api/create_port_mirror/port_mirror.ipynb**

Specify the 2 sites being used for the experiment inside singleuser_ping_example.py e.g. site1, site2 = ('INDI', 'MAX')<br>

For this experiment, set multi_site_twine.sh to have the following values: <br>
```
# This will in effect run the twine listener for (20 + 300) * 1 * 1 = 320 seconds
experiment_retries=1
wait_interval=20
listen_time=300
max_iter_per_retry=1

```
Then execute the program as below: <br>
```
python3 singleuser_ping_example.py
```

## Program flow
1. Create your program topology as needed.
2. In this case there are 2 nodes, e.g. node1 on INDI; node2 on MAX with an L3 connection between them.
3. Submit slice to establish resources and connections.

Once the slice submission has succeeded, obtain the peer switch port of node1 on INDI <br>
```
mirror_port_name = node1.get_interfaces()[0].get_peer_port_name()
```

Then invoke the twine program using the below statements: <br>
```
# site1 in this example would be INDI
# mode should be single_user
# mirror_port_name is obtained as mentioned above
# slice_name is your program's slice_name

os.system(f"./multi_site_twine.sh {mode} {site1} {mirror_port_name} \"{slice_name}\" \"{shm_name}\"")
```

## Synchronizing your program with Twine

Import module that handles creating and removing shared memory <br>
```
import twine_shm
```

Create the shared memory and wait for the 'start' message to arrive from the Twine program OR wait for a default timeout period of 1000 seconds. <br>

```
shm_name, shm_p = twine_shm.create_sharedmem()
# Make sure to start Twine before running synch_pathwork() and after running create_sharedmem()
os.system(f"./multi_site_twine.sh {mode} {site1} {mirror_port_name} \"{slice_name}\" \"{shm_name}\"")
twine_shm.synch_twine("start", shm_p)

# Timeout period can be overwritten by users, for example:
twine_shm.synch_twine("start", shm_p, 1500)

```

Once your program is ready to end, wait for a 'stop' message from the Twine program OR wait for 1000 seconds by default. <br>
```
twine_shm.synch_twine("stop", shm_p)
twine_shm.remove_sharedmem(shm_p)

```

### Twine execution :
1. Twine will create a listener node on the same site as node0
2. Listener slice will listen to packets mirrored from the earlier peer port
3. Submit listening slice
4. Start listening
5. Listen for ICMP echo packets being sent/received from INDI to MAX

## Output

1. Check the utils/check_completion.sh script to see if the program has exited. <br>
See[Utility helper files to aid with Twine experiments](utility_helper.md) for more information on script usage. <br>
2. View the output in INDI/latest_run/
3. Extract the .tgz files and check if the pcap has icmp echo packets, as expected <br>
