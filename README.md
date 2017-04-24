# icaosms
Retrieves all aircraft for a defined radius around a defined coordinate.
Parses the list for flags 'Interested', 'Mil', and custom Icao identifier.
Sends an SMS notification when conditions are met.

## Requirements:
python 3 environment

[Twilio](https://github.com/twilio/twilio-python)

## Usage:
Install twilio from instructions [here](https://github.com/twilio/twilio-python)
or
```
pip install twilio
```

Create a twilio account and retrieve your 34 digit account SID and 32 digit AUTH token
under account summary. Add these to line 58:
```
  client = TwilioRestClient("your-34-character-key", "your-32-character-key")
```
Add any watch identifiers to like 160 using comma separation.
```
watchlist = [] # Enter your 6 digit call sign [here] for alerts
```

Run icaosms.py in terminal passing args:
```
python3 icaosms.py [dec_latitude] [dec_longitude] [radius_km] [+destinationphone] [+twilionumber]
```
