import pandas as pd
import argparse
from telethon import TelegramClient

# Create an Argument Parser object
parser = argparse.ArgumentParser(description='Telegram Group Data Collection Script')

# Add the arguments
parser.add_argument('--app_id', type=int, help='Telegram APP id from https://my.telegram.org/apps')
parser.add_argument('--app_hash', type=str, help='Telegram APP hash from https://my.telegram.org/apps')
parser.add_argument('--phone_number', type=str, help='Telegram user phone number with the leading "+"')
parser.add_argument('--password', type=str, help='Telegram user password')
parser.add_argument('--group_name', type=str, help='Telegram group public name without "@"')
parser.add_argument('--limit_messages', type=int, help='Number of last messages to download')

# Parse the command-line arguments
args = parser.parse_args()

# Access the argument values
app_id = args.app_id
app_hash = args.app_hash
phone_number = args.phone_number
password = args.password
group_name = args.group_name
limit_messages = args.limit_messages


async def main():
    messages = await client.get_messages(group_name, limit=limit_messages)
    df = pd.DataFrame(columns=['date', 'user_id', 'raw_text', 'views', 'forwards', 'text', 'chan', 'id'])

    for m in messages:
        if m is not None:
            if 'from_id' in m.__dict__.keys():
                if m.from_id is not None:
                    if 'user_id' in m.from_id.__dict__.keys():
                        df = pd.concat([df, pd.DataFrame([{'date': m.date, 'user_id': m.from_id.user_id, 'raw_text': m.raw_text, 'views': m.views,
                             'forwards': m.forwards, 'text': m.text, 'chan': group_name, 'id': m.id}])], ignore_index=True)

    df = df[~df['user_id'].isna()]
    df = df[~df['text'].isna()]
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    df.to_csv(f'../telegram_messages_{group_name}.csv', index=False)

client = TelegramClient('session', app_id, app_hash)
client.start(phone=phone_number, password=password)

with client:
    client.loop.run_until_complete(main())




