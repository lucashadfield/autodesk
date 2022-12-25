# autodesk
#### Trigger standing desk based on calendar events

---
**Setup:**

1. set up google api
  - https://support.google.com/googleapi/answer/6158849?hl=en
  - Create Project
  - Library
    - Google Calendar API -> Enable
  - Credentials
    - OAuth client ID
    - Desktop Application
    - Save .json to ~/.config/autodesk/client_secrets.json
  - OAuth consent screen
    - Add user to "Test users"
2. copy `example_config.yaml` to `~/.config/autodesk/config.yaml` and update parameters
3. edit trigger Pin id in `trigger.py`
4. run main.py, complete auth flow in browser
5. move `client_secrets.json` and `token.pickle` to raspberry pi
6. run `main.py` daily on cron
  - it will append trigger times to the end of cron
  
**Example crontab after running main.py**
```
50 8 * * 1 python /home/pi/autodesk/main.py
50 8 * * 2 python /home/pi/autodesk/main.py
50 8 * * 3 python /home/pi/autodesk/main.py
50 8 * * 4 python /home/pi/autodesk/main.py
50 8 * * 5 python /home/pi/autodesk/main.py

# Desk Actions
29 10 10 9 6 python /home/pi/autodesk/trigger.py
59 13 10 9 6 python /home/pi/autodesk/trigger.py
```
