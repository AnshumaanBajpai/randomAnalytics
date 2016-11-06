###############################################################################
## This script pulls the required data from GoogleMaps API. The aim is to
## obtain a set of estimated time of travel between destinations and origins
###############################################################################

## Importing the required objects and libraries
import time
import json
import pymongo
import crython
import requests
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate


## Setting up paths and some global constants
GMAQueryPath = r'./API_params.txt'
GMAKeyPath = r'./GMA_key.txt'
GMAKeyPathRev = r'./GMA_keyRev.txt'
genAPIQuery = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destinations}&departure_time={departure_time}&traffic_model={traffic_model}&key={key}"
passwdPath = r'./senderPasswd.txt'
with open(passwdPath, 'r') as spt:
    passwd = spt.readline()
## Path to MongoDB database in mLab
MONGODB_URI = 'mongodb://AnshumaanBajpaiIBM:'+passwd+'@ds041546.mlab.com:41546/trafficdata_ibm'


## Function to send the json object as an attachment to the email
def send_mail(sendFrom, sendTo, subject, text, attachmentString, attachmentName):
    '''
    Send the information from the traffic query as a json file attachment in an email
    
    @params
    sendFrom: senders email
    sendTo: receivers email
    subject: Email subject
    text: Email Text
    attachmentString: text of the attachment file
    attachmentName: name of the attachment file
    
    @returns
    None
    '''
    # Creating the message
    msg = MIMEMultipart()
    msg['From'] = sendFrom
    msg['To'] = COMMASPACE.join(sendTo)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))
    
    # Creating an attachment
    fileAttachment = MIMEApplication(attachmentString, Name=attachmentName)
    fileAttachment['Content-Disposition'] = 'attachment; filename="%s"' % attachmentName
    msg.attach(fileAttachment)
    
    # Providing logging details
    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.ehlo()
    smtp.starttls()

    # Adding the credentials and sending the email
    smtp.login('anshumaanbajpaiibm@gmail.com', passwd)
    smtp.sendmail(sendFrom, sendTo, msg.as_string())
    smtp.close()
    
    return None


## Function to convert the response from API into an list that can be loaded
## directly to a mongoDB database in appropriate format
def convertMatToDict(MatrixData):
    '''
    Converts the JSON data obtained from the API into a list of dictionaries that
    can easily be loaded into a database
    
    @params
    MatrixData: A JSON object as obtained from the Google Maps Distance Matrix API
    
    @returns
    dictData: A list of dictionaries where each data point is the complete
              information of one trip
    '''
    dictData = [] # The list that is returned
    
    # We iterate through all the origin distance values and populate the dictData
    for origin_id, origin_string in enumerate(MatrixData["origin_addresses"]):
        for destination_id, destination_string in enumerate(MatrixData["destination_addresses"]):
            this_data = MatrixData["rows"][origin_id]["elements"][destination_id]
            if this_data["status"]=="OK":             
                this_data_dict = {"origin":origin_string,
                                  "destination":destination_string,
                                  "duration(s)":this_data["duration"]["value"],
                                  "duration_in_traffic(s)":this_data["duration_in_traffic"]["value"],
                                  "distance(m)":this_data["distance"]["value"],
                                  "timestamp":MatrixData["queryTime"],
                                  "status":MatrixData["status"]}
                dictData.append(this_data_dict)
    
    return dictData


# Send the info to the MongoDB
def sendToMongoDB(dataList1, dataList2):
    '''
    Sends the list of dictionaries to the mongoDB database mentioned in
    global constants section of this script
    
    @params
    dataList: List of dictionaries that will be added to the mongoDB database
    
    @returns
    None
    '''
    # Connecting to the proper database
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.get_default_database()
    
    # First we'll add a collection to the database
    trips = db['trips']
    # Insert the data
    trips.insert(dataList1)
    trips.insert(dataList2)
    # Close the connection
    client.close()

    
## Function to send the data query and obtain the results
## Fires twice a minute
@crython.job(fpath_input=GMAQueryPath, fpath_API=GMAKeyPath, fpath_APIRev=GMAKeyPathRev, minute=range(5, 65, 15), second=[0])
def getETTMatrixJson(fpath_input, fpath_API, fpath_APIRev):
    '''
    Obtains the Estimated Trip Time matrix for a given API query. The API
    query is generated using the data from an input file. The response is
    converted to a list of dictionary format and sent to an external MongoDB
    database
    
    @params
    fpath_input: Path to the input file which has the basic parameters for API query
    fpath_API: Path to the API Key which is hidden and not shared with everyone
    
    @return
    None
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
    
    # Creating another dictionary for the queries in the reverse direction
    # Due to constraints on the number of free queries that we have from Google API,
    # We are unable to work with full n*n matrix and we work only with two matrices,
    # one of which is n*2 and the other is 2*n
    APIQueryDictRev = {}
    for key in APIQueryDict:
        if key == "origin":
            APIQueryDictRev[key] = APIQueryDict["destinations"]
        elif key == "destinations":
            APIQueryDictRev[key] = APIQueryDict["origin"]
        else:
            APIQueryDictRev[key] = APIQueryDict[key]
    # Adding the Rev API key
    # We use a different key so as to have more number of queries available to us
    with open(fpath_APIRev, 'r') as fpARev:
        APIQueryDictRev['key'] = fpARev.readline()
    
    # Formatting the queries and obtaining the response
    thisAPIQuery = genAPIQuery.format(**APIQueryDict)
    thisAPIQueryRev = genAPIQuery.format(**APIQueryDictRev)

    queryTime = time.strftime("%m-%d-%Y_%H:%M:%S_%A")
    ETTMatrix = requests.get(thisAPIQuery).json() #ETT: Estimated Trip Time
    
    queryTimeRev = time.strftime("%m-%d-%Y_%H:%M:%S_%A")
    ETTMatrixRev = requests.get(thisAPIQueryRev).json()

    ETTMatrix['queryTime'] = queryTime
    ETTMatrixRev['queryTime'] = queryTimeRev

    #outFileName = time.strftime("%Y%m%d-%H%M%S")+'.json'
    #outFileNameRev = time.strftime("%Y%m%d-%H%M%S")+'Rev.json'

    # Convert ETTMatrix into a dictionary with database friendly format
    ETTDict = convertMatToDict(ETTMatrix)

    ETTDictRev = convertMatToDict(ETTMatrixRev)

    # Send the data to AWS mongoDB database
    print "Sending to Database......."
    sendToMongoDB(ETTDict, ETTDictRev)
    
    # Sending the data as an email attachment
#    send_mail(sendFrom="anshumaanbajpaiibm@gmail.com", sendTo=["anshumaanbajpaiibm@gmail.com"],
#              subject="TrafficData", text="From anshumaanbajpaiibm@gmail.com",
#              attachmentString=json.dumps(ETTMatrix, indent=1), attachmentName=outFileName)
#    send_mail(sendFrom="anshumaanbajpaiibm@gmail.com", sendTo=["anshumaanbajpaiibm@gmail.com"],
#              subject="TrafficData", text="From anshumaanbajpaiibm@gmail.com",
#              attachmentString=json.dumps(ETTMatrixRev, indent=1), attachmentName=outFileNameRev)
        
    return None

# Running the cronjob when called directly
if __name__ == "__main__":
    crython.tab.run()
