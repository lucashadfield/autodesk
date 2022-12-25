import datetime
import os
import pickle
from pathlib import Path

import pytz
from dateutil.parser import parse
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.events.readonly']


def get_service(credentials_path: Path, token_path: Path):
    credentials = None
    if token_path.exists():
        with token_path.open('rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            credentials = flow.run_local_server(port=0)
        with token_path.open('wb') as token:
            pickle.dump(credentials, token)

    return build('calendar', 'v3', credentials=credentials)


def get_calendar_events(service, timezone: str, calendar_id: str):
    start_date = datetime.date.today()

    start = datetime.datetime.combine(start_date, datetime.time(0), pytz.timezone(timezone)).astimezone(pytz.UTC)
    end = start + datetime.timedelta(days=1)

    time_min = start.replace(tzinfo=None).isoformat() + 'Z'
    time_max = end.replace(tzinfo=None).isoformat() + 'Z'

    return (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
        )
        .execute()
    )


def calculate_trigger_times(
    events: dict, timezone: str, end_threshold_seconds: int, trigger_offset_seconds: int, max_meeting_standing_time: int
):
    trigger_times = []
    prev_end_time = None
    for event in events['items']:
        start_time = parse(event['start']['dateTime'])
        end_time = parse(event['end']['dateTime'])
        if (
            prev_end_time is None
            or (start_time - prev_end_time).total_seconds() >= end_threshold_seconds
            or (end_time - start_time) <= max_meeting_standing_time
        ):
            trigger_times.append(
                start_time.astimezone(pytz.timezone(timezone)) - datetime.timedelta(seconds=trigger_offset_seconds)
            )
        prev_end_time = parse(event['end']['dateTime'])
    return trigger_times


def backup_cron(cron_backup_path: str):
    os.system(f'crontab -l > {cron_backup_path}')


def restore_cron(cron_backup_path: str):
    os.system(f'crontab {cron_backup_path}')


def datetime_to_cron(dt: datetime.datetime):
    return f'{dt.minute} {dt.hour} {dt.day} {dt.month} {dt.isoweekday()}'


def append_cron_jobs(trigger_times, cron_backup_path, cron_delimiter, trigger_script):
    with open(cron_backup_path, 'r') as f:
        cron = f.readlines()
        for i, c in enumerate(cron):
            if c == cron_delimiter:
                break

    with open(cron_backup_path, 'w') as f:
        cron_append = cron[:i] + [cron_delimiter] + [f'{datetime_to_cron(t)} {trigger_script}\n' for t in trigger_times]
        f.writelines(cron_append)


def main():
    # config
    credentials_path = '~/.config/autodesk/client_secret.json'  # google api credentials
    token_path = '~/.config/autodesk/token.pickle'  # google api token
    timezone = 'Australia/Sydney'  # timezone of the machine running cron
    calendar_id = 'Calendar Name'  # name of the calendar to fetch (could be email address if it's a shared calendar)
    end_threshold_seconds = 600  # if previous meeting ends within 600 seconds of this one, don't raise
    max_meeting_standing_time = 3600  # don't raise if meeting is longer than this
    trigger_offset_seconds = 60  # how many seconds before the start of the meeting should the desk raise
    cron_delimiter = '# Desk Actions\n'  # replace everything below this line in cron with the updated jobs
    trigger_script = 'python /home/user/autodesk/trigger.py'  # cron command
    cron_backup_path = '/tmp/crontab.bak'  # where to backup cron file for editing

    # get calendar service
    service = get_service(Path(credentials_path).expanduser(), Path(token_path).expanduser())

    # get today's calendar events
    events = get_calendar_events(service, timezone, calendar_id)

    # work out when we should trigger based on those event times
    trigger_times = calculate_trigger_times(
        events, timezone, end_threshold_seconds, trigger_offset_seconds, max_meeting_standing_time
    )

    # backup cron to file
    backup_cron(cron_backup_path)

    # write new cron jobs
    append_cron_jobs(trigger_times, cron_backup_path, cron_delimiter, trigger_script)

    # restore cron from file
    restore_cron(cron_backup_path)


if __name__ == '__main__':
    main()
