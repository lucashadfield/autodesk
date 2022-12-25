import datetime
import os
import pickle
from pathlib import Path
import yaml

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
            or (end_time - start_time).total_seconds() <= max_meeting_standing_time
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
    config_path = '~/.config/autodesk/config.yaml'
    with open(Path(config_path).expanduser(), 'r') as f:
        config = yaml.safe_load(f)

    # get calendar service
    service = get_service(Path(config['credentials_path']).expanduser(), Path(config['token_path']).expanduser())

    # get today's calendar events
    events = get_calendar_events(service, config['timezone'], config['calendar_id'])

    # work out when we should trigger based on those event times
    trigger_times = calculate_trigger_times(
        events,
        config['timezone'],
        config['end_threshold_seconds'],
        config['trigger_offset_seconds'],
        config['max_meeting_standing_time'],
    )

    # backup cron to file
    backup_cron(config['cron_backup_path'])

    # write new cron jobs
    append_cron_jobs(trigger_times, config['cron_backup_path'], config['cron_delimiter'], config['trigger_script'])

    # restore cron from file
    restore_cron(config['cron_backup_path'])


if __name__ == '__main__':
    main()
