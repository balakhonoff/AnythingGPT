import requests
import json
import pandas as pd
import argparse

# Create an Argument Parser object
parser = argparse.ArgumentParser(description='Discord Channel Data Collection Script')

# Add the arguments
parser.add_argument('--channel_id', type=str, help='Channel ID from the URL of a channel in browser https://discord.com/channels/xxx/{CHANNEL_ID}')
parser.add_argument('--authorization_key', type=str, help='Authorization Key. Being on the discord channel page, start typing anything, then open developer tools -> Network -> Find "typing" -> Headers -> Authorization.')

# Parse the command-line arguments
args = parser.parse_args()

# Access the argument values
channel_id = args.channel_id
authorization_key = args.authorization_key

# Print the argument values
print(f"Channel ID: {channel_id}")
print(f"Authorization Key: {authorization_key}")


def retrieve_messages(channel_id, authorization_key):
    num = 0
    limit = 100

    headers = {
        'authorization': authorization_key
    }

    last_message_id = None

    # Create a pandas DataFrame
    df = pd.DataFrame(columns=['id', 'dt', 'text', 'author_id', 'author_username', 'is_bot', 'is_reply', 'id_reply'])

    while True:
        query_parameters = f'limit={limit}'
        if last_message_id is not None:
            query_parameters += f'&before={last_message_id}'

        r = requests.get(
            f'https://discord.com/api/v9/channels/{channel_id}/messages?{query_parameters}', headers=headers
        )
        jsonn = json.loads(r.text)
        if len(jsonn) == 0:
            break

        for value in jsonn:
            is_reply = False
            id_reply = '0'
            if 'message_reference' in value and value['message_reference'] is not None:
                if 'message_id' in value['message_reference'].keys():
                    is_reply = True
                    id_reply = value['message_reference']['message_id']

            text = value['content']
            if 'embeds' in value.keys():
                if len(value['embeds'])>0:
                    for x in value['embeds']:
                        if 'description' in x.keys():
                            if text != '':
                                text += ' ' + x['description']
                            else:
                                text = x['description']
            df_t = pd.DataFrame({
                'id': value['id'],
                'dt': value['timestamp'],
                'text': text,
                'author_id': value['author']['id'],
                'author_username': value['author']['username'],
                'is_bot': value['author']['bot'] if 'bot' in value['author'].keys() else False,
                'is_reply': is_reply,
                'id_reply': id_reply,
            }, index=[0])
            if len(df) == 0:
                df = df_t.copy()
            else:
                df = pd.concat([df, df_t], ignore_index=True)

            last_message_id = value['id']
            num = num + 1

        print('number of messages we collected is', num)


        # Save DataFrame to a CSV file
        df.to_csv(f'../discord_messages_{channel_id}.csv', index=False)


if __name__ == '__main__':
    retrieve_messages(channel_id, authorization_key)