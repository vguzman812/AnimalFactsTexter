import os
import random
import pandas as pd
from twilio.rest import Client
from dotenv import load_dotenv
import ast
from datetime import date
import urllib
import requests


load_dotenv()

CUTTLY_API_KEY = os.environ.get("CUTTLY_API_KEY")
ACCOUNT_SID = os.environ.get("ACCOUNT_SID")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
SENDING_NUMBER = os.environ.get("SENDING_NUMBER")
RECEIVING_NUMBERS_STR = os.environ.get("RECEIVING_NUMBERS") # type == string
RECEIVING_NUMBERS_DICT = ast.literal_eval(RECEIVING_NUMBERS_STR) # type == dictionary {"name" : "adam", "phone number": "+19876543210", etc...}

# Load dataset and filter out rows without media link
data = pd.read_csv("animal-fun-facts-dataset.csv").dropna(subset=['media_link'])
# column names are: animal_name, source, text, media_link, wikipedia_link

# Load used indices from log file, or initialize as empty set
try:
    with open("used_indices.log", "r") as file:
        used_indices = set(map(int, file.read().split()))
except FileNotFoundError:
    used_indices = set()

# Select an unused random index
while True:
    rand_index = random.randint(0, len(data) - 1)
    if rand_index not in used_indices:
        used_indices.add(rand_index)
        # Compare number of rows in the CSV to the number of indices in the used indices log
        remaining_rows = len(data) - len(used_indices)
        if remaining_rows < 30:
            print(f"WARNING: THERE ARE ONLY {remaining_rows} UNUSED ROWS LEFT.")
        break

# Write the used index to the log file
with open("used_indices.log", "w") as file:
    for index in used_indices:
        file.write(f"{index}\n")


# Select the row with the random unused index
selected_row = data.iloc[rand_index]


animal_name = selected_row.animal_name
animal_fact = selected_row.text
wikipedia_link = selected_row.wikipedia_link
media_link = None
media_message = ""

# if media link present/ not NaN then include it
if pd.notna(selected_row.media_link):
    # get media link from selected row
    media_link = selected_row.media_link
    # parse media link for use in cuttly API
    short_media = urllib.parse.quote(f'{media_link}')
    # request from cuttly API
    r = requests.get('http://cutt.ly/api/api.php?key={}&short={}'.format(CUTTLY_API_KEY, short_media, ))
    short_link = r.json()['url']['shortLink']
    # put short url in media_message
    media_message = "Media Link: \n" \
                    f"{short_link}\n"

# if wikipedia_link not NaN add "wikipedia.org" on to the front
if pd.notna(selected_row.wikipedia_link):
    wikipedia_link = "wikipedia.org" + wikipedia_link



# use Twilio API to compose and send text message
client = Client(ACCOUNT_SID, AUTH_TOKEN)
for receiver in RECEIVING_NUMBERS_DICT:
    first_name = receiver.split()[0]
    receiving_number = RECEIVING_NUMBERS_DICT[receiver]
    message = client.messages.create(
        body=f"Hello, {first_name}.☀️\n" \
             "Another beautiful day is here! That means it's time for another animal 🐙 fact!\n " \
             f"\nAnimal of the day: {animal_name}\n" \
             f"\n{animal_fact}\n" \
             f"\n{wikipedia_link}\n" \
             f"\n{media_message}" \
             "\nRemember, you are beautiful, strong, and loved. Now go make this day good!",
        from_=SENDING_NUMBER,
        to=receiving_number,
    )
    # print key response phrases
    print(f"\nattempt message send to: {receiver}" \
        f"\nstatus: {message.status}," \
        f"\nerror: {message.error_code}," \
        f"\nerror message: {message.error_message}," \
        f"\nsegments: {message.num_segments}," \
        f"\nprice: {message.price}")

for i in RECEIVING_NUMBERS_DICT:
    print(i, RECEIVING_NUMBERS_DICT[i])

print(
    f"date: {date.today()}\n" \
    f"fact: {animal_fact}\n" \
    f"wikipedia: {wikipedia_link}\n" \
    f"media: {media_link}\n"
)
print(f"Hello, name.☀️\n" \
        "Another beautiful day is here! That means it's time for another animal 🐙 fact!\n " \
         f"\nAnimal of the day: {animal_name}\n" \
         f"\n{animal_fact}\n" \
         f"\n{wikipedia_link}\n" \
         f"\n{media_message}" \
         "\nRemember, you are beautiful, strong, and loved. Now go make this day good!")
