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
2. edit config params in `main.py` -> `main()`
3. edit trigger Pin id in `trigger.py`
4. Run main.py, complete auth flow in browser
5. Move client_secrets.json and token.pickle to raspberry pi
6. Run `main.py` daily on cron
- it will append trigger times to the end of cron