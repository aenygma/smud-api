# SMUD API
---

An API to get usage and cost information from SMUD (Sacramento Municipal Utility District), an electricity provider for the Sacramento County.

SMUD didn't have a programmatic way to get usage and cost data for my account. I made this to get that information so I could monitor and run stats.

This project logs in, manages the SSO, parses the energy usage data and returns a list.

---
### Usage:

Here's code to login and get the cost for the day of March 14th 2019.

```
import api
sapi = api.SMUD_API()
sapi.login(username, password)

sapi.get("cost", "day", (2019, 3, 14)

[{'startDate': 'Thu, 20 Mar 2019 00:00:00',
  'endDate': 'Thu, 20 Mar 2019 00:59:59',
  'value': 0.11202064},
 {'startDate': 'Thu, 14 Mar 2019 01:00:00',
  'endDate': 'Thu, 14 Mar 2019 01:59:59',
  'value': 0.10421324},
 {'startDate': 'Thu, 14 Mar 2019 02:00:00',
 ...
 ]

```
---

### Types of queries:
* Usage data 
```
    # get usage for the day
    sapi.get("usage", "day", (2019, 3, 14))
    
    # get usage for the billing period of March 2019. Day is ignored
    sapi.get("usage", "bill", (2019, 3, ''))
    
    # get usage for year 2019. Month and Day is ignored
    sapi.get("usage", "year", (2019, '', ''))
```

* Cost data 
```
    # get cost for the day
    sapi.get("cost", "day", (2019, 3, 14))
    
    # get cost for the billing period of March 2019. Day is ignored
    sapi.get("cost", "bill", (2019, 3, ''))
    
    # get cost for year 2019. Month and Day is ignored
    sapi.get("cost", "year", (2019, '', ''))
```

---

### Dependencies
* requests
* BeautifulSoup

