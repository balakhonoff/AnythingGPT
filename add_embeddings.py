import pandas as pd
import openai
import argparse


# Create an Argument Parser object
parser = argparse.ArgumentParser(description='Adding embeddings for each line of csv file')

# Add the arguments
parser.add_argument('--openai_api_key', type=str, help='API KEY of OpenAI API to create contextual embeddings for each line')
parser.add_argument('--file', type=str, help='A source CSV file with the text data')
parser.add_argument('--colname', type=str, help='Column name with the texts')

# Parse the command-line arguments
args = parser.parse_args()

# Access the argument values
openai.api_key = args.openai_api_key
file = args.file
colname = args.colname

if file[-4:] == '.csv':
    df = pd.read_csv(file)
else:
    df = pd.read_excel(file)

# filter NAs
df = df[~df[colname].isna()]
# Keep only questions
df = df[df[colname].str.contains('\?')]


def get_embedding(text, model="text-embedding-ada-002"):
    i = 0
    max_try = 3
    # to avoid random OpenAI API fails:
    while i < max_try:
        try:
            text = text.replace("\n", " ")
            result = openai.Embedding.create(input=[text], model=model)['data'][0]['embedding']
            return result
        except:
            i += 1


def process_row(x):
    return get_embedding(x, model='text-embedding-ada-002')


df['ada_embedding'] = df[colname].apply(process_row)
df.to_csv(file[:-4]+'_question_embed.csv', index=False)


