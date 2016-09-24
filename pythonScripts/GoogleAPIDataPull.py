###############################################################################
## This script pulls the required data from GoogleMaps API. The aim is to
## obtain a set of estimated time of travel between destinations and origins
__author__ = "Anshumaan Bajpai, and Tanuj Pandey"
__email__ = "bajpai.anshumaan@gmail.com, tanuj5480@gmail.com"


## Importing the required objects and libraries
import os
import time
import requests


## Setting up paths and some global constants
baseDir = os.path.normpath(r'C:/Users/Anshumaan/Desktop/Github/randomAnalytics/pythonScripts')
GMAQueryPath = os.path.join(baseDir, 'API_params.txt')
GMAKeyPath = os.path.join(baseDir, 'GMA_key.txt')
genAPIQuery = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destinations}&departure_time={departure_time}&traffic_model={traffic_model}&key={key}"


## Function to send the data query and obtain the results
def getETTMatrixJson(fpath_input, fpath_API):
    '''
    Obtains the Estimated Trip Time matrix for a given API query. The API
    query is generated using the data from an input file
    
    @param
    fpath_input: Path to the input file which has the basic parameters for API query
    fpath_API: Path to the API Key which is hidden and not shared with everyone
    
    @return
    JSON object which contains the response from the API query
    '''
    APIQueryDict = {}
    # Adding the API key
    with open(fpath_API, 'r') as fpA:
        APIQueryDict['key'] = fpA.readline()
    # Adding all other inputs
    with open(fpath_input, 'r') as fpi:
        for line in fpi:
            inputData = line.split(":")
            APIQueryDict[inputData[0]] = inputData[1].replace(" ", "+").rstrip("\n")
    
    # Formatting the query and obtaining the response
    thisAPIQuery = genAPIQuery.format(**APIQueryDict)
    APIQueryResponse = requests.get(thisAPIQuery)
    
    print APIQueryResponse.json()

    return None

if __name__ == "__main__":
    getETTMatrixJson(GMAQueryPath, GMAKeyPath)