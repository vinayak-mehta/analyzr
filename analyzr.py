import re
import sys
import json
import tweepy
import redis
import requests

from time import sleep
from threading import Thread
from tweepy import OAuthHandler, Stream
from tweepy.streaming import StreamListener
from stop_words import stop_words

# get these from apps.twitter.com
consumer_key = 'x-x-x-x'
consumer_secret = 'x-x-x-x'
access_token = 'x-x-x-x'
access_secret = 'x-x-x-x'

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
r.flushdb() # flush all keys stored in db

tweet_in = 1 # last db write key
tweet_out = 1 # last db read key
count = 0 # number of tweets analyzed
sent = 0 # for API call

class MyStreamListener(StreamListener):
    def on_data(self, data):
        global tweet_in
        r.set('tweet: %d' % tweet_in, data)
        tweet_in += 1

url = 'http://www.sentiment140.com/api/bulkClassifyJson?appid=your_email_id' # sentiment140 API, add your email id
positive = 0
neutral = 0
negative = 0
sentiment_string = "Current sentiment: Positive: 0%, Neutral: 0%, Negative: 0% (updates after every 50 tweets)"
def calculate_sentiment(response):
    global positive, neutral, negative, sentiment_string
    resp = response.json()
    for i in range(len(resp['data'])):
        if resp['data'][i]['polarity'] == 4:
            positive += 1
        elif resp['data'][0]['polarity'] == 2:
            neutral += 1
        else:
            negative += 1
    pos_p = positive / (positive + neutral + negative) * 100
    neu_p = neutral / (positive + neutral + negative) * 100
    neg_p = negative / (positive + neutral + negative) * 100 
    sentiment_string = "Current sentiment: Positive: %.2f%%, Neutral: %.2f%%, Negative: %.2f%% (updates after every 50 tweets)" % (pos_p, neu_p, neg_p)

twitter_stream = Stream(auth, MyStreamListener())
print("Which topic would you like me to analyze?")
topic = input()
t = Thread(target=twitter_stream.filter, kwargs={'track': [topic]})
t.daemon = True
t.start() # start stream thread

# dictionaries
words_d = {}
hashtags_d = {}
tzones_d = {}

req = []

while True:
    try:
        print("\x1b[2J\x1b[H", end="") # clear console output
        if tweet_out > tweet_in - 5:
            sleep(0.5)
            continue
        tweet = r.get('tweet: %d' % tweet_out)
        tweet = json.loads(tweet.decode())

        if tweet['user']['lang'] != 'en': # currently analyzing only english language tweets
            r.delete('tweet: %d' % tweet_out)
            tweet_out += 1
            continue

        r.delete('tweet: %d' % tweet_out)
        tweet_out += 1
        count += 1

        tokenize = re.compile(r'@[\w]+|\#[\w]+|http[s]?://[\w\D\S\W]+|[\w]+') # regex for @-mentions|hashtags|http-links|words
        tokens = tokenize.findall(tweet['text'])

        # top 10 words
        wh = ['@', '#']
        words = [word for word in tokens if word not in stop_words and word[0] not in wh and word[0:4] != 'http']
        for w in words:
            if w not in words_d:
                words_d[w] = 1
            else:
                words_d[w] += 1

        top_w = sorted(words_d, key=words_d.get, reverse=True)[:11]
        print("Top 10 words: ", top_w)

        # top 10 hashtags
        hashtags = [hashtag for hashtag in tokens if hashtag[0] == '#']
        for h in hashtags:
            if h not in hashtags_d:
                hashtags_d[h] = 1
            else:
                hashtags_d[h] += 1

        top_h = sorted(hashtags_d, key=hashtags_d.get, reverse=True)[:11]
        print("Top 10 hashtags: ", top_h)

        # top 10 time zones
        tzone = tweet['user']['time_zone']
        if tzone != None:
            if tzone in tzones_d:
                tzones_d[tzone] += 1
            else:
                tzones_d[tzone] = 1

        top_t = sorted(tzones_d, key=tzones_d.get, reverse=True)[:11]
        print("Top 10 time zones: ", top_t)

        # current sentiment
        req.append({'text': tweet['text']})
        
        if count - sent == 50:
            sent = count
            data = {'data': req} 
            req = []
            response = requests.post(url, json=data) # POST request to sentiment140 API
            calculate_sentiment(response)
        print(sentiment_string)

        print("Tweets analyzed: %d" % count)

    except KeyboardInterrupt:
        sys.exit()
