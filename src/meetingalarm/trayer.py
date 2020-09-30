#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: trayer.py
Github: https://github.com/eikemoe/meetingalarm
Description: Meeting Alarm Trayer
"""

from __future__ import print_function

import subprocess
import logging
from datetime import timedelta
import re
import os
import time
import argparse

import dbus
from PyQt5 import QtGui, QtWidgets, QtCore

from icalevents import icalevents, icalparser
import notify2

import meetingalarm.resources.images

_LOGGER = logging.getLogger(__name__)

MAX_WAIT_FOR_TRAY_SECONDS = 10

## XXX monkey patching icalevents

def event_ended(event):
    """ returns whether the event has already ended """
    return event.end < icalparser.now()

def event_soon(event):
    """ returns whether the event starts soon (within next 12 hours) """
    return timedelta(hours=0) < event.time_left() < timedelta(hours=12)

def event_very_soon(event):
    """ returns whether the event starts very soon (within next 10 minutes) """
    return timedelta(hours=0) < event.time_left() < timedelta(minutes=10)

def event_running(event):
    """ returns whether the event is running """
    return event.end > icalparser.now() > event.start

icalparser.Event.ended = event_ended
icalparser.Event.soon = event_soon
icalparser.Event.very_soon = event_very_soon
icalparser.Event.running = event_running

del event_ended, event_soon, event_very_soon, event_running

class Calendar(object):

    def __init__(self, url=None, file=None, default_url=None):
        """ initialize the Calendar with the given url or file """
        self._calurl = url
        self._calfile = file
        self._default_url = default_url
        self._ignore = list()

    def get_upcoming_events(self, very_soon=False):
        """ returns a list of upcoming events """
        events = icalevents.events(url=self._calurl, file=self._calfile, fix_apple=True)

        ## XXX filter all day events here as icalparser compares offset-naive
        ##     and offset-aware datetimes otherwise
        events = filter(lambda e: not e.all_day, events)

        def keep(event):
            """ removes all_day, ended, and far events """
            if very_soon:
                return (
                    not event.ended() and
                    event.very_soon() and
                    event.uid not in self._ignore
                )
            return (
                not event.ended() and
                event.soon() and
                event.uid not in self._ignore
            )

        events = list(filter(keep, events))

        ## sort by start
        events.sort()

        return list(events)

    def get_event_by_uid(self, uid):
        """ returns the event for the given uid or None """
        events = icalevents.events(url=self._calurl, file=self._calfile, fix_apple=True)

        for event in events:
            if event.uid == uid:
                return event
        return None

    def ignore_event(self, uid):
        """ ignore events with the given uid """
        self._ignore.append(uid)

    def open_event(self, uid):
        """ use xdg-open to open the event (tries to extrat an http-url from
        location, description or summary falls back to the default url """
        event = self.get_event_by_uid(uid)

        url = None

        if event.location and 'http' in event.location:
            res = re.split(r"^.*(http(s)?://[^ ]*).*$", event.location)
            if res and len(res) > 1:
                url = res[1]

        if not url and event.description and 'http' in event.description:
            res = re.split(r"^.*(http(s)?://[^ ]*).*$", event.description)
            if res and len(res) > 1:
                url = res[1]

        if not url and event.summary and 'http' in event.summary:
            res = re.split(r"^.*(http(s)?://[^ ]*).*$", event.summary)
            if res and len(res) > 1:
                url = res[1]

        if not url:
            url = self._default_url

        subprocess.call(["xdg-open", url])

class TrayIcon(QtWidgets.QSystemTrayIcon):

    SHOW_REPORTS = True
    CHECK_TRACKING = False
    CHECK_ACTIVITY = True

    exit_clicked = QtCore.pyqtSignal()

    def __init__(self, calendar, parent=None):
        QtWidgets.QSystemTrayIcon.__init__(self, parent=parent)

        self.calendar = calendar

        # create the icon
        icon = "/usr/share/icons/Adwaita/96x96/status/alarm-symbolic.symbolic.png"
        self._icon = QtGui.QIcon(icon)

        # create the tray icon
        self.setIcon(self._icon)
        self.setVisible(True)

        # create the menu for tray icon
        self._menu = QtWidgets.QMenu()

        # add items to menu 
        self._calendar_action = QtWidgets.QAction("Open Calendar")
        self._menu.addAction(self._calendar_action)
        self._calendar_action.triggered.connect(self.open_calendar)

        self._menu.addSeparator()

        self.show_report = self.SHOW_REPORTS
        self._report_action = QtWidgets.QAction("notify on upcoming meetings",
                                                checkable=True)
        self._menu.addAction(self._report_action)
        self._report_action.setChecked(self.show_report)
        self._report_action.triggered.connect(self.toggle_show_report)

        self._menu.addSeparator()

        # add exit item to menu
        self._exitAction = QtWidgets.QAction("&Exit")
        self._menu.addAction(self._exitAction)
        self._exitAction.triggered.connect(self.exit_clicked)

        # add the menu to the tray
        self.setContextMenu(self._menu)

        self._update_tool_tip()

        def click_action(signal):
            if signal == 3:
                #self._hamster.open_hamster()
                pass

        self.activated.connect(click_action)

    def open_calendar(self):
        print("should open calendar")

    def _update_tool_tip(self):
        events = self.calendar.get_upcoming_events()
        if events and len(events) > 0:
            self.setToolTip("""\
            <html>
             <div style="width: 300px;">
              <nobr><b>Upcoming meetings:</b></nobr>
              <br>
              <nobr>{0}</nobr>
             </div>
            </html>""".format(
                "<br>\n".join([str(event) for event in events])
            ))
        else:
            self.setToolTip("""\
            <html>
             <div style="width: 300px;">
              <nobr><b>Upcoming meetings:</b></nobr>
              <br>
              No Meetings
             </div>
            </html>"""
            )

    def toggle_show_report(self, state):
        """ toggle whether reports will be shown """
        self.show_report = state


class MeetingAlarmTrayApp(QtWidgets.QApplication):

    REPORT_INTERVAL = 30 * 1000

    def __init__(self, calendar_file=None, calendar_url=None,
                 default_url=None, args=None):
        if args is None:
            args = list()
        QtWidgets.QApplication.__init__(self, args)
        self.setQuitOnLastWindowClosed(False)

        self.setStyleSheet("""\
        QToolTip {
            white-space: nowrap;
            color: #ffffff;
            background-color: #000000;
            border: 10px solid black;
        }""")

        self.calendar = Calendar(
            url = calendar_url,
            file = calendar_file,
            default_url = default_url,
        )

        ## setup notifier
        notify2.init("Meeting Alaram Notifier", mainloop='glib')

        self.notify_capabilities = notify2.get_server_caps()

        # icon = QtGui.QIcon(":/img/taskwarrior.ico")
        icon = "/usr/share/icons/Adwaita/scalable/status/alarm-symbolic.svg"
        self.notification = notify2.Notification("inactive", icon=icon)
        self.notification.set_urgency(notify2.URGENCY_NORMAL)

        ## setup report timer
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.do_report)

        ## setup tray icon
        self._tray = TrayIcon(self.calendar, parent=self)
        self._tray.exit_clicked.connect(self.quit)

        self._in_dialog = False

    def exec_(self):
        self._timer.start(self.REPORT_INTERVAL)
        super().exec_()
        self._timer.stop()

    def report_action_cb(self, n, action, user_data=None):
        if action == "dismiss":
            _LOGGER.info("ignoring event with uid %s", user_data)
            self.calendar.ignore_event(user_data)
        elif action == "open":
            _LOGGER.info("jumping to event with uid %s", user_data)
            self.calendar.open_event(user_data)

    def do_report(self):
        """ function called periodically to generate a report """

        self._tray._update_tool_tip()

        if not self._tray.show_report:
            return

        events = self.calendar.get_upcoming_events(very_soon=True)

        if not events or len(events) == 0:
            return

        event = events[0]

        if not event:
            return

        n = self.notification
        minutes = event.time_left().seconds / 60
        n.update(
            "You have a meeting in {:.1f} minutes.".format(minutes),
            "{} starts {} at {}.".format(
                event.summary,
                event.start.strftime("%H:%M"),
                event.location
            ))
        n.actions.clear()
        if 'actions' in self.notify_capabilities:
            n.add_action("open", "Jump into Meeting",
                         self.report_action_cb, user_data=event.uid)
            n.add_action("dismiss", "Dismiss",
                         self.report_action_cb, user_data=event.uid)
        n.show()


def main():
    ## init logger
    logformatter = logging.Formatter('%(asctime)s [%(levelname)-5.5s] %(message)s')
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(logformatter)
    consolehandler.setLevel("WARN")
    logging.getLogger().addHandler(consolehandler)

    ## parse args
    parser = argparse.ArgumentParser(description="Meeting Alarm")
    parser.add_argument('--calendar-file', type=str, default=None,
                        help='set a calendar file (default: None)')
    parser.add_argument('--calendar-url', type=str, default=None,
                        help='set a calendar url (default: None)')
    parser.add_argument('--disable-alarm', action='store_true',
                        help='disable alarm')
    parser.add_argument('--default-url', type=str, default=None,
                        help='url to open if event does not contain an url')
    parser.add_argument('--verbose', action='store_true',
                        help='be verbose')

    ## parse arguments
    args = parser.parse_args()

    if args.verbose:
        consolehandler.setLevel("DEBUG")
        logging.getLogger().setLevel("DEBUG")

    # create the application
    app = MeetingAlarmTrayApp(
        calendar_file = args.calendar_file,
        calendar_url = args.calendar_url,
        default_url = args.default_url,
    )

    loop_start = time.time()
    while not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
        if time.time() - loop_start > MAX_WAIT_FOR_TRAY_SECONDS: # wait max 5 seconds
            print("Could not find system tray")
            return
        time.sleep(0.1)
    del loop_start

    # run the application
    app.exec_()
