# AnythingGPT
The Python micro framework for building knowledge base powered ChatGPT assistants

# Install
```buildoutcfg
virtualenv -p python3.8 .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Collect data from discord (optional)
- First, open a discord channel in your browser and get the channel ID from the URL https://discord.com/channels/xxx/{CHANNEL_ID}
- Second, being on the discord channel page, start typing anything, then open developer tools -> Network -> Find "typing" -> Headers -> Authorization.
- Third, run the script with the obtained parameters
```buildoutcfg
source .venv/bin/activate
python  discord-channel-data-collection.py --channel_id=123456 --authorization_key="123456qwerty"
```

# Collect data from telegram chat (optional)
- First, create an app using https://my.telegram.org/apps and get app_id and app_hash
- Second, find a group name that you are going to use
- Third, run the script with the obtained parameters from your telegram user creds:
```buildoutcfg
source .venv/bin/activate
python telegram-group-data-collection.py --app_id=123456 --app_hash="123456qwerty" --phone_number="+xxxxxx" --password="qwerty123" --group_name="xxx" --limit_messages=100
```