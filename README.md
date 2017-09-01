## ArubaAPI

Logs into the ArubaOS web UI and issues arbitrary CLI commands.


### Example

```python
import arubaapi
from pprint import pprint

connection = arubaapi.ArubaAPI('aruba-master.example.com', 'username', 'password')
data = connection.cli('show ap database local')
connection.close()

pprint(data, 120)
```

will output

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
 'table': [{'AP Type': '135',
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
            'Status': 'Up 42d:22h:16m:41s',
            'Switch IP': '10.0.0.10'}]}
```

Also supports the `with` statement.

```python
import arubaapi
from pprint import pprint

with arubaapi.ArubaAPI('aruba-master.example.com', 'username', 'password') as connection:
	data = connection.cli('show ap database local')
```
