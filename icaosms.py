#!/usr/bin/env python
"""Retrieves all aircraft for a defined radius around a defined coordinate. Parses the list
for flags 'Interested', 'Mil', and custom Icao identifier. Sends an SMS notification when conditions
are met.

Usage:
    python3 icaosms.py [dec_latitude] [dec_longitude] [radius_km] [+destinationphone] [+twilionumber]

Requirements:
    twilio
    Modify for your API keys

Copyright:
    icaosms.py Copyright 2017, Patrick Montalbano

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
# TODO: Make watchlist, blacklist optional
import argparse


def icao_notify(telto, telfrom):
    """Sends SMS notification of interesting aircraft in geofence radius.
    
    Uses periodic Virtual Radar API request to retrieve all flights in a defined radius.
    Filters flights in range using flags and user defined watchlist.
    Sends an SMS message.
    
    Args:
        telto:
        telfrom:

    Usage:
        trFmt=sa, location trail;fCallQ=######, filter callsign
    References:
        https://www.adsbexchange.com/data/
        http://www.virtualradarserver.co.uk/Documentation/Formats/AircraftList.aspx
    """
    from urllib.request import Request, urlopen, build_opener, HTTPCookieProcessor
    from http.cookiejar import CookieJar
    import json
    from twilio.rest import TwilioRestClient
    import time
    import http

    # Twilio Account SID and Auth Token
    client = TwilioRestClient("your-34-character-key", "your-32-character-key")
    starttime = time.time()
    
    while True:
        message = []         # Initiate and clear message every loop

        try:
            cooldown
        except NameError:
            print('(re)initializing cooldown')
            # Initialize dictionary of all aircraft received indexed by Icao, each entry contains time first seen.
            # Index values are removed after expire time time has passed.
            # Dictionary grows as large as flights within the expire time.
            cooldown = {}

        # Seconds flight is not to be repeated for
        expire = 7200

        # Open url
        while True:
            try:
                cj = CookieJar()
                opener = build_opener(HTTPCookieProcessor(cj))
                opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                response = opener.open(url)
                str_response = response.read().decode('utf-8')
                data = json.loads(str_response)
            except (IOError, http.client.HTTPException) as e:
                    print(e)
            break

        # Remove from cooldown dict after t time
        for key in cooldown:
            if time.time()-cooldown[key] > expire:
                cooldown.pop(key, None)
                break

        # Parse flight response list
        for idx, plane in enumerate(data['acList']):       

            # Skip planes in cooldown
            if plane['Icao'] in cooldown:
                continue    # Return to top of for loop and increment

            # Interesting flag set
            if plane['Interested']:
                message.append(data['acList'][idx]['Icao'])
                try: 
                    message.append(plane['Op'])
                except Exception:
                    pass
            # Personal Watchlist
            if True in (x == plane['Icao'] for x in watchlist):
                message.append(plane['Icao'])
                try:
                    message.append(plane['Op'])
                except Exception:
                    pass
                try:
                    message.append(plane['Mdl'])
                except Exception:
                    pass
            # Mil flag
            if plane['Mil']:
                message.append(plane['Icao'])
                try:
                    message.append(plane['Op'])
                except Exception:
                    pass
                try:
                    message.append(plane['Mdl'])
                except Exception:
                    pass

            # If flight is not in cooldown list
            if plane['Icao'] not in cooldown:
                cooldown.update({plane['Icao']: time.time()})

        # Build message string
        string = ""
        if len(message) > 0:
            for item in message:
                string += item
                string += ", \n"
            print(string)

        # account to send SMS to any phone number
        if len(message) > 0:
            client.messages.create(to=telto, from_=telfrom, body=string)

        time.sleep(240.0 - ((time.time() - starttime) % 240.0))

# Command line execution handling
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("lat", help="Center latitude")
    parser.add_argument("lng", help="Center longitude")
    parser.add_argument("radius", help="Radius in meters")
    parser.add_argument("telto", help="Phone to, like +15555555555")
    parser.add_argument("telfrom", help="Phone from: twilio phone number")
    args = parser.parse_args()

    watchlist = [] # Enter your 6 digit call sign [here] for alerts
    url = ('http://public-api.adsbexchange.com/VirtualRadar/AircraftList.json?'
           'lat={lat}&lng={lng}&fDstL=0&fDstU={radius}'.format(lat=args.lat, lng=args.lng, radius=args.radius))

    icao_notify(args.telto, args.telfrom)
