### ArubaAPI

Logs into the ArubaOS web UI and issues arbitrary CLI commands.


## Example

```python
import arubaapi
from pprint import pprint

connection = arubaapi.ArubaAPI(device, username, password)
data = connection.cli('show ap database local')

pprint(data)
```

will output

```
{'data': [None,
          'Flags: U = Unprovisioned; N = Duplicate name; G = No such group; L = Unlicensed',
          '       I = Inactive; D = Dirty or no config; E = Regulatory Domain Mismatch',
          '       X = Maintenance Mode; P = PPPoE AP; B = Built-in AP; s = LACP striping',
          '       R = Remote AP; R- = Remote AP requires Auth; C = Cellular RAP;',
          '       c = CERT-based RAP; 1 = 802.1x authenticated AP; 2 = Using IKE version 2',
          '       u = Custom-Cert RAP; S = Standby-mode AP; J = USB cert at AP',
          '       i = Indoor; o = Outdoor',
          '       M = Mesh node; Y = Mesh Recovery',
          None,
          ('Total APs', '2')],
 'table': [['AP Database', '', '', '', '', '', '', ''],
           ['Name',
            'Group',
            'AP Type',
            'IP Address',
            'Status',
            'Flags',
            'Switch IP',
            'Standby IP'],
           ['AP Name 1',
            'AP Group 1',
            '135',
            '10.0.0.11',
            'Down',
            None,
            '10.0.0.10',
            '0.0.0.0'],
           ['AP Name 2',
            'AP Group 1',
            '225',
            '10.0.0.12',
            'Up 42d:19h:13m:26s',
            None,
            '10.0.0.10',
            '0.0.0.0']]}
```


