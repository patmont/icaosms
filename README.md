# icaosms
Retrieves all aircraft for a defined radius around a defined coordinate 
from Virtual Radar Server http json request.
Parses the list for flags 'Interested', 'Mil', and custom Icao identifier.
Sends an SMS notification when conditions are met.

## Requirements:
python 3 environment
configparser:  pip install configparser



## Usage:

Create config.ini file with the following:
```
[VRS]
url = http://adsbexchange.com/VirtualRadar/AircraftList.json?lat=0.00&lng=0.00&fDstL=0&fDstU=30
#flags may be Interested or Mil separated by comma
flags = Interested, Mil

[TIMING]
# Notification is to be sent on the first instance of the airplane entering
# the radius. The plane id enters a cooldown period before notification will
# be sent again.
timeout = 7200

# How often data will be refreshed
refresh_time = 240

[MAIL]
server=smtp.gmail.com
port=465
auth=*********
from=from@gmail.com
to=to@anywhere.com
```

Create watchlist.csv and blacklist.csv files.

Run email_notify.py in terminal passing args:
```
    python email_notify.py
```
