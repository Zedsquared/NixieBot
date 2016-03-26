""" chopped down nixiebot that just maintains the queue for running while changing hardware or whatever
"""
from twython import Twython , TwythonStreamer
import time
import datetime
import queue
import threading
import random
import pickle
import collections
from subprocess import call
from glob import glob
from functools import partial
import os
import re
import html.parser
import botkeys

timeThen=time.time()
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

badwords=["4r5e", "5h1t", "5hit", "a55", "anal", "anus", "ar5e", "arrse", "arse", "ass", "ass-fucker", "asses", "assfucker", "assfukka", "asshole", "assholes", "asswhole", "a_s_s", "b!tch", "b00bs", "b17ch", "b1tch", "ballbag", "balls", "ballsack", "bastard", "beastial", "beastiality", "bellend", "bestial", "bestiality", "bi+ch", "biatch", "bitch", "bitcher", "bitchers", "bitches", "bitchin", "bitching", "bloody", "blow job", "blowjob", "blowjobs", "boiolas", "bollock", "bollok", "boner", "boob", "boobs", "booobs", "boooobs", "booooobs", "booooooobs", "breasts", "buceta", "bugger", "bum", "bunny fucker", "butt", "butthole", "buttmuch", "buttplug", "c0ck", "c0cksucker", "carpet muncher", "cawk", "chink", "cipa", "cl1t", "clit", "clitoris", "clits", "cnut", "cock", "cock-sucker", "cockface", "cockhead", "cockmunch", "cockmuncher", "cocks", "cocksuck", "cocksucked", "cocksucker", "cocksucking", "cocksucks", "cocksuka", "cocksukka", "cok", "cokmuncher", "coksucka", "coon", "cox", "crap", "cum", "cummer", "cumming", "cums", "cumshot", "cunilingus", "cunillingus", "cunnilingus", "cunt", "cuntlick", "cuntlicker", "cuntlicking", "cunts", "cyalis", "cyberfuc", "cyberfuck", "cyberfucked", "cyberfucker", "cyberfuckers", "cyberfucking", "d1ck", "damn", "dick", "dickhead", "dildo", "dildos", "dink", "dinks", "dirsa", "dlck", "dog-fucker", "doggin", "dogging", "donkeyribber", "doosh", "duche", "dyke", "ejaculate", "ejaculated", "ejaculates", "ejaculating", "ejaculatings", "ejaculation", "ejakulate", "f u c k", "f u c k e r", "f4nny", "fag", "fagging", "faggitt", "faggot", "faggs", "fagot", "fagots", "fags", "fanny", "fannyflaps", "fannyfucker", "fanyy", "fatass", "fcuk", "fcuker", "fcuking", "feck", "fecker", "felching", "fellate", "fellatio", "fingerfuck", "fingerfucked", "fingerfucker", "fingerfuckers", "fingerfucking", "fingerfucks", "fistfuck", "fistfucked", "fistfucker", "fistfuckers", "fistfucking", "fistfuckings", "fistfucks", "flange", "fook", "fooker", "fuck", "fucka", "fucked", "fucker", "fuckers", "fuckhead", "fuckheads", "fuckin", "fucking", "fuckings", "fuckingshitmotherfucker", "fuckme", "fucks", "fuckwhit", "fuckwit", "fudge packer", "fudgepacker", "fuk", "fuker", "fukker", "fukkin", "fuks", "fukwhit", "fukwit", "fux", "fux0r", "f_u_c_k", "gangbang", "gangbanged", "gangbangs", "gaylord", "gaysex", "goatse", "god-dam", "god-damned", "goddamn", "goddamned", "hardcoresex", "hell", "heshe", "hoar", "hoare", "hoer", "homo", "hore", "horniest", "horny", "hotsex", "jack-off", "jackoff", "jap", "jerk-off", "jism", "jiz", "jizm", "jizz", "kawk", "knob", "knobead", "knobed", "knobend", "knobhead", "knobjocky", "knobjokey", "kock", "kondum", "kondums", "kum", "kummer", "kumming", "kums", "kunilingus", "l3i+ch", "l3itch", "labia", "lmfao", "lust", "lusting", "m0f0", "m0fo", "m45terbate", "ma5terb8", "ma5terbate", "masochist", "master-bate", "masterb8", "masterbat*", "masterbat3", "masterbate", "masterbation", "masterbations", "masturbate", "mo-fo", "mof0", "mofo", "mothafuck", "mothafucka", "mothafuckas", "mothafuckaz", "mothafucked", "mothafucker", "mothafuckers", "mothafuckin", "mothafucking", "mothafuckings", "mothafucks", "mother fucker", "motherfuck", "motherfucked", "motherfucker", "motherfuckers", "motherfuckin", "motherfucking", "motherfuckings", "motherfuckka", "motherfucks", "muff", "mutha", "muthafecker", "muthafuckker", "muther", "mutherfucker", "n1gger", "nazi", "nigg3r","nigger", "niggers", "nob", "nob jokey", "nobhead", "nobjocky", "nobjokey", "numbnuts", "nutsack", "orgasim", "orgasims", "orgasm", "orgasms", "p0rn", "pawn", "pecker", "penis", "penisfucker", "phonesex", "phuck", "phuk", "phuked", "phuking", "phukked", "phukking", "phuks", "phuq", "pigfucker", "pimpis", "piss", "pissed", "pisser", "pissers", "pisses", "pissflaps", "pissin", "pissing", "pissoff", "poop", "porn", "porno", "pornography", "pornos", "prick", "pricks", "pron", "pube", "pusse", "pussi", "pussies", "pussy", "pussys", "rectum", "retard", "rimjaw", "rimming", "s hit", "s.o.b.", "sadist", "schlong", "screwing", "scroat", "scrote", "scrotum", "semen", "sex", "sh!+", "sh!t", "sh1t", "shag", "shagger", "shaggin", "shagging", "shemale", "shi+", "shit", "shitdick", "shite", "shited", "shitey", "shitfuck", "shitfull", "shithead", "shiting", "shitings", "shits", "shitted", "shitter", "shitters", "shitting", "shittings", "shitty", "skank", "slut", "sluts", "smegma", "smut", "snatch", "son-of-a-bitch", "spac", "spunk", "s_h_i_t", "t1tt1e5", "t1tties", "teets", "teez", "testical", "testicle", "tit", "titfuck", "tits", "titt", "tittie5", "tittiefucker", "titties", "tittyfuck", "tittywank", "titwank", "tosser", "turd", "tw4t", "twat", "twathead", "twatty", "twunt", "twunter", "v14gra", "v1gra", "vagina", "viagra", "vulva", "w00se", "wang", "wank", "wanker", "wanky", "whoar", "whore", "willies", "willy", "xrated", "xxx"]
nicewords=["love","luv","excellent","happy","joy","joyous","fantastic","superb","great","wonderful","nice","respect","respectful","anticipating","lovely","friendly","friend","best","cheers","thanks","glad","satisfied","satisfying","splendid","kind","welcome","welcoming","charming","delicious","pleasant","polite","tender","affable","sympathy","empathy","empathetic","sympathetic","peaceful","fond","good","cake","pie","kitten","kittens","swell","grand","peace","unity","amity","justice","truce","esteem"]
validTags=["twitnice","twitswears","twitall","thetime"] #list of tags that can substitute for an actual word
twitter = Twython(botkeys.APP_KEY,botkeys.APP_SECRET,botkeys.USER_KEY,botkeys.USER_SECRET)

priorityUsers=["Zedsquared", "NixtestTest"]
#dummyTweet ={ 'text':"dummy text", 
#              'entities' : {
#                    'hashtags':["NixieBotShowMe"]
#                    }
#              'user' : { 'id' : acctID, 'screen_name' : acctName } ,
#                    }
                    
userCounter = collections.Counter()
minInterval=38  #seconds per tweet minimum 
frameLimit = 100
wordq = queue.PriorityQueue() #Stores incoming command tweets,priority allows quicker live testing
randq=queue.Queue(20) #just a little buffer 
consoleQ =  queue.Queue()  # for direct injection messages
maxWordQ = 0 
wordQIdx = 0 #usd to keep wordq items sortable
rollq = queue.Queue()
recentTweetDeque = collections.deque('a',1000)  #random feed seems to be about five a second
recentTweetDeque.clear()

recentReqs = []
reqPickleFrequency = 100 #how many requests to hold in RAM before writing out to disc

comLock = threading.RLock()
fortunes = {}
fortuneTags = []
qAtZero = False #flag used to determine whether to update twitter profile

class filterStreamer(TwythonStreamer):
    backOffTime = 60

    def on_success(self, tweet):
        if 'text' in tweet and not ('retweeted_status' in tweet) :
            print("<<<<<<<<<<<<<<<<<<<  Incoming!<<<<<<<<<<<<<<<<<< " + html.parser.HTMLParser().unescape(tweet['text']))
            processIncomingTweet(tweet)
            backOffTime = 60

    def on_error(self, status_code, data):
        print("************************************error from filter stream!  ")
        print (status_code)
        if (status_code == 420) :
            print("***************** filter is rate limited!" )
            print("*****************sleeping for" + str(self.backOffTime) )
            time.sleep(self.backOffTime)
            if self.backOffTime < 1200 :
                self.backOffTime = self.backOffTime * 2
        # Want to stop trying to get data because of the error?
        # Uncomment the next line!
        #self.disconnect()


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
    global running
    global tubes
    global twitter
    global timeInterval
    global dtctr
    global cam
    global makeMovie
    global timeThen
    global profileUpdateCounter
    print("**************clock thread starting ")
    timeThen=time.time()
    lastdecade = int(datetime.datetime.now().second ) // timeInterval
    print("main loop entry")
    while running:
        if ((time.time() - timeThen) > minInterval) : #brain dead rate limit algo, should really examine returned headers in case of limit
            if not wordq.empty() :
                profileUpdateCounter +=1
                if profileUpdateCounter == 4 or ( wordq.empty() and  not qAtZero) or (qAtZero and not wordq.empty()) :
                    updateQlength()
                    profileUpdateCounter = 0;
            timeThen = time.time()       
        t=datetime.datetime.now()
    print("runclcok closing")
    return


def updateQlength() : #sets the description parameter in twitter profile so that queue length can be read, also adds random usage hint.
    global wordq
    global twitter
    global qAtZero
    qLen = wordq.qsize() 
    desc = "dummy"*50  #start with a big string so loop executes at least once!
    while len(desc) > 159 :
        baseDesc= "I'm a twitterised, neon display, clock. Full guide on tumblr. "
        hints = ["MAINTENANCE MODE!, tweets are being collected and queued only"]
        desc = baseDesc+random.choice(hints)
        if qLen > 0 :
            desc = desc + " Queue at: "+ str(wordq.qsize()) + " to go."
            qAtZero = False
        else :
            desc = desc + " Queue : Empty"
            qAtZero = True
    try:
        print("Updating profile :",desc)
        twitter.update_profile(description = desc)
    except:
        print("status update exception!")
        
            
def scanTags(tweet, tag) : #case insensitive hashtag detection
    for t in tweet['entities']['hashtags'] :
        if tag.lower() in t['text'].lower() :
            return True
    return False        

def killURL(tweet) :
    text = tweet['text']
    return(text)
    
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
    else :
        return(50)

def pickleMe(item, baseName, dateStamp = True) :  #pickle item out to a file named
    fileName = baseName + "-" + time.strftime("%Y%m%d-%H%M%S")+ ".pkl"
    print("Trying to pickle out " + fileName )
    try :
        pickle.dump(item,open( fileName, "wb" ))
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


def readStream():
    global running
    global instream
    print("Starting filter stream reader")
    while running:
        try:
           instream.statuses.filter(track="#NixieBotShowMe,#NixieBotRollMe")
        except BaseException as e:
           print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exception in readstream!") 
           print(e)
           #todo  check for ctrl-c exception and call shutdown etc
           continue
    instream.disconnect()

def changeSettings() :
    input(" Settings: nothing here yet, press a key")
    #things to change: timeInterval, onlyOriginalRandoms, showTwOI, reset TWOI counters
    
def bStr(val) :
    if val :
        return("on")
    else :
        return("off")

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
    
    global fortunes
    for fileName in glob("*.ftn") :
        listName = fileName.split(".")[0].lower()
        validTags.append(listName)
        fortuneTags.append(listName)
        print("Loading fortunefile " + fileName + " as " + listName)
        with open(fileName) as f :
            fortunes[listName] = f.readlines()
            print( fortunes[listName])
    
     
running=True
# retrieve saved queue if file is present here, remember to delete file after!
try:
    with open('tweetstash.pkl','rb') as f:
        stashlist=[]
        print("found stash file,unpickling")
        stashlist=pickle.load(f)
        print("found " + str(len(stashlist)) + " tweets, now enqueuing") 
        for tweet in stashlist :
            #wordqPut(tweet,priority = 50)  #one time hack for old pickle
            wordqPut(tweet[2], priority=tweet[0])
        print(" all enqueued, size = " + str(wordq.qsize()))
        f.close()
        os.remove('tweetstash.pkl')
except IOError as e:
    print ("Unable to open stash file, starting queue anew" )#Does not exist OR no read permissions
# load up ussr characterset uf there is i=one (actual font is stored on eeprom in contrllers, this file is written when font are loaded)    

        
print("setting up incoming filter stream")
instream=filterStreamer(botkeys.APP_KEY,botkeys.APP_SECRET,botkeys.USER_KEY,botkeys.USER_SECRET)

print("starting threads")
c=threading.Thread(target=runClock)
c.start()
s=threading.Thread(target=readStream)
s.start()
try:
    while running:
        key = input("Enter log level(0-4) q to quit nicely or H for help ")
        if key.upper() == "H" :
            print(" ? for various live stats")
            print("Q to quit nicely, disconnecting twitter streams behind you (if rate limit sleep is in progress it is not interrupted)")
            print("H to display this message")
            
        if key.isdigit() :
            log_level = int(key)
            print("loglevel set to " + key)
        if key =="?" :
            print("word queue length = " + str(wordq.qsize()))
            print("Maximumword queue was " + str(maxWordQ) )
            print("Collected requests buffer length (emptied to disc at ", reqPickleFrequency , ") ", len(recentReqs))         
        if key == "Q" or key == "q" :
            running = False
            print("joining runclock until it terminates")
            c.join()
            instream.disconnect() 
            print("terminating streams")               
            print("joining s")
            s.join()
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
                pickle.dump( stash, open( "tweetstash.pkl", "wb" ) ) 
                print("pickled ok! now joining remaining threads") 
            pickleMe(recentReqs, "Requests", dateStamp=True)
            print("all done, bye bye")
except BaseException as e:
    print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!exception in main loop")
    print(e)