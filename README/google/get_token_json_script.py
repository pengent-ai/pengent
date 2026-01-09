from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    'client_id.json',
    scopes=[
        'https://www.googleapis.com/auth/calendar', # Google Calendar API
        'https://www.googleapis.com/auth/presentations', # Google Slides API
        'https://www.googleapis.com/auth/gmail.send', # Gmail API
        'https://www.googleapis.com/auth/drive', # Google Drive API
        # 'https://www.googleapis.com/auth/drive.readonly', # 読み込みのみの場合
    ]
)
creds = flow.run_local_server(port=0)
with open('token.json', 'w') as token:
    token.write(creds.to_json())
