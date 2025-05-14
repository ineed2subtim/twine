## Known issues while running Twine

The following issues can be seen by running './check_errors.sh' script, or by perusing the 'startup_log.txt' file <br>

# Fixable issues
1. Slice Exception: Slice Name: Traffic Listening Demo GATECH, Slice ID: 84b0bc73-8fe7-4e32-962f-2c8fccc47b76: Slice Exception: Slice Name: Traffic Listening Demo GATECH, Slice ID: 84b0bc73-8fe7-4e32-962f-2c8fccc47b76: Node: GATECH_node0, Site: GATECH, State: Closed, Insufficient resources: No candidates nodes found to serve res: #3d425fc6-0f44-4e98-a0cc-d9ee9358cb8f slice: [Traffic Listening Demo GATECH(84b0bc73-8fe7-4e32-962f-2c8fccc47b76) Owner:] state:[Nascent,Ticketing] # <br>

2. Insufficient RAM <br>

3. Insufficient CPU <br>

4. Insufficient storage <br>

5. No IP addresses available <br>
```
Fix: These issues are due to a lack of resources on FABRIC for a specific site. Try to run the experiment on a different site or try again later.
```

6. failed lease update- all units failed priming: Exception during create for unit: 1fcb2fca-3841-4c98-bcd8-0da78815cfd2 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: M
ethod failed, data: message: External error in the NED implementation for device max-data-sw: Tue Jul  2 18:56:22.105 UTCrnrn Failed to commit one or more configuration items during a pseudo-atomic operation. All changes made have
 been reverted.rn  SEMANTIC ERRORS: This configuration was rejected by rn the system due to semantic errors. The individual rn errors with each failed configuration command can be rn found below.rnrnrninterface HundredGigE0/0/0/22
rn monitor-session mon_MAX_MAX_node1_pm-1fcb2fca-3841-4c98-bcd8-0da78815cfd2 ethernet port-levelrn SPAN detected the warning condition This platform doesnt support configuring multiple attachments of a traffic classrn rnrnend, int
ernal: jsonrpc_tx_commit357#all units failed priming: Exception during create for unit: 1fcb2fca-3841-4c98-bcd8-0da78815cfd2 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, mes
sage: Method failed, data: message: External error in the NED implementation for device max-data-sw: Tue Jul  2 18:56:22.105 UTCrnrn Failed to commit one or more configuration items during a pseudo-atomic operation. All changes ma
de have been reverted.rn  SEMANTIC ERRORS: This configuration was rejected by rn the system due to semantic errors. The individual rn errors with each failed configuration command can be rn found below.rnrnrninterface HundredGigE0
/0/0/22rn monitor-session mon_MAX_MAX_node1_pm-1fcb2fca-3841-4c98-bcd8-0da78815cfd2 ethernet port-levelrn SPAN detected the warning condition This platform doesnt support configuring multiple attachments of a traffic classrn rnrne
nd, internal: jsonrpc_tx_commit357#<br>
```
Fix: Ensure that the source/destination ports of all mirror links are globally unique. If there is a duplication, this error will be raised
```

7. Error when connecting to bastion host: Invalid key <br>
```
Fix: For the bastion host invalid key, you need to go your Jupyter environment and there is a file called 'configure_and_validate.ipynb' in the jupyter_examples folder(use the version 1.7.0). You need to run the notebook,
which will ckeck if your Bastion keys have expired and recreate another one if that is the case. You will then need to copy only the Bastion pub and priv keys to your local folder as mentioned in the
Twine documentation.
```

## Transient issues
The errors below are transient. Please **report these errors to us**, if you encounter them. <br>

1. Error when connecting to bastion host: Error reading SSH protocol banner
Traceback (most recent call last):
  File "/mnt/disk/nshyamkumar/fabric-jupyter/lib/python3.9/site-packages/paramiko/transport.py", line 2327, in _check_banner
    buf = self.packetizer.readline(timeout)
  File "/mnt/disk/nshyamkumar/fabric-jupyter/lib/python3.9/site-packages/paramiko/packet.py", line 381, in readline
    buf += self._read_timeout(timeout)
  File "/mnt/disk/nshyamkumar/fabric-jupyter/lib/python3.9/site-packages/paramiko/packet.py", line 618, in _read_timeout
    raise EOFError()
EOFError
<br>


2. failed lease update- all units failed priming: Exception during create for unit: 4b99e670-f7e7-406f-9b25-e99bbbf293f9 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: External error in the NED implementation for device max-data-sw: Tue Jul  2 19:09:36.967 UTCrnrn Failed to commit one or more configuration items during a pseudo-atomic operation. All changes made have been reverted.rn  SEMANTIC ERRORS: This configuration was rejected by rn the system due to semantic errors. The individual rn errors with each failed configuration command can be rn found below.rnrnrnmonitor-session mon_MAX_MAX_node2_pm-4b99e670-f7e7-406f-9b25-e99bbbf293f9 ethernetrn destination interface TwentyFiveGigE0/0/0/16/2rn Destination interface TwentyFiveGigE0/0/0/16/2 for session mon_MAX_MAX_node2_pm-4b99e670-f7e7-406f-9b25-e99bbbf293f9 is already configured for use with session mon_MAX_MAX_node0_pm-e80ed1e2-e96b-4724-885a-04c1a7173bc4rnrnend, internal: jsonrpc_tx_commit357#all units failed priming: Exception during create for unit: 4b99e670-f7e7-406f-9b25-e99bbbf293f9 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: External error in the NED implementation for device max-data-sw: Tue Jul  2 19:09:36.967 UTCrnrn Failed to commit one or more configuration items during a pseudo-atomic operation. All changes made have been reverted.rn  SEMANTIC ERRORS: This configuration was rejected by rn the system due to semantic errors. The individual rn errors with each failed configuration command can be rn found below.rnrnrnmonitor-session mon_MAX_MAX_node2_pm-4b99e670-f7e7-406f-9b25-e99bbbf293f9 ethernetrn destination interface TwentyFiveGigE0/0/0/16/2rn Destination interface TwentyFiveGigE0/0/0/16/2 for session mon_MAX_MAX_node2_pm-4b99e670-f7e7-406f-9b25-e99bbbf293f9 is already configured for use with session mon_MAX_MAX_node0_pm-e80ed1e2-e96b-4724-885a-04c1a7173bc4rnrnend, internal: jsonrpc_tx_commit357#
<br>


3. failed lease update- all units failed priming: Exception during create for unit: 0ee151cb-1f27-42df-90d1-1b1363c8d6ec Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: Network Element Driver: device cern-data-sw: out of sync, internal: jsonrpc_tx_commit357#all units failed priming: Exception during create for unit: 0ee151cb-1f27-42df-90d1-1b1363c8d6ec Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: Network Element Driver: device cern-data-sw: out of sync, internal: jsonrpc_tx_commit357#<br>

4. "Exception: Failed to submit modify slice: Status.FAILURE, (500)
Reason: INTERNAL SERVER ERROR
HTTP response headers: HTTPHeaderDict({'Server': 'nginx/1.21.6', 'Date': 'Mon, 22 Jul 2024 20:17:44 GMT', 'Content-Type': 'text/html; charset=utf-8', 'Content-Length': '225', 'Connection': 'keep-alive', 'Access-Control-Allow-Credentials': 'true', 'Access-Control-Allow-Headers': 'DNT, User-Agent, X-Requested-With, If-Modified-Since, Cache-Control, Content-Type, Range, Authorization', 'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS', 'Access-Control-Allow-Origin': '\*', 'Access-Control-Expose-Headers': 'Content-Length, Content-Range, X-Error', 'X-Error': ""'NoneType' object has no attribute 'reservation_id'""})
HTTP response body: b'{\n    ""errors"": [\n        {\n            ""details"": ""\'NoneType\' object has no attribute \'reservation_id\'"",\n            ""message"": ""Internal Server Error""\n        }\n    ],\n    ""size"": 1,\n    ""status"": 500,\n    ""type"": ""error""\n}'"<br>

5. AttributeError: 'NoneType' object has no attribute 'dumps' <br>


6. failed lease update- all units failed priming: Exception during create for unit: 544abf4e-c2ea-449a-bfe2-952b5f89c919 Playbook has failed tasks: NSO validate_commit returned JSON-RPC error: type: trans.validation_failed, code: -32000, message: Validation failed, data: errors: [reason: port-mirror-template.xml:141 Expression /from-interface/id resulted in an incompatible value 0/0/0/21.3000 for /ncs:devices/deviceucsd-data-sw/config/cisco-ios-xr:interface/HundredGigE/id]#all units failed priming: Exception during create for unit: 544abf4e-c2ea-449a-bfe2-952b5f89c919 Playbook has failed tasks: NSO validate_commit returned JSON-RPC error: type: trans.validation_failed, code: -32000, message: Validation failed, data: errors: [reason: port-mirror-template.xml:141 Expression /from-interface/id resulted in an incompatible value 0/0/0/21.3000 for /ncs:devices/deviceucsd-data-sw/config/cisco-ios-xr:interface/HundredGigE/id]# <br>

7. failed lease update- all units failed priming: Exception during create for unit: 2edd026d-72fe-4091-bb97-bfe00f7d6beb Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: Failed to connect to device newy-data-sw: connection refused: NEDCOM CONNECT: Connect timed out in new state, internal: jsonrpc_tx_commit395#all units failed priming: Exception during create for unit: 2edd026d-72fe-4091-bb97-bfe00f7d6beb Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: Failed to connect to device newy-data-sw: connection refused: NEDCOM CONNECT: Connect timed out in new state, internal: jsonrpc_tx_commit395# <br>

8. failed lease update- all units failed priming: Exception during create for unit: bf8333c2-ba28-442e-812a-41a9aa72f405 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: External error in the NED implementation for device brist-data-sw: read timeout after 20 seconds when waiting for Qshow running-configE, internal: jsonrpc_tx_commit395#all units failed priming: Exception during create for unit: bf8333c2-ba28-442e-812a-41a9aa72f405 Playbook has failed tasks: NSO commit returned JSON-RPC error: type: rpc.method.failed, code: -32000, message: Method failed, data: message: External error in the NED implementation for device brist-data-sw: read timeout after 20 seconds when waiting for Qshow running-configE, internal: jsonrpc_tx_commit395# <br>

9. paramiko.ssh_exception.ChannelException: ChannelException(2, 'Connect failed') <br>


