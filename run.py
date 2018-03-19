# Command line execution handling
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("lat", help="Center latitude")
    parser.add_argument("lng", help="Center longitude")
    parser.add_argument("radius", help="Radius in meters")
    parser.add_argument("telto", help="Phone to, like +15555555555")
    parser.add_argument("telfrom", help="Phone from: twilio phone number")
    args = parser.parse_args()

    url = ('http://your-server/VirtualRadar/AircraftList.json?'
           'lat={lat}&lng={lng}&fDstL=0&fDstU={radius}'.format(lat=args.lat, lng=args.lng, radius=args.radius))

    icao_notify(args.telto, args.telfrom)
