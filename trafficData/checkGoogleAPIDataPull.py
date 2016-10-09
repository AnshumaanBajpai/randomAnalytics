###############################################################################
## This script performs a basic check on the data saved to the MongoBD database
###############################################################################

## Importing the required objects and libraries
import datetime
import json
import pymongo
import crython
import requests

## Setting up paths and some global constants
passwdPath = r'./senderPasswd.txt'
with open(passwdPath, 'r') as spt:
    passwd = spt.readline()
## Path to MongoDB database in mLab
MONGODB_URI = 'mongodb://AnshumaanBajpaiIBM:'+passwd+'@ds041546.mlab.com:41546/trafficdata_ibm'


def checkMongoDB():
    '''
    Checks to make sure that the queries sent have had proper responses

    @returns
    None
    '''
    # Connecting to the proper database
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.get_default_database()
    
    startTimeStr = "10-08-2016_06:50:00"
    startTime = datetime.datetime.strptime(startTimeStr, '%m-%d-%Y_%H:%M:%S')
    currentTime = datetime.datetime.now()
    numQueries = int((currentTime - startTime).total_seconds()/60/15) + 1
    expectedEntries = numQueries * 52
    
    # First we'll connect to a collection in the database
    trips = db['trips']
    # All entries
    cursor_all = trips.find()
    cursor_ok = trips.find({'status': "OK"})
    
    # Results
    print "Expected Entries: ", expectedEntries
    print "Found Entries: ", cursor_all.count() - 7020
    print "OK Entries: ", cursor_ok.count() - 7020

    # Close the connection
    client.close()
    
    return None
    
checkMongoDB()
