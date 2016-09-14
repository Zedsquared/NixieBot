import pykml
import pickle
from glob import glob
import collections

files = sorted(glob("Req*.pkl"))
print("number of files found: ", len(files))
#print("earliest: ", datefromFile(files[0]))
#print("latest: ", dateFromFile(files[-1]))
oldest = int(input("how may files back to start?"))
latest = int(input("how many to process?"))
oldest = len(files) - oldest
latest = latest + oldest
geoLocTotal = 0
tweetsTotal = 0
placedTotal = 0
langTotal = 0
locatedUsers=0
userctr = collections.Counter()
countryctr = collections.Counter()
langctr = collections.Counter()
for f in files[oldest:latest] :
    #print("processing file", f)
    with open(f,'rb') as pkl :
        try :
            tweets = pickle.load(pkl)
        except: 
            print("!!!!!!!!!!!!!!!couldn't unpickle file ", f )
        else:
            #print(len(tweets), " tweets in file" )
            for tweet in tweets :
                tweetsTotal += 1
                if 'coordinates' in tweet and tweet['coordinates'] is not None:
                    print(tweet['coordinates'])
                    geoLocTotal += 1   
                if 'place' in tweet and tweet['place'] is not None :
                    placedTotal += 1
                    print( tweet['place']['country'])
                    countryctr.update({tweet['place']['country_code']:1})
                if 'lang' in tweet and tweet['lang'] is not None :
                    langTotal += 1
                    print( tweet['lang']['country'])
                    langctr.update({tweet['lang']:1})    
                if 'user' in tweet :
                    userctr.update({tweet['user']['id_str']:1})
                    if 'location' in tweet['user'] and tweet['user']['location'] is not None :
                        if userctr[tweet['user']['id_str']] == 1 :
                            locatedUsers += 1
                            #print(tweet['user']['location'])
print("Total tweets: ", tweetsTotal)
print("Total geolocated tweets ", geoLocTotal)
print("Total placed tweets ", placedTotal)
print("Total tweets with language set", langTotal)
print("top ten languages: ", lanctr.most_common(10))
print("number of languages used:", len(langctr))
print("Total unique users: ", len(userctr)) 
print ("top ten users : ", userctr.most_common(10))
print("Total located users = ", locatedUsers)
print ("Total countries reached", len(countryctr))
print("Top ten countries: ", countryctr.most_common(10))
    
