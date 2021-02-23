import requests
import collections
import string
import os
import alpaca_trade_api as tradeapi
import json
import pyotp
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone
import robin_stocks.robinhood as r

def hello_world(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    # Set CORS headers for the preflight request
    if request.method == 'OPTIONS':
        # Allows GET requests from any origin with the Content-Type
        # header and caches preflight response for an 3600s
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        print("options")
        return ('', 204, headers)

    # Set CORS headers for the main request
    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    request_json = request.get_json()
    tweet = request_json['tweet']
    print(tweet) # for logging
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    alpaca = tradeapi.REST(
        os.getenv("ACCESS_KEY_ID"),
        os.getenv("SECRET_ACCESS_KEY"),
        base_url="https://paper-api.alpaca.markets"
    )

    # Get the tweet
    # Get the stock ticker from the tweet
    ticker, qty = getStockTicker(tweet)
    print(ticker, qty)
    if ticker == "" or qty <= 0:
        response = {
            "success": "false" 
        }
        return (json.dumps(response, default=str), 200, headers)

    # buy the stock on Alpaca
    alpaca.submit_order(
        symbol=ticker,
        qty=qty,
        side='buy',
        type='market',
        time_in_force='gtc'
    )

    # buy the stock on robinhood
    totp  = pyotp.TOTP(os.getenv("MFA_TOKEN")).now()
    print("Current OTP:", totp)
    login = r.login(os.getenv("RH_USERNAME"), os.getenv("RH_PASSWORD"), mfa_code=totp)
    order = r.order_buy_fractional_by_quantity(
        ticker,
        qty
    )

    response = {
        "success": "true" 
    }

    return (json.dumps(response, default=str), 200, headers)

def getAllTickers():
    from urllib.request import urlopen

    r = urlopen("https://www.sec.gov/include/ticker.txt")

    tickers = {line.decode('UTF-8').split("\t")[0].upper() for line in r}
    return tickers

def getStockTicker(tweet):
    allTickers = getAllTickers()
    try: 
        amount = tweet.split("i'm buying ")
        amount = amount[1] # the part right after "im buying"
        amount = int(amount.split(" ")[0])
    except:
        return "", -1

    for word in tweet.split(" "):
        if '$' not in word:
            continue
        word = word.replace("$", "")
        word = word.translate(str.maketrans('', '', string.punctuation))
        if word.upper() not in allTickers:
            continue
        return word.upper(), amount
    return "", -1

# For local testing
# class Object(object):
#     pass

# if __name__ == "__main__":
#     request = Object()
#     request.method = "GET"
#     request.get_json = lambda: {"tweet": "i'm buying 2 shares of $GSV"}
#     hello_world(request)