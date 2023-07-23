import threading
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

import openai
from openai.embeddings_utils import cosine_similarity

import numpy as np
import pandas as pd

import argparse
import functools

# Create an Argument Parser object
parser = argparse.ArgumentParser(description='Run the bot which uses prepared knowledge base enriched with contextual embeddings')

# Add the arguments
parser.add_argument('--openai_api_key', type=str, help='API KEY of OpenAI API to create contextual embeddings for each line')
parser.add_argument('--telegram_bot_token', type=str, help='A telegram bot token obtained via @BotFather')
parser.add_argument('--file', type=str, help='A source CSV file with the questions, answers and embeddings')
parser.add_argument('--topic', type=str, help='Write the topic to add a default context for the bot')
parser.add_argument('--start_message', type=str, help="The text that will be shown to the users after they click /start button/command", default="Hello, World!")
parser.add_argument('--model', type=str, help='A model of ChatGPT which will be used', default='gpt-3.5-turbo-16k')
parser.add_argument('--num_top_qa', type=str, help="The number of top similar questions' answers as a context", default=3)

# Parse the command-line arguments
args = parser.parse_args()

# Access the argument values
openai.api_key = args.openai_api_key
token = args.telegram_bot_token
file = args.file
topic = args.topic
model = args.model
num_top_qa = args.num_top_qa
start_message = args.start_message

# reading QA file with embeddings
df_qa = pd.read_csv(file)
df_qa['ada_embedding'] = df_qa.ada_embedding.apply(eval).apply(np.array)



def retry_on_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        max_retries = 3
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Error occurred, retrying ({i+1}/{max_retries} attempts)...")
        # If all retries failed, raise the last exception
        raise e

    return wrapper

@retry_on_error
def call_chatgpt(*args, **kwargs):
    return openai.ChatCompletion.create(*args, **kwargs)


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input = [text], model=model)['data'][0]['embedding']


def search_similar(df, product_description, n=3, pprint=True):
    embedding = get_embedding(product_description, model='text-embedding-ada-002')
    df['similarities'] = df.ada_embedding.apply(lambda x: cosine_similarity(x, embedding))
    res = df.sort_values('similarities', ascending=False).head(n)
    return res


def collect_text_qa(df):
    text = ''
    for i, row in df.iterrows():
        text += f'Q: <'+row['Question'] + '>\nA: <'+ row['Answer'] +'>\n\n'
    print('len qa', len(text.split(' ')))
    return text

def telegram_message_format(text):
    max_message_length = 4096

    if len(text) > max_message_length:
        parts = []
        while len(text) > max_message_length:
            parts.append(text[:max_message_length])
            text = text[max_message_length:]
        parts.append(text)
        return parts
    else:
        return [text]


def collect_full_prompt(question, qa_prompt, chat_prompt=None):
    prompt = f'I need to get an answer to the question related to the topic of "{topic}": ' + "{{{"+ question +"}}}. "
    prompt += '\n\nPossibly, you might find an answer in these Q&As [use the information only if it is actually relevant and useful for the question answering]: \n\n' + qa_prompt
    # edit if you need to use this also
    if chat_prompt is not None:
        prompt += "---------\nIf you didn't find a clear answer in the Q&As, possibly, these talks from chats might be helpful to answer properly [use the information only if it is actually relevant and useful for the question answering]: \n\n" + chat_prompt
    prompt += f'\nFinally, only if the information above was not enough you can use your knowledge in the topic of "{topic}" to answer the question.'

    return prompt


def start(update, context):
    user = update.effective_user
    context.bot.send_message(chat_id=user.id, text=start_message)

def message_handler(update, context):

    thread = threading.Thread(target=long_running_task, args=(update, context))
    thread.start()

def long_running_task(update, context):
    user = update.effective_user
    context.bot.send_message(chat_id=user.id, text='🕰️⏰🕙⏱️⏳...')

    try:
        question = update.message.text.strip()
    except Exception as e:
        context.bot.send_message(chat_id=user.id,
                                 text=f"🤔It seems like you're sending not text to the bot. Currently, the bot can only work with text requests.")
        return

    try:
        qa_found = search_similar(df_qa, question, n=num_top_qa)
        qa_prompt = collect_text_qa(qa_found)
        full_prompt = collect_full_prompt(question, qa_prompt)
    except Exception as e:
        context.bot.send_message(chat_id=user.id,
                                 text=f"Search failed. Debug needed.")
        return

    try:
        print(full_prompt)
        completion = call_chatgpt(
            model=model,
            n=1,
            messages=[{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": full_prompt}]
        )
        result = completion['choices'][0]['message']['content']
    except Exception as e:
        context.bot.send_message(chat_id=user.id,
                                 text=f'It seems like the OpenAI service is responding with errors. Try sending the request again.')
        return

    parts = telegram_message_format(result)
    for part in parts:
        update.message.reply_text(part, reply_to_message_id=update.message.message_id)


bot = telegram.Bot(token=token)
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", start, filters=Filters.chat_type.private))
dispatcher.add_handler(MessageHandler(~Filters.command & Filters.text, message_handler))

updater.start_polling()
