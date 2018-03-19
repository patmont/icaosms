import icaosms as icao
import time

notifier = icao.Notifier()
while True:
    starttime = time.time()

    notifier.get_flights(best_position=True)
    parsed_data = notifier.parse_flights()
    if len(parsed_data) > 0:
        notifier.email_notify()
        print('Sent Notification!')
    else:
        print('Nothing to notify!')
    time.sleep(30.0 - ((time.time() - starttime) % 30.0))
