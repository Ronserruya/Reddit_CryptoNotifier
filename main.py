import requests
import json
import time
import praw
from praw.models import Message
import config
import re

def bot_login():
    # Login with praw
    print ("Logging in...")
    r = praw.Reddit(username = config.username,
                    password= config.password,
                    client_id = config.client_id,
                    client_secret = config.client_secret,
                    user_agent = 'Cryptocurrencies Prices Notifier')
    print ("Logged in!")

    return r

def GetUnreadMessages(r):
    unreadMessages = []
    for message in r.inbox.unread(limit=None):
        if isinstance(message,Message):
            unreadMessages.append(message)
    r.inbox.mark_read(unreadMessages)
    return unreadMessages

def CheckSyntax(message):

    try:
        token = re.search('(?<=\s)[A-Z]{3}(?=\s)|(?<=\s)[A-Z]{3}$|^[A-Z]{3}(?=\s)',message.body).group(0)
    except:
        return False,0,0

    try:
        amount = re.search('\d+',message.body).group(0)
    except:
        return False,0,0

    words = re.split('\s+',message.body.lower())
    if 'over' in words:
        state = 'over'
    elif 'under' in words:
        state = 'under'
    else:
        return False,0,0

    #e.g BTC under 13500
    return token,state,amount

def UpdateRequestFile(username,token,state,amount):
    try:
        with open('UsersRequests','a') as myFile:
            #e.g 'CatEyes ETH over 800'
            myFile.write('{} {} {} {}\n'.format(username,token,state,amount))
        myFile.close()
    except Exception as e:
        return str(e)
    return True

def GetPrices():
    response = requests.get('https://api.coinmarketcap.com/v1/ticker/')
    JsonPrice = json.loads(response.text)

    prices = []
    for token in JsonPrice:
        prices.append(token['symbol'])
        prices.append(float(token['price_usd']))

    return prices

def CheckRequestes(prices):
    Responses = []
    with open('UsersRequests','r') as myFile:
        Original = myFile.read().splitlines()
    myFile.close()

    with open('UsersRequests','w') as myFile:
        for line in Original:
            username = line.split()[0]
            token = line.split()[1]
            state = line.split()[2]
            amount = float(line.split()[3])
            if state == 'over':
                if amount <= prices[prices.index(token)+1]:
                    Responses.append([username,'You asked me to reminde you, so Im here!.  \n\n{} is now over {}$,'
                                               ' current price is : {}'.format(token,amount
                                                                              ,prices[prices.index(token)+1])])
                    continue
            if state == 'under':
                if amount > prices[prices.index(token)+1]:
                    Responses.append([username, 'You asked me to reminde you, so Im here!.  \n\n{} is now under {}$,'
                                                ' current price is : {}'.format(token,amount
                                                                               ,prices[prices.index(token)+1])])
                    continue
            myFile.write(line+'\n')
    myFile.close()

    return Responses






    return True

def sendPM(r,username,message):
    try:
        r.redditor(username).message('CryptoNotifier notification!',message)
    except:
        return False
    return True

def reportError(r,message):
    developer = config.developer
    r.redditor(developer).message('Crypto error report',message)

def run_bot(r):
    messeges = GetUnreadMessages(r)
    for message in messeges:
        token,state,amount = CheckSyntax(message)
        #Check if I got all needed syntax
        if token != False:
            updateResponse = UpdateRequestFile(message.author.name,token,state,amount)
            if updateResponse:
                sendPM(r,message.author.name,'Got it! I will message you when {} will be {} {}$'
                       .format(token,state,amount))
            else:
                reportError(r,'Error when sending a message: {}'.format(updateResponse))

    Responses = CheckRequestes(GetPrices())
    for response in Responses:
        sendPM(r,response[0],response[1])

def main():
    r = bot_login()
    while (True):
        run_bot(r)
    time.sleep(20)



if __name__ == '__main__':
    main()




