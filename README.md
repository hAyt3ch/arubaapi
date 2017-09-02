## ArubaAPI

Logs into the web UI of an Aruba Controller and issues arbitrary CLI show commands.  This was created to alleviate the pain of screen-scraping ArubaOS output, especially tables.

The HTTP API used is the one that the web GUI uses to gather data.  It's not terribly consistent and probably isn't guaranteed between AOS versions.  Submit an issue or pull request if you see issues with the data you're receiving.

There are three types of data output from the HTTP API:
 * Table data
 * Named data - Generally a key-value pair but not always.  In the case of duplicate names, the value is a list of all values seen.
 * Anonymous data - Auxiallary data output.  Generally unstructured lines like flag legends.

Config commands appear to be able to be sent through this same interface one at a time.  You will receive no data back from performing a config command, but it's important to note that an invalid command will also receive no data back.  It's probably a good idea to double-check that the config change stayed with a subsequent show command.

### Notes
 * It really doesn't like `show running-config`.  It will just hang and return no data.
 * Sessions will not be deleted unless `close()` is called or the `with` statement is used.
 * Invalid commands return an HTTP 200 with no data, so there's currently no way to detect them.

### Example

```python
import arubaapi
from pprint import pprint

connection = arubaapi.ArubaAPI('aruba-master.example.com', 'username', 'password')
data = connection.cli('show ap database local')
connection.close()

pprint(data, 120)
```

Output:

```
{'data': ['Flags: U = Unprovisioned; N = Duplicate name; G = No such group; L = Unlicensed',
          '       I = Inactive; D = Dirty or no config; E = Regulatory Domain Mismatch',
          '       X = Maintenance Mode; P = PPPoE AP; B = Built-in AP; s = LACP striping',
          '       R = Remote AP; R- = Remote AP requires Auth; C = Cellular RAP;',
          '       c = CERT-based RAP; 1 = 802.1x authenticated AP; 2 = Using IKE version 2',
          '       u = Custom-Cert RAP; S = Standby-mode AP; J = USB cert at AP',
          '       i = Indoor; o = Outdoor',
          '       M = Mesh node; Y = Mesh Recovery'],
 'namedData': {'Total APs': '2'},
 'tables': {'AP Database': [{'AP Type': '135',
                             'Flags': None,
                             'Group': 'AP Group 1',
                             'IP Address': '10.0.0.12',
                             'Name': 'AP 1',
                             'Standby IP': '0.0.0.0',
                             'Status': 'Down',
                             'Switch IP': '10.0.0.10'},
                            {'AP Type': '277',
                             'Flags': None,
                             'Group': 'AP Group 1',
                             'IP Address': '10.0.0.99',
                             'Name': 'AP 2',
                             'Standby IP': '0.0.0.0',
                             'Status': 'Up 43d:0h:23m:54s',
                             'Switch IP': '10.0.0.10'}]}}
```
