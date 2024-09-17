#!/bin/bash

# get the ics files (e.g., Google Calendar's private URL for a calendar)
wget -O /path/to/calendar.ics https://foo.bar/basic.ics
wget -O /path/to/calendar2.ics https://foo.bar/basic2.ics

# extract events from multiple ics files and sort them
python /path/to/extractEvents.py -o /output/folder calendar.ics calendar2.ics

# update Vestaboard
python /path/to/updateVestaBoard.py /output/folder/combined_events.txt