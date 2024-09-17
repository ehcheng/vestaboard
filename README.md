# vestaboard
## Vestaboard Calendar and News Updater

This project automates the process of fetching calendar events from an ics file and news headlines, generating a poem, and updating a Vestaboard display.

## Components

- `extractEvents.py`: Processes iCalendar files and extracts relevant events, including expanding recurring events
- `updateVestaBoard.py`: Sends formatted text to the Vestaboard display
- `newsPoem.py`: Fetches news headlines and generates a poem

## Sample scripts

- `runUpdateVestaboard.sh`: Main script to fetch calendar events and update Vestaboard
- `runNews.sh`: Generates a news poem and updates Vestaboard

## Setup

1. Install required Python packages (may be incomplete):
   ```
   pip install ics icalendar recurring_ical_events pytz openai python-dotenv feedparser beautifulsoup4 requests
   ```

2. Set up environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `VESTABOARD_READ_WRITE_KEY`: Your Vestaboard API key

3. Update file paths in the shell scripts to match your system.

## Configuration

- Adjust `DAYS_TO_INCLUDE` in `extractEvents.py` to change the event horizon
- Use extractEvents.py's optional argument "-d DATE" if you want to extract a date other than today's date
- Modify RSS feed URL in `newsPoem.py` to change news source

## Note

Ensure all scripts have execute permissions:
```
chmod +x runUpdateVestaboard.sh
chmod +x runNews.sh
```
## Disclaimer

This code is heavily AI assisted. I stopped working on the project when it started to work.
