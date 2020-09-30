# Meeting Alarm Tray

A simple tray icon that uses desktop notification via DBUS to inform about upcoming meeting by watching an ICS file or URL.

The notification allows to directly jump into the meeting by searching for an URL (`http` or `https`) in either summary, description or location of the event. On activation of the jump-in button, the URL is opened via `xdg-open` which should open your default browser. If no such an URL is found, then a default URL is used.

## Usage

```
usage: meetingalaram [-h] [--calendar-file CALENDAR_FILE] [--calendar-url CALENDAR_URL] [--disable-alarm] [--default-url DEFAULT_URL] [--verbose]

Meeting Alarm

optional arguments:
  -h, --help            show this help message and exit
  --calendar-file CALENDAR_FILE
                        set a calendar file (default: None)
  --calendar-url CALENDAR_URL
                        set a calendar url (default: None)
  --disable-alarm       disable alarm
  --default-url DEFAULT_URL
                        url to open if event does not contain an url
  --verbose             be verbose
```

## ChangeLog

### Next Version

### Version 0.0.1

- initial package
