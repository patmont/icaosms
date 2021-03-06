#!/usr/bin/env python
"""Retrieves all aircraft for a defined radius around a defined coordinate. Parses the list
for flags 'Interested', 'Mil', and custom Icao identifier. Sends an email notification when conditions
are met.

Requirements:
    configparser

Copyright:
    notifier.py Copyright 2017, Patrick Montalbano

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
from urllib.request import build_opener, HTTPCookieProcessor, urlopen
from http.cookiejar import CookieJar
import json
import time, datetime
import http
import smtplib
from email.mime.text import MIMEText
import configparser
import csv
from os.path import exists


class Notifier:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')

        self.url = self.config['VRS']['url']
        self.refresh_time = self.config['TIMING']['refresh_time']
        self.flags = self.config['VRS']['flags']
        with open('watchlist.csv', 'r') as f:
            r = csv.reader(f)
            self.watchlist = list(r)
        with open('blacklist.csv', 'r') as f:
            r = csv.reader(f)
            self.blacklist = list(r)
        self.timeout_time = int(self.config['TIMING']['timeout'])
        self.smtp_ssl_host = self.config['MAIL']['server']
        self.smtp_ssl_port = self.config['MAIL']['port']
        self.mailto = self.config['MAIL']['to']
        self.mailfrom = self.config['MAIL']['from']
        self.mail_auth = self.config['MAIL']['auth']
        self.buffer = {}
        self.data = {}
        self.parsed_data = {}

    def best_position(self):
        """ACARS vs MLAT position is reported differently in VRS; unify values under a new key.
            References:
            https://www.adsbexchange.com/data/
            http://www.virtualradarserver.co.uk/Documentation/Formats/AircraftList.aspx
        """
        data = self.data

        for idx, plane in enumerate(self.data['acList']):
            latitude = None
            longitude = None
            altitude = None
            timestamp = None
            speed = None

            # Use short trails if available
            if 'Cos' in plane:
                try:
                    l = int(len(plane['Cos']) / 4)
                    for i in range(0, l):
                        latitude = plane['Cos'][0::4][i]
                        longitude = plane['Cos'][1::4][i]
                        timestamp = datetime.datetime.fromtimestamp(plane['Cos'][2::4][i] / 1000)
                        if plane['TT'] == 'a':
                            altitude = plane['Cos'][3::4][i]
                        elif plane['TT'] == 's':
                            speed = plane['Cos'][3::4][i]
                        else:
                            pass
                except:
                    pass

            # Use Lat Long if available
            else:
                try:
                    latitude = plane['Lat']
                    longitude = plane['Long']
                    altitude = plane['alt']
                    timestamp = plane['PosTime']

                except:
                    pass

            # Append best position to data
            self.data['acList'][idx].update({'latitude': latitude,
                                             'longitude': longitude,
                                             'altitude': altitude,
                                             'timestamp': timestamp,
                                             'speed': speed
                                            })

    def get_flights(self, best_position=True):
        self.data = {}
        for i in range(0,10):
            while True:
                try:
                    cj = CookieJar()
                    opener = build_opener(HTTPCookieProcessor(cj))
                    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                    response = opener.open(self.url)
                    str_response = response.read().decode('utf-8')
                    self.data = json.loads(str_response)
                    if best_position:
                        Notifier.best_position(self)

                except:
                    time.sleep(30)
                    continue
                break

        return self.data

    def parse_flights(self):
        self.parsed_data = {}         # Initiate and clear message every loop
        for idx, plane in enumerate(self.data['acList']):
            try:
                icao = plane['Icao']
            except KeyError:
                continue

            # Add or update plane to buffer
            if icao not in self.buffer:
                self.buffer[icao] = {'firstseen': time.time(),'notified': False}

            # Skip planes already notified
            if 'notified' in self.buffer[icao]\
                    and self.buffer[icao]['notified'] == True:
                continue    # Return to top of for loop and increment

            # Parse conditions
            #TODO: consider checking all keys for any blacklist value
            if any(icao not in x for x in self.blacklist)\
                    and any(plane['Type'] not in x for x in self.blacklist)\
                    and plane['Mil'] is True and 'Mil' in self.flags\
                    or plane['Interested'] is True and 'Interested' in self.flags\
                    or any(icao in x for x in self.watchlist):
                self.parsed_data[icao] = plane

            # Remove flight from buffer after timeout
            for plane in list(self.buffer):
                if time.time() - self.buffer[plane]['firstseen'] >= self.timeout_time:
                    self.buffer.pop(plane, None)

        return self.parsed_data

    def email_notify(self, subject="Flight Notification"):
        server = smtplib.SMTP_SSL(self.smtp_ssl_host, self.smtp_ssl_port, timeout=5)
        server.login(self.mailfrom, self.mail_auth)

        for plane in self.parsed_data:
            self.buffer[plane]['notified'] = True

        msg = MIMEText(str(self.parsed_data))
        msg['Subject'] = subject
        msg['From'] = self.mailfrom
        msg['To'] = self.mailto
        server.sendmail(self.mailfrom, self.mailto, msg.as_string())
        server.quit()

    def plane_image(self, icao):
        """
        http://www.airport-data.com/api/doc.php
        :return: (str) relative filepath to image
        """
        # Search for saved plane image
        if exists('/images/planes/{}.jpg'.format(icao)) is False:
            # Get image from airport-data
            url = "http://www.airport-data.com/api/ac_thumb.json?m={}&n=N".format(icao)
            while True:
                try:
                    cj = CookieJar()
                    opener = build_opener(HTTPCookieProcessor(cj))
                    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
                    response = opener.open(url)
                    str_response = response.read().decode('utf-8')
                    image_data = json.loads(str_response)
                    thumb_url = image_data['data'][0]['image']
                    f = open('images/planes/{}.jpg'.format(icao), 'wb')
                    f.write(urlopen(thumb_url).read())
                    f.close()
                except:
                    icao = "unavailable"
                break
        return '/images/planes/{}.jpg'.format(icao)

if __name__ == "__main__":
    notifier = Notifier()
    config = configparser.ConfigParser()
    config.read('config.ini')

    while True:
        # Initialize
        starttime = time.time()
        notifier.get_flights(best_position=True)
        parsed_data = notifier.parse_flights()

        # Save image to directory
        for plane in parsed_data:
            notifier.plane_image(plane)
        # Send notification
        if len(parsed_data) > 0:
            notifier.email_notify()
            print('Sent Notification!')
        else:
            print('Nothing to notify!')
        refresh_time = float(config['TIMING']['refresh_time'])
        time.sleep(refresh_time - ((time.time() - starttime) % refresh_time))

