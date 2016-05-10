"""
NixieBot.py 
Author: Robin Bussell 

Nixiebot.py will, when run on suitable hardware and provided with valid twitter API keys,
listen for tweets containing a specific hashtag and act on them by displaying words, photographing them
and returning a picture or scrolling movie as a tweet, mentioning the originator ofn the tweet that triggered it.
Inbetween tweet processing it acts as a clock and random tweet display.

Suitable hardware is a raspberry pi with camera module pointed at an array of smartsockets holding B7971
nixie tubes. You'll need to install the picamera and GPIO modues plus grafixmagick for producing the movies.

Tags:  #Nixiebotshowme  main trigger tag,if no other special tags then display nearest word to tag 
            words = text.split(" ") so users can:use:non:dispaying:character:to:seperate:a:phrase
            probably best to change this tag if you run your own bot from this code!
        Other special tags:
             Add files of lines of text called filename.ftn into the working directory to activate the tag #filename to chose a random line from that file 
                    This is how the #eightball and #oblique tags work on the original Nixiebot.
             #twitswears ... summon list of recent swearwords used on twitter
             #twitnice   ... summon list of nice words
             #twitall   ... summon all words used  
             optional modifiers for lists:
                    #alphabetic  ... sorts the selected wordlist #raw turns off deduplication
                    #charts      ... sorts in order of popularity
                    
Health warning! Currently this is a python monolith that has grown too big and messy for its own good, refactor will happen sometime :)

There are four threads running:
    one to gather tweets with the right hashtag(filter streamer)
    one to gather random tweets  (random streamer)
    one to run the clock and tweeting (runClock()
    Main thread has a few console commands.
    
"""

import serial
from twython import Twython , TwythonStreamer
import time
import datetime
import picamera
import queue
import threading
import random
import pickle
import RPi.GPIO as GPIO
import collections
from subprocess import call
from glob import glob
from functools import partial
import os
import re
import html.parser
import botkeys   #API keys are stored in botkeys.py ... edit it with your keys

timeThen=time.time()
com = serial.Serial("/dev/ttyAMA0",baudrate=9600,timeout=1.0)
tubes = 8
scrollIt = False
makeMovie=False
frameCount=0
doSwears = False
doNice = False
sortWords = False
popWords = False
dequeHold = False
doRandoms = True
wordAtATime = False
doAllWords=False
running=True
blanked = False
killURLs  = True
userFont = False
dummyRun = False
effx = 0
fxspeed = 0
log_level=0
originalTweets = 0
reTweets = 0
profileUpdateCounter = 0
onlyOriginalRandoms=True
displayTwOI=True
timeInterval=15
dtctr=0
dtCycles = 3
blankpin = 12  #we use GPIO in BOARD mode so this is a P1 pin number not the broadcom GPIO number
HVToggleTime = 0
scrollInterval = 0.15
userProperChars = ""
cam=None
glitchType = "none"
glitchLevel = 0

botState={'lastDM':0,'lastDMCheckTime':time.time(),'DMdq':collections.deque()}

badwords=["4r5e", "5h1t", "5hit", "a55", "anal", "anus", "ar5e", "arrse", "arse", "ass", "ass-fucker", "asses", "assfucker", "assfukka", "asshole", "assholes", "asswhole", "a_s_s", "b!tch", "b00bs", "b17ch", "b1tch", "ballbag", "balls", "ballsack", "bastard", "beastial", "beastiality", "bellend", "bestial", "bestiality", "bi+ch", "biatch", "bitch", "bitcher", "bitchers", "bitches", "bitchin", "bitching", "bloody", "blow job", "blowjob", "blowjobs", "boiolas", "bollock", "bollok", "boner", "boob", "boobs", "booobs", "boooobs", "booooobs", "booooooobs", "breasts", "buceta", "bugger", "bum", "bunny fucker", "butt", "butthole", "buttmuch", "buttplug", "c0ck", "c0cksucker", "carpet muncher", "cawk", "chink", "cipa", "cl1t", "clit", "clitoris", "clits", "cnut", "cock", "cock-sucker", "cockface", "cockhead", "cockmunch", "cockmuncher", "cocks", "cocksuck", "cocksucked", "cocksucker", "cocksucking", "cocksucks", "cocksuka", "cocksukka", "cok", "cokmuncher", "coksucka", "coon", "cox", "crap", "cum", "cummer", "cumming", "cums", "cumshot", "cunilingus", "cunillingus", "cunnilingus", "cunt", "cuntlick", "cuntlicker", "cuntlicking", "cunts", "cyalis", "cyberfuc", "cyberfuck", "cyberfucked", "cyberfucker", "cyberfuckers", "cyberfucking", "d1ck", "damn", "dick", "dickhead", "dildo", "dildos", "dink", "dinks", "dirsa", "dlck", "dog-fucker", "doggin", "dogging", "donkeyribber", "doosh", "duche", "dyke", "ejaculate", "ejaculated", "ejaculates", "ejaculating", "ejaculatings", "ejaculation", "ejakulate", "f u c k", "f u c k e r", "f4nny", "fag", "fagging", "faggitt", "faggot", "faggs", "fagot", "fagots", "fags", "fanny", "fannyflaps", "fannyfucker", "fanyy", "fatass", "fcuk", "fcuker", "fcuking", "feck", "fecker", "felching", "fellate", "fellatio", "fingerfuck", "fingerfucked", "fingerfucker", "fingerfuckers", "fingerfucking", "fingerfucks", "fistfuck", "fistfucked", "fistfucker", "fistfuckers", "fistfucking", "fistfuckings", "fistfucks", "flange", "fook", "fooker", "fuck", "fucka", "fucked", "fucker", "fuckers", "fuckhead", "fuckheads", "fuckin", "fucking", "fuckings", "fuckingshitmotherfucker", "fuckme", "fucks", "fuckwhit", "fuckwit", "fudge packer", "fudgepacker", "fuk", "fuker", "fukker", "fukkin", "fuks", "fukwhit", "fukwit", "fux", "fux0r", "f_u_c_k", "gangbang", "gangbanged", "gangbangs", "gaylord", "gaysex", "goatse", "god-dam", "god-damned", "goddamn", "goddamned", "hardcoresex", "hell", "heshe", "hoar", "hoare", "hoer", "homo", "hore", "horniest", "horny", "hotsex", "jack-off", "jackoff", "jap", "jerk-off", "jism", "jiz", "jizm", "jizz", "kawk", "knob", "knobead", "knobed", "knobend", "knobhead", "knobjocky", "knobjokey", "kock", "kondum", "kondums", "kum", "kummer", "kumming", "kums", "kunilingus", "l3i+ch", "l3itch", "labia", "lmfao", "lust", "lusting", "m0f0", "m0fo", "m45terbate", "ma5terb8", "ma5terbate", "masochist", "master-bate", "masterb8", "masterbat*", "masterbat3", "masterbate", "masterbation", "masterbations", "masturbate", "mo-fo", "mof0", "mofo", "mothafuck", "mothafucka", "mothafuckas", "mothafuckaz", "mothafucked", "mothafucker", "mothafuckers", "mothafuckin", "mothafucking", "mothafuckings", "mothafucks", "mother fucker", "motherfuck", "motherfucked", "motherfucker", "motherfuckers", "motherfuckin", "motherfucking", "motherfuckings", "motherfuckka", "motherfucks", "muff", "mutha", "muthafecker", "muthafuckker", "muther", "mutherfucker", "n1gger", "nazi", "nigg3r","nigger", "niggers", "nob", "nob jokey", "nobhead", "nobjocky", "nobjokey", "numbnuts", "nutsack", "orgasim", "orgasims", "orgasm", "orgasms", "p0rn", "pawn", "pecker", "penis", "penisfucker", "phonesex", "phuck", "phuk", "phuked", "phuking", "phukked", "phukking", "phuks", "phuq", "pigfucker", "pimpis", "piss", "pissed", "pisser", "pissers", "pisses", "pissflaps", "pissin", "pissing", "pissoff", "poop", "porn", "porno", "pornography", "pornos", "prick", "pricks", "pron", "pube", "pusse", "pussi", "pussies", "pussy", "pussys", "rectum", "retard", "rimjaw", "rimming", "s hit", "s.o.b.", "sadist", "schlong", "screwing", "scroat", "scrote", "scrotum", "semen", "sex", "sh!+", "sh!t", "sh1t", "shag", "shagger", "shaggin", "shagging", "shemale", "shi+", "shit", "shitdick", "shite", "shited", "shitey", "shitfuck", "shitfull", "shithead", "shiting", "shitings", "shits", "shitted", "shitter", "shitters", "shitting", "shittings", "shitty", "skank", "slut", "sluts", "smegma", "smut", "snatch", "son-of-a-bitch", "spac", "spunk", "s_h_i_t", "t1tt1e5", "t1tties", "teets", "teez", "testical", "testicle", "tit", "titfuck", "tits", "titt", "tittie5", "tittiefucker", "titties", "tittyfuck", "tittywank", "titwank", "tosser", "turd", "tw4t", "twat", "twathead", "twatty", "twunt", "twunter", "v14gra", "v1gra", "vagina", "viagra", "vulva", "w00se", "wang", "wank", "wanker", "wanky", "whoar", "whore", "willies", "willy", "xrated", "xxx"]
nicewords=["love","luv","excellent","happy","joy","joyous","fantastic","superb","great","wonderful","nice","respect","respectful","anticipating","lovely","friendly","friend","best","cheers","thanks","glad","satisfied","satisfying","splendid","kind","welcome","welcoming","charming","delicious","pleasant","polite","tender","affable","sympathy","empathy","empathetic","sympathetic","peaceful","fond","good","cake","pie","kitten","kittens","swell","grand","peace","unity","amity","justice","truce","esteem"]
validTags=["twitnice","twitswears","twitall","thetime"] #list of tags that can substitute for an actual word
#validTags=[] #temporary measure
client_args = {'timeout': 90 }
twitter = Twython(botkeys.APP_KEY,botkeys.APP_SECRET,botkeys.USER_KEY,botkeys.USER_SECRET, client_args=client_args)

priorityUsers=["Zedsquared", "NixtestTest"]  #tweets from these users get high priority (for jumping the queue when testing)

#dummyTweet ={ 'text':"dummy text", 
#              'entities' : {
#                    'hashtags':["NixieBotShowMe"]
#                    }
#              'user' : { 'id' : acctID, 'screen_name' : acctName } ,
#                    }
                    
userCounter = collections.Counter()
minInterval=46  #seconds per tweet minimum (2400 per day allowed)
frameLimit = 100
wordq = queue.PriorityQueue() #Stores incoming command tweets, priority allows quicker live testing
randq=queue.Queue(100) #just a little buffer 
consoleQ =  queue.Queue()  # for direct injection messages
maxWordQ = 0 
wordQIdx = 0 #usd to keep wordq items sortable
rollq = queue.Queue()
recentTweetDeque = collections.deque('a',1000)  #random feed seems to be about five a second
recentTweetDeque.clear()
recentIDDeque = collections.deque('a',100) #deduplication deque to spot incoming duplicates from twitter
recentReqs = []
reqPickleFrequency = 100 #how many requests to hold in RAM before writing out to disc

comLock = threading.RLock()
fortunes = {}
fortuneTags = []
qAtZero = False #flag used to determine whether to update twitter profile

class filterStreamer(TwythonStreamer):
    backOffTime = 60
    
    def on_success(self, tweet):
        global recentIDDeque
        if 'text' in tweet and not ('retweeted_status' in tweet) :
            print("<<<<<<<<<<<<<<<<<<<  Incoming!<<<<<<<<<<<<<<<<<< " + html.parser.HTMLParser().unescape(tweet['text']) + tweet['id_str'])
            if tweet['id_str'] not in recentIDDeque :
                 processIncomingTweet(tweet)
                 recentIDDeque.appendleft(tweet['id_str'])
            else :
                print("!!!! duplicate!  Ignored ")
            backOffTime = 60

    def on_error(self, status_code, data):
        global running
        print("************************************error from filter stream!  ")
        print (status_code)
        if (status_code == 420) :
            print("***************** filter is rate limited!" )
            print("*****************sleeping for" + str(self.backOffTime) )
            for i in range (1,int(self.backOffTime / 10)) :
                if running :
                    time.sleep(10)
                else :
                    break
            if self.backOffTime < 1200 :
                self.backOffTime = self.backOffTime * 2
        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        #self.disconnect()

        
class randomStreamer(TwythonStreamer):
    backOffTime = 60
    global randq
    global onlyOriginalRandoms
    
    def on_success(self, data):
        global originalTweets
        global reTweets
        global onlyOriginalRandoms
        global dequeHold
        if 'text' in data:
            if killURLs :
                data['text'] = killURL(data)
            isOriginal = not ('retweeted_status' in data)
            if log_level >=4 :
                print ("incoming Random, deque at: " + str(len(recentTweetDeque)) + "  " + data['text'])
            if not dequeHold : 
                recentTweetDeque.appendleft(data)    
            if not randq.full():
                if (not onlyOriginalRandoms ) or isOriginal :
                    if log_level >=3 :
                        print("##queing random: "  + data['text'] )
                    elif log_level >=2 :
                        print("##queing random: " )
                    randq.put(data)    
            backOffTime = 60

    def on_error(self, status_code, data):
        global running
        print("************************************error from random stream!  ")
        print (status_code)
        if (status_code == 420) :
            print("!!!!!!!!!!!!!!!!!!!! random is rate limited!" )
            print("!!!!!!!!!!!!!!!!!!!! sleeping for" +  str(self.backOffTime) )
            for i in range (1,int(self.backOffTime / 10)) :
                if running :
                    time.sleep(10)
                else :
                    break
            if self.backOffTime <= 7200 :
                self.backOffTime = self.backOffTime * 2    
        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        #self.disconnect()  
    
    def originality_index(self) :
        global recentTweetDeque
        retweets = 0
        tweets = 0
        for i in recentTweetDeque :
            if 'retweeted_status' in i :
                retweets = retweets +1
            tweets = tweets + 1
        if tweets > 0 :
            return(1-(retweets/tweets))
        else :
            return(1)

    def swears(self) :
        global recentTweetDeque
        global dequeHold
        swearlist=[]
        swearcount = 0
        wordcount = 0
        dequeHold = True
        for i in recentTweetDeque :
            twords = i['text'].split()
            for word in twords :
                wordcount = wordcount + 1
                if word in badwords :
                    swearlist.append(word)
                    swearcount = swearcount + 1
        dequeHold = False            
        return {'wordList':swearlist,'wordTypeCount':swearcount,'totalCount':wordcount}            
                    
            
    def nices(self) :
        global recentTweetDeque
        global dequeHold
        nicelist=[]
        nicecount = 0
        wordcount = 0
        dequeHold = True
        for i in recentTweetDeque :
            twords = i['text'].split()
            for word in twords :
                wordcount = wordcount + 1
                if word in nicewords :
                    nicelist.append(word)
                    nicecount = nicecount + 1
        dequeHold = False            
        return {'wordList':nicelist,'wordTypeCount':nicecount,'totalCount':wordcount}      
    
    def allWords(self) :
        global recentTweetDeque
        global dequeHold
        twords=[]
        dequeHold = True
        for i in recentTweetDeque :
            twords.extend(i['text'].split())
        dequeHold = False            
        return {'wordList':twords,'wordTypeCount':len(twords),'totalCount':len(twords)}      


def wordqPut(item, priority = 50) :
    global wordQIdx
    global wordq
    try:
        wordQIdx +=1
        wordq.put((priority,wordQIdx,item)) #items are retrieved as worq.get()[2]
    except :
        print("Exception putting in queue,idx=",wordQIdx)
        
        
def runClock():  #TODO ... use queue get with timeout and try catch as I think it's deadlocking this function when neither queue is being filled
    global wordq
    global randq
    global running
    global tubes
    global twitter
    global timeInterval
    global dtctr
    global cam
    global makeMovie
    global timeThen
    global profileUpdateCounter
    global clockPause
    print("**************clock thread starting ")
    print("GPIO init")
    initGPIO()
    print("Tubes on")
    lightTubes()
    print("Tubes init")
    initTubes()
    timeThen=time.time()
    lastdecade = int(datetime.datetime.now().second ) // timeInterval
    print("main loop entry")
    with picamera.PiCamera() as cam:
        initcam(cam)
        while running:
            makeMovie = False
            if ((time.time() - timeThen) > minInterval) : 
                if not wordq.empty() :
                    tweetOutWord()
                    profileUpdateCounter +=1
                    if profileUpdateCounter == 4 or ( wordq.empty() and  not qAtZero) or (qAtZero and not wordq.empty()) :
                        updateQlength()
                        profileUpdateCounter = 0;
                if not rollq.empty() :
                    rollDice()
            t=datetime.datetime.now()
            if  int(t.second) // timeInterval != lastdecade :
                lastdecade = int(t.second) // timeInterval
                dtctr += 1
                #display time
                setEffex(6,5) # funky dissolve effect
                displayTime()
                time.sleep(1) #give time for dissolve effect to work
                setEffex(1,1)
                for secs in range(4):
                    displayTime()
                    time.sleep(1)
                setEffex(6,5)    
                if displayTwOI and dtctr == dtCycles:  #every so many times the time is displayed, also display twitter stats
                    dtctr=0
                    if log_level >= 5 : print("TWOi display")
                    displayString("TWOI " + str(int(randstream.originality_index()*100)).ljust(tubes) )
                    time.sleep(2)
                    displayString("Q " + str(wordq.qsize()).ljust(tubes) )
                    time.sleep(2.5)
                    if doSwears :
                        displayWords( randstream.swears(), sortem = sortWords , popularity = popWords, uniq = False, doAutoScroll = True)
                    if doNice :
                        displayWords(randstream.nices(), sortem = sortWords, popularity = popWords,uniq = False, doAutoScroll = True)
                    if doAllWords :
                        displayWords(randstream.allWords(), sortem = True, popularity = True,  minLength=tubes, uniq=True,)
            else :  #display a random tweet, if there is one ready
                if doRandoms and not randq.empty():
                    tweet = randq.get()
                    if log_level >= 1 :
                        print( "Displaying random:  " + tweet['text'])
                    if not scrollIt :    
                        displayList(atMostnLetters(tweet['text'].split(),tubes),0.45,False, True) #TODO ... drop the atmostNletters as it defeats autoscroll
                    else :
                        scrollList(tweet['text'].split())
                        
                    randq.task_done()
                    doDMs()
        # we get here if running is false i.e. quit command received
        cam.close()
        print("runclcok closing")
        return

def tweetOutWord() : #main function for processing a tweet that has a command in it
    global makeMovie
    global timeThen
    global glitchLevel
    global glitchType
    lightTubes()
    nextOne=wordq.get()
    tweet = nextOne[2]
    timeThen=time.time()
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>> Tweeting!>>>>>>>",html.parser.HTMLParser().unescape(tweet['text'])," Queue= " + str(wordq.qsize()))
    tt=False   #tt used as simple "has a special hashtag been processed" flag
    setCamEffex(cam, tweet)
    oldGlitchLevel = glitchLevel
    oldGlitchType = glitchType
    setGlitch(tweet)
    for ht in tweet['entities']['hashtags']:
        if ht['text'].lower() =="thetime" and not tt:
            displayTime()
            tt=True
            theWord = "TheTimeIs"
        if ht['text'].lower() =="twitall" and not tt:
            makeMovie = True
            displayWords(randstream.allWords(), scanTags(tweet,"alphabetic") , scanTags(tweet,"charts"), not scanTags(tweet,"raw"), not scanTags(tweet,"noAutoScroll"), topCount=20 ) 
            tt = True
            tweetMovie("movie.gif",tweet,"all_words")    
        if ht['text'].lower() =="twitswears" and not tt:
            makeMovie = True
            displayWords(randstream.swears(), scanTags(tweet,"alphabetic") , scanTags(tweet,"charts"), not scanTags(tweet,"raw"), not scanTags(tweet,"noAutoScroll") )
            tt = True
            tweetMovie("movie.gif",tweet,"swear_words")
        if ht['text'].lower() == "twitnice" and not tt :
            makeMovie = True
            displayWords(randstream.nices(), scanTags(tweet,"alphabetic") , scanTags(tweet,"charts"), not scanTags(tweet,"raw"), not scanTags(tweet,"noAutoScroll"))
            tt = True
            tweetMovie("movie.gif",tweet,"nice_words")
        if ht['text'].lower() in fortuneTags and not tt :
            makeMovie = True
            fortuneAsList = random.choice(fortunes[ht['text'].lower()]).split(" ")
            print("picked fortune ; ", fortuneAsList)
            displayWords({'wordList':fortuneAsList},delay=40)
            tt = True
            makeMovie = False
            tweetMovie("movie.gif",tweet,ht['text'])   
    if not tt: #tt flag gets set if any action other than "display a word that has been submitted "  has happened already
        theWord=extractWord(html.parser.HTMLParser().unescape(tweet['text']))
        picStatus=makeStatusText(tweet, theWord) 
        if len(theWord) > tubes or scanTags(tweet,"scroll"):
            print("movie")
            lockCamExposure(cam)
            makeMovie = True
            scrollString(proper(theWord," "))
            makeGif("tweetWord")
            mediaName = 'tweetWord.gif'
            makeMovie=False
        else :
            print("single shot, makeMovie = ", makeMovie)
            displayString(proper(theWord," ").ljust(tubes))
            time.sleep(1.5)
            cam.capture('tweet.jpg',resize=(800,480))
            mediaName = 'tweet.jpg'
        pic=open(mediaName,'rb')
        addOwners=str(tweet['user']['id'])
        for m in tweet['entities']['user_mentions'] : #add all mentions as media owners so they can pass it on
            userID=m['id_str']
            addOwners = addOwners + "," + userID
        if not dummyRun :
            try:
                print(">>>>>>>>>>>>> Uploading media ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
                response = twitter.upload_media(media=pic, additional_owners=addOwners ) 
                print(">>>>>>>>>>>>> Updating status  ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
                twitter.update_status( status=picStatus, 
                     media_ids=[response['media_id']], 
                     in_reply_to_status_id=tweet['id_str'])
                print(">>>>>>>>>>>>> Done  ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
            except BaseException as e:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Tweeting exception!" + str(e))
                print(" status text =", picStatus)
                if not 'retries' in tweet :
                    tweet['retries'] = 0
                    wordqPut(tweet,priority = 30)
                elif tweet['retries'] < 5 :
                    tweet['retries'] += 1
                    wordqPut(tweet,priority = 30)
        else :
            print("Dummy run, not tweeting")
    #flashWord(theWord,10)
    cam.image_effect="none"
    wordq.task_done()
    glitchLevel=oldGlitchLevel
    glitchType=oldGlitchType
    if blanked : blankTubes()

    
def setGlitch(tweet) :
    #sets glitching according to #glitchlevel:[0-100] and #glitchtype:[swap,shuffle]
    global glitchLevel
    global glitchType
    glitchLevel = 0
    glitchType = "none"
    print("setting gitch")
    level = re.compile(r'glitchlevel(?:100|[0]?[0-9]?[0-9])$')
    typ = re.compile(r'glitchtype(swap|shuffle)$')
    for tx in tweet['entities']['hashtags'] :
        t=tx['text'].lower()
        if level.match(t) :
            try :
                gl = int(t.split("glitchlevel")[1])
                print("glitch level req to ", gl)
                glitchLevel = gl
            except :
                print("glitchlevel setting exception text = ", t, "split = ", gl)
                pass
        if typ.match(t) :
            try :
                gt = t.split("glitchtype")[1]
                print("glitch type req to ", gt)
                glitchType = gt
            except :
                print("glitchtype setting exception text = ", t, "split = ", gt)
                pass
                
    if glitchType !="none" and glitchLevel == 0 :
        glitchLevel = 50
    elif glitchLevel >= 0 and glitchType =="none" :
        glitchType = "swap"
        
def rollDice() :
    global makeMovie
    lightTubes()
    tweet = rollq.get()
    if scanTags(tweet,"EightBall") :
        tweetOutEightBall()  #ToDO ... write this!
    else : #scan tags for xxDyy tag to indicate dice
        numDice = 0
        numFaces = 0
        pattern = re.compile("[1-3]D[0-9][0-9]?")
        for t in tweet['entities']['hashtags'] :
            if pattern.match(t) :
                dice = t.split("D")
                numDice = int(dice[0])
                numfaces = int(dice[1])
                break   #later, maybe make a list of differnt dice encoded and display them all at once
        #TODO  dice rolling here        
    rollq.task_done()
    if blanked : blankTubes()    


def updateQlength() : #sets the description parameter in twitter profile so that queue length can be read, also adds random usage hint.
    global wordq
    global twitter
    global qAtZero
    qLen = wordq.qsize() 
    desc = "dummy"*50  #start with a big string so loop executes at least once!
    while len(desc) > 159 :
        baseDesc= "I'm a twitterised, neon display, clock. Tweet with #NixieBotShowMe and a word, full guide on tumblr. "
        hints = ["","100 character limit on movies.", "Try #twitNice .", "Phrases:need:separators.", "No need to @ mention me.", "Twitter will munge URLs.", "Ask an #eightBall question.", "Be patient with long queues.", "Remember, tweets are not anonymous!","Try #twitSwears.","Try #oblique.", "Use #scroll on short words for a gif"]
        names = ["Neon Clock Tweet Bot", "Nixie McBotFace","Your Words In Neon","Neon Clock Tweet Bot","Neon Clock Tweet Bot"]
        desc = baseDesc+random.choice(hints)
        nom = random.choice(names)
        if qLen > 0 :
            desc = desc + " Queue at: "+ str(wordq.qsize()) + " to go."
            qAtZero = False
        else :
            desc = desc + " Queue : Empty"
            qAtZero = True
    try:
        print(">>>>>>>>>>>>> Updating profile ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
        twitter.update_profile(description = desc, name=nom)
        print(">>>>>>>>>>>>> Done",  datetime.datetime.now().strftime('%H:%M:%S.%f'))
    except:
        print("status update exception!")
 
def doDMs() :
    global botState  #we have to keep track of replied to DMs ourselves
    DMReply = ''' I'm sorry but this bot does not take display commands from direct messages since there should always be a publicly visible origin of anything that is displayed.
    To get a message displayed you need to tweet with the hashtag #NixieBotShowMe and it will display the word immediatley after that hashtag.
    For further info see http://nixiebot.tumblr.com/FAQ and http://nixiebot.tumblr.com/ref 
    This is an automated message sent in reply to all DMs.'''
    newOnes = False
    if time.time() - botState['lastDMCheckTime'] > 120 : #check dms every couple of minutes
        botState['lastDMCheckTime']=time.time()
        lastDM = botState['lastDM']
        lastDMHere = lastDM
        try :
            dms = twitter.get_direct_messages(since_id=lastDM)
        except BaseException as e:
            print("DM fetch exception ", str(e))
        for dm in dms : #gather new messages
            if dm['id'] > lastDM :
                newOnes = True
                print("new DM! ", dm['id'])
                botState['DMdq'].appendleft({'ID':dm['sender']['id_str'],'tries':0})
                if dm['id'] > lastDMHere :
                    lastDMHere = dm['id']
        botState['lastDM']=lastDMHere
        #now send any that are waiting:
        quota = 1
        while len(botState['DMdq']) > 0 and quota >=1 :
            try:
                rep = botState['DMdq'].pop()
                response = twitter.send_direct_message(user_id = rep['ID'], text=DMReply)
                rlr = twitter.get_lastfunction_header('X-Rate-Limit-Remaining')
                rlrst = twitter.get_lastfunction_header('X-Rate-Limit-Reset')
               # print("DM rate limit remaining = ", rlr )
               # print("DM rate limit reset = ", rlrst ) 
               # currently just getting None replies on the above calls... find out why!
                if rlr is not None and rlrst is not None :                
                    quota = rlr - int((rlrst - time.time()) / 60) #number of calls available this interval minus the number of minutes left 
                    print("DM quota = ", quota)
                else :
                    quota = quota - 1  #default to one per minute safe rate
            except BaseException as e:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! DM sending exception!" + str(e))
                rep['tries'] += 1
                quota = quota - 1
                if rep['tries'] < 20 :
                    botState['DMdq'].appendleft(rep)
                else :
                    print("!!!!!******   dropping DM due to too many retries at reply: ", rep)
        if newOnes :
            pickleMe(botState,'stateStash',dateStamp=False)            
        
def displayTime() :
    global tubes
    #print("displaytime")
    if tubes >= 8 :
        displayString(time.strftime("%H %M %S"))
    elif tubes >= 6 :
        displayString(time.strftime("%H %M %S"))
            
def scanTags(tweet, tag) : #case insensitive hashtag detection
    for t in tweet['entities']['hashtags'] :
        if tag.lower() in t['text'].lower() :
            return True
    return False        

def killURL(tweet) :
    text = tweet['text']
    return(text)
    
def tweetMovie(fileName, tweet, tag) :
    if not dummyRun :
        mediaName = fileName
        sens_tags=["swear_words"]
        pic=open(mediaName,'rb')
        picStatus=makeStatusText(tweet, tag) 
        addOwners=str(tweet['user']['id'])
        if tag in sens_tags :
            sensitive = True
        else : sensitive = False    
            
        for m in tweet['entities']['user_mentions'] :
                userID=m['id_str']
                addOwners = addOwners + "," + userID
        #print("tweeting movie, additional owners = ", addOwners)        
        
        try:
            print(">>>>>>>>>>>>> Uploading Movie ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
            response = twitter.upload_media(media=pic, additional_owners=addOwners, possibly_sensitive = sensitive )
            print(">>>>>>>>>>>>> Updating status ", datetime.datetime.now().strftime('%H:%M:%S.%f'))  
            twitter.update_status( status=picStatus, 
                 media_ids=[response['media_id']], 
                 in_reply_to_status_id=tweet['id_str'])
            print(">>>>>>>>>>>>> Done  ", datetime.datetime.now().strftime('%H:%M:%S.%f'))
        except BaseException as e:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Tweeting movie exception!" + str(e))
            print(" status text =", picStatus)
            if not 'retries' in tweet :
                tweet['retries'] = 0
                wordqPut(tweet,priority = prioritise(tweet))
            elif tweet['retries'] < 5 :
                tweet['retries'] += 1
                wordqPut(tweet,priority = prioritise(tweet))
    else : 
        print("Not tweeting...dummy mode")    

        
def displayWords(words, sortem = False, popularity = False, uniq = False, doAutoScroll = True, topCount = None, minLength = 4, maxPop = 1000, delay =20, upperOnly = False ):
    global makeMovie
    global cam
    if makeMovie : 
        setEffex(0,0)
        lockCamExposure(cam)
        if len(words['wordList']) > 100 :
            words['wordList'] = words['wordList'][:frameLimit]
    if sortem :
        if uniq :
            displayList(sorted(set(words['wordList'])),0.3,True, doAutoScroll)
        else :    
            displayList(sorted(words['wordList']),0.3,True, doAutoScroll)
        if log_level >=1 :
            print("*****  SORTED WORDS:", *sorted(words['wordList']))
    elif popularity :
        topWords = []
        for w in words['wordList'] :
            if len(w) >= minLength : topWords.append(w)   
        c = collections.Counter(topWords) 
        commons = c.most_common(topCount)
        commonlist = []
        setEffex(0,0)
        for w in commons :#merge in wordcounts
            if w[1] < maxPop :
                commonlist.append(w[0]+" X "+ str(w[1]))
        for w in commonlist :
            scrollString(proper(w," "))
            if not makeMovie : time.sleep(0.5)
        if log_level >=1 :
            print("***** COMMON WORDS:", *c.most_common())
    else :
        displayList(words['wordList'],0.3,False, doAutoScroll)
        if log_level >=1 :
            print("*****  RAW WORDS:", *words['wordList'])                     
    if makeMovie :
        unlockCamExposure(cam)
        makeGif("movie",delay)
        makeMovie=False

        
def makeGif(name,delay=20) :
    global frameCount
    print("making Movie!")
    # mresult = call(["convert","-delay","20","-loop", "0", "tweetMov*.jpg",name+".gif"]) #imagemagick version
    mresult = call(["gm","convert","-delay",str(delay),"-loop", "0", "tweetMov*.jpg",name+".gif"]) #graphicsMagick version
    print("Make movie command result code = ",mresult)
    for killit in glob("tweetMov*.jpg") :
        if not dummyRun : 
            os.remove(killit) #get rid of the frame files now they're wrapped up
    frameCount=0

def takeFrame(resize = True) :
    global cam
    global frameCount
    if frameCount < 10 :
        frameStr = "00"+ str(frameCount)
    elif  frameCount < 100 :
        frameStr  = "0" + str(frameCount)
    else :
        frameStr = str(frameCount)
    if frameCount % 10 == 0 :
        print("capturing frame:", frameCount)
    if frameCount <= frameLimit and resize:    
        cam.capture('tweetMov'+frameStr+'.jpg',resize=(320,200))
        frameCount += 1
    elif not resize :
        cam.capture('tweetMov'+frameStr+'.jpg')
        frameCount += 1
    else : print("hit frame limit")

    
def lockCamExposure(camra) :
    global makeMovie
    camra.exposure_mode='auto'
    camra.awb_mode = 'auto'
    camra.iso = 0
    makeMovie=False
    displayString("8"*tubes)
    time.sleep(3)
    camra.capture('exposure.jpg')
    #assumes camera is already open and gains have settled
    camra.shutter_speed = camra.exposure_speed
    camra.exposure_mode = 'off'
    g = camra.awb_gains
    camra.awb_mode = 'off'
    camra.awb_gains = g
    #camra.iso = 800
    displayString(" "*tubes)
    makeMovie=True

def unlockCamExposure(camra) :
    camra.exposure_mode='auto'
    camra.awb_mode = 'auto'
    camra.iso = 0
    
def setCamEffex(camra,tweet) :
    #check to see if any camera effect tags are in message and apply them if so (only one effect at a time so last one encountered wins)
    for ht in tweet['entities']['hashtags'] :
        if ht['text'].lower() in camra.IMAGE_EFFECTS :
            camra.image_effect = ht['text'].lower()
            
def makeStatusText(tweet,aWord):
    salutes=("Your wish is my command","Thanks for the suggestion","Hello","Hi",
             "Wotcha","Greetings","Thanks","","","","Thanks for the tweet","Eh-up","Wotcher",
             "So,","Hello","Hi","Good%DAYTIME%","Salutations","Ahoy there", "Well,", "OK,", "Ummm,", "'Sup", "Ah, there you are" )   
    scolds = (". How very original,", ". How old are you? I'm guessing 13,", ". 'Edgy' is dank now, didn't you know? Anyway," , ". Would your mother let you say that? Anyway,",
               ". Really? OK,"     )             
    picStatus = random.choice(salutes) + " @" + tweet['user']['screen_name']
    if aWord.lower() in badwords : 
        r = random.random()
        if r < 0.25:
             picStatus = picStatus + ". How very original,"
        elif r < 0.5:
             picstatus = picStatus + ". How old are you? I'm guessing 13,"
        elif r < 0.6:
             picstatus = picStatus + ". 'Edgy' is dank now, didn't you know? Anyway,"     
        elif r < 0.75:
             picStatus = picStatus + ". Would your mother let you say that? Anyway,"
        elif r < 0.9:
             picstatus = picStatus + ". Really? OK,"
    if aWord.upper() in ("BUM","TIT","POO","WEE","FART") :
        r = random.random()
        if r < 0.25:
             picStatus = picStatus + ". Teeheeeheee, rude! "
        elif r < 0.5:
             picstatus = picStatus + ". Same to you! Anyway, "
        elif r < 0.75:
             picStatus = picStatus + ". Do your parents know you're playing with twitter?"
        elif r < 0.9:
             picstatus = picStatus + ".  What are you, five?"
    if aWord == "TheTimeIs" :
        picStatus=picStatus + " The time (hereabouts) is :"
    if aWord =="swear_words" :
        picStatus=picStatus + " Well, you asked for it, here's a sweary movie:"
    elif aWord =="nice_words" :
       picStatus=picStatus + " Some nice words from tweeps:" 
    else :
        picStatus = picStatus + " here's your pic. "
    
    if scanTags(tweet, "HMHB") :
       picStatus = picStatus + "#HMHB"  
    tailIt = False    
    if len(tweet['entities']['user_mentions'])> 0:
        #print("############ processing mentions ")
        if len(tweet['entities']['user_mentions'])== 1 : 
            if tweet['entities']['user_mentions'][0]['screen_name'].lower() == "nixiebot" : # educate people @mentioning me
                edString = "BTW: No need to @ mention me, just use the tag"
                if len(picStatus) + len(edString) <  90  : picStatus = picStatus + edString
        
        picStatus = picStatus + " Hey:"
        for m in tweet['entities']['user_mentions'] :
            uName=str(m['screen_name'])
            if len(picStatus + uName) <= 97 and not (uName.lower() == "nixiebot") : 
                picStatus = picStatus + " @"+uName + " "
                tailIt = True
        if tailIt : picStatus=picStatus + " this is for you too!"              
    return(picStatus)
                    

def hasCommand(tweet) :
    global validTags
    for t in tweet['entities']['hashtags'] :
        if t['text'].lower() in validTags :
            return(True)
    return(False)
    
                    
def processIncomingTweet(tweet): #check tweet that has come in via the filter stream, it might have commands in it
    # print(tweet)
    global maxWordQ
    global wordq
    global randstream
    if scanTags(tweet,"NixieBotShowMe") :
        theWord=extractWord(html.parser.HTMLParser().unescape(tweet['text']))
        if ((theWord is not None ) or ( hasCommand(tweet))) :
            wordqPut(tweet,priority = prioritise(tweet))
            size = wordq.qsize()
            if size > maxWordQ : maxWordQ = size
            print("word request from", tweet['user']['screen_name'], "word = ", theWord, " Word queue at:", size, "maxqueue was ", maxWordQ)
            recentReqs.append(tweet) # store for sending to hard storage every now and then
            if len(recentReqs) > reqPickleFrequency :
                if pickleMe(recentReqs, "Requests", dateStamp=True) :
                    recentReqs[:]=[]      
            #userCounter.update(tweet['user']['screen_name'])
    elif scanTags(tweet,"NixieBotRollMe") :
        rollq.put(tweet)
        print("roll request incoming! Word queue at:", rollq.qsize())
    else :
        #must be a trump tweet so submit to random for now
        randstream.on_success(tweet)
    
    # DMreceipt bad idea as it still counts against rate limit
    #for ht in tweet['entities']['hashtags']:        
    #    if ht['text']=="NBreceipt" and not rct:
    #        sendReceipt(tweet,theWord,tt)
    #        rct=True           

def prioritise(tweet) :
    # assign a priority number to a tweet, currently just used to shoehorn test tweets in 
    # future use: deprioritise abusive users?
    if tweet['user']['screen_name'] in priorityUsers :
        return(1)
    elif scanTags(tweet,"HMHB"):
         return(40)
    else :
        return(50)

def pickleMe(item, baseName, dateStamp = True) :  #pickle item out to a file named
    fileName = baseName
    if dateStamp :
        fileName = fileName + "-" + time.strftime("%Y%m%d-%H%M%S")
    fileName = fileName + ".pkl"    
    print("Trying to pickle out " + fileName )
    fh = open( fileName, "wb" )
    with fh :
        try :
            pickle.dump(item,fh)
            return (True)
        except : 
            print("exception pickling! better check disc space ")
            return(False)
            
def sendReceipt(tweet,theWord,tt):
    global wordq
    global twitter
    if theWord is None and not tt:
        msg="I'm sorry I couldn't find a word short enough to display in that tweet"
    else:
        msg="Thanks! your message is at position " + str(wordq.qsize()) + " in the queue. I can only tweet once a minute, "
        if wordq.qsize() >5 :
            msg = msg + " so you might have to wait a bit, sorry." 
    msg=msg+" sent: " + time.strftime("%H:%M:%S")               
    twitter.send_direct_message(user_id=tweet['user']['id'], text=msg)
    
    
def extractWord(strng):
    #print("***********************extractword... parameter = " + strng + " type " + str(type(strng))) 
    wordlist=strng.split()
    if log_level >=2 : 
        print("******** wordlist = " + str(wordlist))
    preTag=None
    result=None
    tagged=False
    #scan for a suitable word after the hashtag
    for w in wordlist:
       if w.upper() == "#NIXIEBOTSHOWME" :
         tagged = True
         continue  
       else: 
         preTag = w
       if tagged and w[0] != "#":
           result=w  #get first non hashtag after showme tag
           break
    if result == None and preTag != None :
        result = preTag    
    return(result)

def initGPIO():
    global HVToggleTime
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(blankpin,GPIO.OUT)
    HVToggleTime = 0 # NB check boot behavior of blanking pin, it's high on boot then set this to time.time() to avoid too quick toggle on program start 
    
def blankTubes():
    #blank tubes, honoring maximum frequency of toggle for PSU boards which is ten seconds
    global HVToggleTime
    sleeptime = max(10 - (time.time() - HVToggleTime),0)
    if sleeptime >= 0 and GPIO.input(blankpin):
        time.sleep(sleeptime)
        GPIO.output(blankpin,GPIO.LOW)
        HVToggleTime = time.time()
    
    
def lightTubes():
   #switch on tubes HV supply, honoring maximum frequency of toggle for PSU boards which is ten seconds
    global HVToggleTime
    sleeptime = max(10 - (time.time() - HVToggleTime),0)
    #print(" Lighting tubes, sleeptime = " + str(sleeptime))
    if sleeptime >= 0 and not GPIO.input(blankpin): 
       # print("sleeptime test passed")
        time.sleep(sleeptime)
        HVToggleTime = time.time()    
        GPIO.output(blankpin,GPIO.HIGH)
     
def initTubes():
    global makeMovie
    global comLock
    global userProperChars
    if log_level >= 5 : print("initTubes acquiring comLock")
    with comLock :
        if log_level >= 5 : print("inittubes acq comlock")
        com.write(bytes("\r$B7F11111111111111\r","utf-8"))
        com.write(bytes("$B7E0000000000000000\r","utf-8"))
        com.write(bytes("$B7S0000000000000000\r","utf-8"))
        com.write(bytes("$B7U0000000000000000\r","utf-8"))
        oldmakeMovie = makeMovie
        makeMovie=False
        scrollString("1234567890")
        makeMovie=oldmakeMovie
        try:
            with open("uCharSet.txt",'r') as cf :
                userProperChars = cf.readline()
                print("user charset =", userProperChars)
                toggleUserFont()
        except IOError as e:
            print("no user charset found")        
    if log_level >= 5 : print("initTubes releasing comlock")    
    return

def setEffex(effect, speed):
    global effx
    global fxspeed
    global comLock
    if log_level >= 5 : print("setfx wait for comlock")
    with comLock :
        if log_level >= 5 : print("setfx acq comlock")
        strng=str(effect) * tubes
        com.write(bytes("$B7E"+strng+"\r","utf-8"))
        strng = str(speed) * tubes
        com.write(bytes("$B7S"+strng+"\r","utf-8"))
        effx=effect
        fxspeed=speed
    if log_level >= 5 : print("setfx release comlock")
    return

def proper(strng,subst):
    if userFont :
        properchars = userProperChars
    else :
        properchars="@1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ "
        strng=strng.upper()
    newstring=""
    for i,ch in enumerate(strng):
        if ch not in properchars:
            newstring=newstring+subst
        else:
           newstring=newstring+ch
    return(newstring)


def glitchIt(strng) :
    global glitchLevel
    global glitchType
    slist = list(strng)
    if glitchLevel == 0 :
        return(strng)
    if glitchType.lower() == "swap" :  
        for i in range(0,len(slist)-1) :
            if random.randint(0,100) <=  glitchLevel :
                if userFont :
                    slist[i] = random.choice(userProperChars)
                else :
                    slist[i] = random.choice("@1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ ")                      
    elif glitchType.lower() == "shuffle" :
        if random.randint(0,100) <= glitchLevel :
            if len(slist) >= 4  :
                startCh = random.randint(0,len(slist)-4)
                endCh = random.randint(startCh,len(slist)-2)
                print("shuffling ", startCh, endCh)
                try :
                    random.shuffle(slist[startCh:endCh])
                except  :
                    slist = list(strng) #slice failed due to too short a string and bad random choice, so just reset   
            #random.shuffle(slist)
    strng="".join(slist)         
    return(strng)        
            
    
def displayString(strng, resize = True):
    global comLock
    #print("displaystring wait comlock")
    strng=glitchIt(strng)
    with comLock :
     #   print("displaystring  got comlock")
        if log_level > 5 :
            print("displaying: "+ strng)
        com.write(bytes("$B7M"+strng+"\r","utf-8"))
        if makeMovie:
            takeFrame(resize)
    #print("displaystring rel comlock")        
    return

def scrollString(strng, offset = tubes-2, resize = True):
    global tubes
    global scrollInterval
    stashfx = effx
    stashspeed = fxspeed
    if offset > tubes : offset = tubes
    setEffex(0,0)
    #scroll in from the right
    for startTube in range(tubes - offset,0,-1):
        #print("StartTube=" + str(startTube))
        displayString((" " * startTube) + ( strng[0:tubes-startTube].ljust(tubes) ), resize = resize )
        #print((" " * startTube) + ( strng[0:tubes-startTube].ljust(tubes) ))
        if not makeMovie : time.sleep(scrollInterval)    
    #then scroll out off the left    
    for startChar in range(0,len(strng)-(tubes - 4)):
        displayString(strng[startChar:startChar+tubes].ljust(tubes), resize = resize)
        #print(strng[startChar:startChar+tubes].ljust(tubes))
        if not makeMovie: time.sleep(scrollInterval)
    displayString(" ".ljust(tubes), resize = resize)
    if not makeMovie : time.sleep(scrollInterval)
    setEffex(stashfx,stashspeed)
    
    
def flashWord(strng,times):
    stashfx = effx
    stashspeed = fxspeed
    setEffex(0,0)
    for i in range(1,int(times)):
        displayString(strng.ljust(tubes))
        time.sleep(0.75)
        displayString("       ")
        time.sleep(0.25)
    displayString(strng.ljust(tubes))
    setEffex(stashfx,stashspeed)
    return    
    
    
def nLetters(lst, n):
    outpt = []
    for s in lst :
        if len(s) == n :
            outpt.append(s)
    return(outpt)
   
def atMostnLetters(lst,n) :
    outpt = []
    for s in lst :
        if len(s) <= n :
            outpt.append(s)
    return(outpt)


def displayList(lst, sleepytime, blanket, autoScroll):
    #print ("********************displaylist!")
    #print (lst)
    firstword=True
    for s in lst :
      if autoScroll and len(s) > tubes :
          scrollString(proper(s," "))
      else :    
          displayString(proper(s.ljust(tubes)," "))
      #displaystring(proper(s,"").ljust(tubes))
      if firstword :
        time.sleep(1.0)
        setEffex(1,1)
        firstword=False
      time.sleep(sleepytime)
      if blanket :
        displayString(" " * tubes);
        time.sleep(sleepytime / 2)

def scrollList(lst):
    setEffex(0,0)
    proplist=[]
    for i in lst :
        proplist.append(proper(i," "))
        
    if wordAtATime :
       for s in proplist:
           scrollString(s)
    else:
        scrollString(" ".join(proplist))
        
      
def testIt():
    initGPIO()
    lightTubes()
    initTubes()
    scrollList("The quick brown fox jumped over the lazy red hypercaterpillar".split())
    print("************** running quick test ")
    with picamera.PiCamera() as cam:
        initcam(cam)
        time.sleep(1.5)
        cam.capture('tweet.jpg',resize=(800,480))
    cam.close()
    time.sleep(10)
    return()    

def readStream():
    global running
    global instream
    print("Starting filter stream reader")
    while running:
        try:
           instream.statuses.filter(track="#NixieBotShowMe")
        except BaseException as e:
           print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exception in readstream!") 
           print(e)
           #todo  check for ctrl-c exception and call shutdown etc
           continue
    instream.disconnect()

def enqueueRandoms():
    global running
    global randstream
    print("starting random tweet streamer")
    while running:
           try:
              randstream.statuses.sample(language="en")
           except BaseException as e:
             if log_level >=1 :
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exception in readrandom!")
                print(e)
             continue    
    randstream.disconnect()             
              
def initcam(cam):
    cam.resolution=(1296,730)
    cam.exif_tags['IFD0.Artist']="NixieBotClock"
    cam.exif_tags['IFD0.Copyright']="Robin Bussell"

def changeSettings() :
    input(" Settings: nothing here yet, press a key")
    #things to change: timeInterval, onlyOriginalRandoms, showTwOI, reset TWOI counters
    
def bStr(val) :
    if val :
        return("on")
    else :
        return("off")

def loadUserFont(fontfile) :
    #load in font file generated from online font designer at http://b7971.lucsmall.com/
    #lines should look like: 0x7622, // 0 - A
    #and the bit order should be reversed using the button at the top of that page
    global comLock
    global userProperChars
    font = {}
    stashfx = effx
    stashspeed = fxspeed
    setEffex(0,0)
    userProperChars = ""
    print("loading font")
    with open(fontfile) as ff :
        for line in ff :
            if line == '\n' : continue # cope with blank at end of file
            parts = line.split(",")
            print("parts = ",parts)
            bits = parts[0]
            letter = parts[1].split("-")[1].strip()
            bitval = int(bits,16) 
            print(bitval,letter)
            font[letter] = bitval
    font['-'] = 0x0022  #nasty hack as hyphen entry is broken by the split("-")
    font[','] = 0x0004  # ditto for comma
    font['~'] = 0x1310  # and tilde
    print(len(font)," characters loaded, now sending")
    with comLock :
        print("loadfont got comlock")
        cmd = "$B7F" + "U" * tubes
        print(cmd)
        com.write(bytes(cmd+"\r","utf-8")) 
        for glyph in font:
            userProperChars = userProperChars + glyph
            cmd="$B7W"+glyph
            mask =int('0b0100000000000000',2)
            while mask > 0 :
                if int(font[glyph]) & int(mask) > 0 :
                    cmd = cmd + "1"
                else :
                    cmd = cmd + "0"
                mask = mask >> 1
            print(cmd) 
            com.write(bytes(cmd+"\r","utf-8"))
            time.sleep(0.3)
            cmd="$B7M"+ glyph * tubes
            print(cmd)
            com.write(bytes(cmd+"\r","utf-8"))
        # special case (ok, bodge!) for space as the strip command in the font file parser above will remove it, and all fonts need a space
        cmd="$B7W 000000000000000"
        print(cmd)
        com.write(bytes(cmd+"\r","utf-8"))
        cmd="$B7M                    "
        print(cmd)
        com.write(bytes(cmd+"\r","utf-8"))
        userProperChars = userProperChars + " "
        setEffex(stashfx,stashspeed)
        # now write out character set file ( used by proper()  )
        with open("uCharSet.txt",'w' ) as cf :
            cf.write(userProperChars)       
    print("loadfont rel comlock")
    
    
def toggleUserFont() :
    global userFont
    global comLock
    print("set ufont wait comlock")
    with comLock :
        print("setufont got comlock")
        if not userFont :        
            #set all tubes to use the user font
            global tubes
            cmd = "$B7F" + "U" * tubes
            print(cmd)
            com.write(bytes(cmd+"\r","utf-8"))    
            userFont = True    
        else :
            cmd = "$B7F" + "1" * tubes
            print(cmd)
            com.write(bytes(cmd+"\r","utf-8"))    
            userFont = False    
    print("setufont rel comlock")    

    
def loadTextFortunes() :
    global fortunes
    for fileName in glob("*.ftn") :
        listName = fileName.split(".")[0].lower()
        validTags.append(listName)
        fortuneTags.append(listName)
        print("Loading fortunefile " + fileName + " as " + listName)
        with open(fileName) as f :
            fortunes[listName] = f.readlines()
            print( fortunes[listName])
    

def picNoTweet(txt, name="noTweet") : #take a highest resolution possible pic or movie and don't tweet it out, file to be transported by other means
    global makeMovie
    with comLock : #wait for display to become ready after latest clock loop has finished with it
        if len(txt) > tubes:
            makeMovie = True
            scrollString(proper(txt," "), resize=False)
            makeGif(name)
            makeMovie=False
        else :    
            displayString(proper(txt," ").ljust(tubes))
            time.sleep(1.5)
            cam.capture(name+'.jpg')

def cameraSettings() :
    global cam
    global camset 
    cp = "Camera> "
    camMode = True
    while camMode :
        key = input(cp + "Enter command, H lists camera commands")
        if key.upper() == "H" :
            print ("A toset Auto White Balance mode, currently at : " + str(cam.awb_mode))
            print(" B to set brightness, currently at: " + str(cam.brightness))
            print(" C to set contrast,currently at: " + str(cam.contrast))
            print(" E to set effects, currently at: " + str(cam.image_effect))
            print(" X to set exposure, ")
            print(" T to Take test image ")
            print(" Q to quit back to main mode ")
        elif key.upper() == "E" :
            print(" Available image effects are:"+str(cam.IMAGE_EFFECTS))
        elif key.upper() =="Q" :
            camMode = False
            
        


    
loadTextFortunes()  #read in *.ftnline by line and put into list in fortunes{} directory    
running=True
# retrieve saved queue if file is present here, remember to delete file after!
print("retrieving state")
try:
    with open('tweetstash.pkl','rb') as f:
        stashlist=[]
        print("found stash file, unpickling")
        stashlist=pickle.load(f)
        print("found " + str(len(stashlist)) + " tweets, now enqueuing") 
        for tweet in stashlist :
            #wordqPut(tweet,priority = 50)  #one time hack for old pickle
            if scanTags(tweet[2],"HMHB") :
               wordqPut(tweet[2],priority=40)
            else :
               wordqPut(tweet[2], priority=tweet[0])
        print(" all enqueued, size = " + str(wordq.qsize()))
        f.close()
        os.remove('tweetstash.pkl')
except IOError as e:
    print ("Unable to open stash file, starting queue anew" )#Does not exist OR no read permissions

try:
    with open('stateStash.pkl','rb') as f:
        print("found state file, unpickling")
        botState=pickle.load(f)
        f.close()
except IOError as e:
    print ("Unable to open state file, using defaults" )#Does not exist OR no read permissions    
    
    
# load up ussr characterset uf there is i=one (actual font is stored on eeprom in contrllers, this file is written when font are loaded)    

        
print("setting up filter stream")
instream=filterStreamer(botkeys.APP_KEY,botkeys.APP_SECRET,botkeys.USER_KEY,botkeys.USER_SECRET)
s=threading.Thread(target=readStream)
s.start()
time.sleep(15) #
print("setting up random sample stream")
randstream=randomStreamer(botkeys.APP_KEY,botkeys.APP_SECRET,botkeys.USER_KEY,botkeys.USER_SECRET)
r=threading.Thread(target=enqueueRandoms)
r.start()

print("starting clock thread")
c=threading.Thread(target=runClock)
c.start()


try:
    while running:
        key = input("Enter log level(0-4) q to quit nicely or H for help ")
        if key.upper() == "H" :
            print(" ? for various live stats")
            print("O to toggle Only Original tweets on display, currently: " + bStr(onlyOriginalRandoms))
            print("R to toggle removal of URLs from incoming tweet text (doesn't actually remove URLs yet, currently: " + bStr(killURLs))
            print("T to toggle Twitter Originality Index (TWOI) display, currently: " + bStr(displayTwOI))
            print("C to toggle dispay of recent swear words in random stream, currently: " + bStr(doSwears))
            print("N to toggle display of recent nice words in random stream, currently: " + bStr(doNice))
            print("A to toggle alphabetic sorting of nice or swear words, currently: " + bStr(sortWords))
            print("P to toggle Popularity sorting of nice or swear words, currently: " + bStr(popWords))
            print("S to toggle scrolling of random tweets, currently: " + bStr(scrollIt))
            print("W to toggle scrolling of a Word at a time of random tweets, currently: " + bStr(wordAtATime))
            print("B to toggle Blanking of tubes (can't unblank within ten seconds of blanking due to PSU constraints), currently: " + bStr(blanked))
            print("F to load a user font file into the smartsockets")
            print("U to toggle use of user fonts, currently: " + bStr(userFont))
            print("D to toggle Dummy run mode, no tweets are sent in dummy run mode, currently: " + bStr(dummyRun))
            print("I to inject a test tweet for immediate display")
            print("G to Go take a picture of a supplied string ... not tweeted, high resolution used. ")
            print("E to enter Exposure test mode (for capturing and setting camera parameters")
            print("L to set display gLitch paramters ")
            print("Q to quit nicely, disconnecting twitter streams behind you (if rate limit sleep is in progress it is not interrupted)")
            print("H to display this message")
            
        if key.isdigit() :
            log_level = int(key)
            print("loglevel set to " + key)
        if key =="?" :
            print("word queue length = " + str(wordq.qsize()))
            print("Maximumword queue was " + str(maxWordQ) )
            print("Collected requests buffer length (emptied to disc at ", reqPickleFrequency , ") ", len(recentReqs))
            print("random queue length = " + str(randq.qsize()))
            print("recent random tweet deque length = " + str(len(recentTweetDeque)))
            print("Nice words collected = " + str(randstream.nices()['wordTypeCount']))
            print("Swear words collected = " + str(randstream.swears()['wordTypeCount']))
            print("total words collected = " + str(randstream.swears()['totalCount']))
            print("unique words used = " + str(len(set(randstream.allWords()['wordList']))))            
        if key.upper()=="O" :
            onlyOriginalRandoms = not onlyOriginalRandoms
            print(" original Only = " + str(onlyOriginalRandoms))
        if key.upper() == "T" :
            displayTwOI = not displayTwOI
            print("Originality index display = " + str(displayTwOI))
        if key.upper() == "C" :
            doSwears = not doSwears
            print("Recent Swears display = " + str(doSwears))
        if key.upper() == "N" :
            doNice = not doNice
            print("Recent Nice words display = " + str(doNice))              
        if key.upper() == "A" :
            sortWords = not sortWords
            print("Alphabetic sort recent display = " + str(sortWords))  
        if key.upper() == "P" :
            popWords = not popWords
            print("Popularity sort recent words = " + str(popWords))            
        if key.upper()=="S" :
            scrollIt = not scrollIt
            print("Scrolling randoms = " + str(scrollIt))
        if key.upper()=="W" :
            wordAtATime = not wordAtATime
            print("Scrolling word at a time = " + str(wordAtATime))    
        if key.upper()=="D" :
            dummyRun = not dummyRun
            print("Dummy run mode = " + str(dummyRun))     
        if key.upper()=="B" :
            blanked = not blanked
            print("Blanked = " + str(blanked))
            if not blanked : lightTubes() 
            else : blankTubes()    
        if key.upper() =="F" :
            fileName = input("please enter the font filename ")
            loadUserFont(fileName)
        if key.upper() =="U" :
            toggleUserFont()
            print("user font = " + bStr(userFont))
        if key.upper() == "I" :  #test tweet injection
            print("not implimented yet ")
        if key.upper() == "G" :
            picWord = input("please enter the text to be displayed, it'll be stored as noTweet.jpg ")
            picNoTweet(picWord)
        if key.upper() =="E" :
            cameraSettings()
        if key.upper() == "L" :
            glitchType = input("choose a glitch type ( swap, shuffle ) ")
            glitchLevel = int(input("choose a glitch level from 0 (no effect) to 100 (all letters affected)"))
            print("Glitch Level = ", glitchLevel, " Glitch type = ", glitchType)
        if key == "Q" or key == "q" :
            running = False
            print("joining runclock until it terminates")
            c.join()
            instream.disconnect() 
            randstream.disconnect() 
            GPIO.cleanup() 
            pickleMe(botState,"stateStash",dateStamp=False)
            if wordq.qsize() >0 :
                #save wordqueue if there's anything in it
                print("pickling the queue, size = " +str(wordq.qsize()) + " tweets")
                #can't pickle a queue directly so copyinto a list first
                #check on memory implications of this for large queues sometime
                stash=[]
                print("stashing queue contents")
                while wordq.qsize() >0 :
                    tweet = wordq.get()
                    stash.append(tweet)
                fh = open("tweetstash.pkl", "wb" )    
                pickle.dump( stash, fh ) 
                fh.close()
                print("pickled ok! now joining remaining threads") 
            pickleMe(recentReqs, "Requests", dateStamp=True)
            print("terminating streams")               
            print("joining s")
            s.join()
            print("joining r")
            r.join()
            
            print("all done, bye bye")
except BaseException as e:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exception in main loop")
    print(e)
