"""
extractEvents.py

This script processes iCalendar (.ics) files to extract and analyze event data.
It uses various libraries to handle calendar operations, time zones, and
recurring events. The script also integrates with OpenAI's GPT model for
advanced event processing.

Key Features:
- Extracts events from multiple iCalendar files
- Handles recurring events
- Processes events within a specified time range
- Integrates with OpenAI's GPT model for event analysis
- Supports custom time zones

Dependencies:
- ics: For basic iCalendar operations
- icalendar: For more advanced iCalendar parsing
- recurring_ical_events: To handle recurring events
- pytz: For timezone operations
- openai: For integration with GPT models
- dotenv: For loading environment variables

Global Settings:
- DAYS_TO_INCLUDE: Number of days to include in event extraction (default: 1)
- DEBUG: Toggle for debug printing (default: True)
- GPT_MODEL: Specifies the GPT model to use (default: "gpt-4-turbo")
- ICSP_PATH: Path to the icsp binary

Usage:
This script is typically run as part of a larger system for calendar event
processing and analysis. It can be imported as a module or run directly,
depending on the implementation details of the broader system.

Note: Ensure that all required environment variables (e.g., OPENAI_API_KEY, ICSP_PATH)
are properly set before running the script.
"""


import sys
import subprocess
import os
from ics import Calendar, Event
from datetime import datetime, timedelta, date, time
import pytz
import recurring_ical_events
import icalendar
import signal
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Define the path to the icsp binary
ICSP_PATH = "/Users/echeng/.local/bin/icsp"  # Adjust this path as needed

# Global variables
DAYS_TO_INCLUDE = 1  # 0 = only the provided day. Adjust this value as needed
DEBUG = True  # Set this to False to turn off debug printing

# Add this near the top of the file, after the openai import
GPT_MODEL = "gpt-4-turbo"

def timeout_handler(signum, frame):
    raise TimeoutError("Event processing timed out")

def extract_recurring_events_ics(ical_file_paths, target_timezone='America/Los_Angeles'):
    if DEBUG:
        print(f"Starting extraction from {len(ical_file_paths)} files with target timezone {target_timezone}", flush=True)

    # Use a default timezone if an empty string is provided
    if not target_timezone:
        target_timezone = 'America/Los_Angeles'  # or any other default timezone you prefer

    all_events = []

    for ical_file_path in ical_file_paths:
        with open(ical_file_path, 'r') as file:
            calendar_data = file.read()

        # Parse the calendar using icalendar
        cal = icalendar.Calendar.from_ical(calendar_data)

        # Get the current date
        current_date = datetime.now(pytz.timezone(target_timezone)).date()
        end_date = current_date + timedelta(days=DAYS_TO_INCLUDE)

        if DEBUG:
            print(f"Parsed calendar data. Current date: {current_date}, End date: {end_date}", flush=True)

        # Set a timeout for event processing
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(5)  # 5 seconds timeout

        try:
            query = recurring_ical_events.of(cal).after(current_date)

            if DEBUG:
                print(f"Retrieved events after {current_date}", flush=True)

            filtered_events = []

            for event in query:
                if DEBUG:
                    print(f"Processing event: {event.get('SUMMARY', 'No Title')}", flush=True)

                start_time = event['DTSTART'].dt
                end_time = event['DTEND'].dt if 'DTEND' in event else start_time

                if DEBUG:
                    print(f"  Original start time: {start_time}, end time: {end_time}", flush=True)

                # Convert to target timezone if necessary
                if isinstance(start_time, datetime):
                    start_time = start_time.astimezone(pytz.timezone(target_timezone))
                    end_time = end_time.astimezone(pytz.timezone(target_timezone))
                    if DEBUG:
                        print(f"  Converted to target timezone. New start time: {start_time}, end time: {end_time}", flush=True)

                # Handle all-day events (date objects) and datetime objects
                if isinstance(start_time, (date, time)) and not isinstance(start_time, datetime):
                    start_time = datetime.combine(start_time, time.min)
                    start_time = start_time.replace(tzinfo=pytz.UTC)

                if isinstance(end_time, date) and not isinstance(end_time, datetime):
                    end_time = datetime.combine(end_time, time.max)
                    end_time = end_time.replace(tzinfo=pytz.UTC)

                # Stop if we've reached events beyond our end date
                if start_time.date() > end_date:
                    if DEBUG:
                        print(f"Reached event beyond end date. Stopping.", flush=True)
                    break

                filtered_events.append({
                    "title": event.get('SUMMARY', 'No Title'),
                    "location": event.get('LOCATION', ''),
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_recurring": 'RRULE' in event
                })

                if DEBUG:
                    print(f"Added event to filtered list: {event.get('SUMMARY', 'No Title')} - {start_time.date()}", flush=True)

        except TimeoutError:
            print(f"Warning: Event processing timed out for file {ical_file_path}. Skipping remaining events.", flush=True)
        except Exception as e:
            print(f"Error processing events from {ical_file_path}: {str(e)}", flush=True)
        finally:
            signal.alarm(0)  # Disable the alarm

        all_events.extend(filtered_events)

    if DEBUG:
        print(f"Finished processing. Total events filtered: {len(all_events)}", flush=True)

    return all_events

def filter_events_by_date(events, filter_date):
    if DEBUG:
        print(f"Filtering events for date: {filter_date}", flush=True)

    filter_date = datetime.strptime(filter_date, "%Y-%m-%d").date()
    filtered_events = []

    for event in events:
        event_date = event['start_time'].date()
        if event_date == filter_date:
            filtered_events.append(event)
            if DEBUG:
                print(f"Added event to filtered list: {event['title']} - {event_date}", flush=True)

    if DEBUG:
        print(f"Finished filtering. Total events for {filter_date}: {len(filtered_events)}", flush=True)

    return filtered_events

def summarize_with_gpt(title, max_length):
    if DEBUG:
        print(f"Attempting to summarize title: '{title}' with max length {max_length}", flush=True)
    try:
        if DEBUG:
            print(f"Sending request to {GPT_MODEL}", flush=True)
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": f"Summarize the following event title in {max_length} characters or less. "
                 "Use common abbreviations, make results as standalone readable as possible. Do not use any hashtags or other formatting. "
                 "shorten 'Peninsula Self Defense' to 'BJJ'. "
                 "Do not add words if they are already within max length "
                 "If names are included (including Mako and Kai), try hard not to omit."
                 },
                {"role": "user", "content": title}
            ],
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        if DEBUG:
            print(f"Received summary from {GPT_MODEL}: '{summary}'", flush=True)
        final_summary = summary[:max_length]
        if DEBUG:
            print(f"Final summary (truncated if necessary): '{final_summary}'", flush=True)
        return final_summary
    except Exception as e:
        if DEBUG:
            print(f"Error summarizing with {GPT_MODEL}: {e}", flush=True)
        return title[:max_length]

def format_events_for_text_file(events, filter_date):
    all_day_events = []
    timed_events = []
    for event in events:
        if event['start_time'].time() == time.min and event['end_time'].time() == time.max:
            # All-day event
            summary = summarize_with_gpt(event['title'], 22)
            all_day_events.append(summary)
        else:
            # Timed event
            start_time = event['start_time'].strftime("%H:%M")
            summary = summarize_with_gpt(event['title'], 16)
            timed_events.append(f"{start_time} {summary}")

    # Sort all-day events alphabetically
    all_day_events.sort()

    # Sort timed events by start time
    timed_events.sort()

    # Combine all-day events and timed events
    formatted_events = timed_events + all_day_events

    date_header = datetime.strptime(filter_date, "%Y-%m-%d").strftime("%B %d").upper()
    header = f"--- {date_header} ---\n"

    return header + "\n".join(formatted_events)

if __name__ == "__main__":
    if DEBUG:
        print("Script started", flush=True)

    import argparse

    parser = argparse.ArgumentParser(description="Process ICS files and extract events.")
    parser.add_argument("ics_files", nargs="+", help="Path(s) to ICS file(s)")
    parser.add_argument("-d", "--date", default=datetime.now().strftime("%Y-%m-%d"), 
                        help="Filter date in YYYY-MM-DD format (default: today)")
    parser.add_argument("-t", "--timezone", default="America/Los_Angeles", 
                        help="Target timezone (default: America/Los_Angeles)")
    parser.add_argument("-o", "--output", default=".", 
                        help="Output folder (default: current directory)")

    args = parser.parse_args()

    if DEBUG:
        print(f"Input parameters: ics_file_paths={args.ics_files}, filter_date={args.date}, "
              f"target_timezone={args.timezone}, output_folder={args.output}", flush=True)

    expanded_cal = extract_recurring_events_ics(args.ics_files, args.timezone)
    filtered_events = filter_events_by_date(expanded_cal, args.date)

    # Sort filtered events by start time
    filtered_events.sort(key=lambda x: x['start_time'])

    # Generate the new filename for the ICS file
    new_ics_filename = os.path.join(args.output, 'combined_expanded.ics')

    if DEBUG:
        print(f"Writing filtered events to {new_ics_filename}", flush=True)

    # Write the filtered events to the new ICS file
    cal = Calendar()
    for event in filtered_events:
        cal.events.add(
            Event(
                name=event['title'],
                begin=event['start_time'],
                end=event['end_time'],
                location=event['location']
            )
        )

    with open(new_ics_filename, 'w') as f:
        f.write(cal.serialize())

    print(f"Filtered calendar written to: {new_ics_filename}")

    # Generate the text file with formatted events
    text_filename = os.path.join(args.output, 'combined_events.txt')
    formatted_events = format_events_for_text_file(filtered_events, args.date)

    with open(text_filename, 'w') as f:
        f.write(formatted_events)

    print(f"Formatted events written to: {text_filename}")

    if DEBUG:
        print("Script completed successfully", flush=True)

# # Generate the base filename without extension
# new_filename_base = ics_file_path.rsplit('.', 1)[0] + '_expanded'

# # Call the icsp command and filter results
# # command = f"{ICSP_PATH} -c 'summary,dtstart,dtend,location' {new_filename} | grep '{filter_date}' > {new_filename_base}.tsv"
# command = f"{ICSP_PATH} -c 'summary,dtstart,dtend,location' {new_filename}' > {new_filename_base}.tsv"

# if DEBUG:
#     print(f"Executing command: {command}", flush=True)

# try:
#     subprocess.run(command, shell=True, check=True)
#     print(f"Filtered events written to: {new_filename_base}.tsv")
#     if DEBUG:
#         print("Script completed successfully", flush=True)
# except subprocess.CalledProcessError as e:
#     print(f"Error executing command: {e}")
#     if DEBUG:
#         print(f"Script failed with error: {e}", flush=True)