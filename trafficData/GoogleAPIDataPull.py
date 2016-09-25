###############################################################################
## This script pulls the required data from GoogleMaps API. The aim is to
## obtain a set of estimated time of travel between destinations and origins


## Importing the required objects and libraries
import os
import time
import json
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
genAPIQuery = "https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destinations}&departure_time={departure_time}&traffic_model={traffic_model}&key={key}"


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
    with open("senderPasswd.txt", 'r') as spt:
        passwd = spt.readline()

    # Adding the credentials and sending the email
    smtp.login('anshumaanbajpaiibm@gmail.com', passwd)
    smtp.sendmail(sendFrom, sendTo, msg.as_string())
    smtp.close()
    
    return None

## Function to send the data query and obtain the results
## Fires twice a minute
@crython.job(fpath_input=GMAQueryPath, fpath_API=GMAKeyPath, minute=range(0,60,30))
def getETTMatrixJson(fpath_input, fpath_API):
    '''
    Obtains the Estimated Trip Time matrix for a given API query. The API
    query is generated using the data from an input file
    
    @params
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
    queryTime = time.strftime("%m-%d-%Y_%H:%M:%S_%A")
    outFileName = time.strftime("%Y%m%d-%H%M%S")+'.json'
    
    ETTMatrix = requests.get(thisAPIQuery).json() #ETT: Estimated Trip Time
    ETTMatrix['queryTime'] = queryTime
    # Sending the data as an email attachment
    send_mail(sendFrom="anshumaanbajpaiibm@gmail.com", sendTo=["anshumaanbajpaiibm@gmail.com"],
              subject="TrafficData", text="From anshumaanbajpaiibm@gmail.com",
              attachmentString=json.dumps(ETTMatrix, indent=1), attachmentName=outFileName)
    
    return None

# Running the cronjob when called directly
if __name__ == "__main__":
    crython.tab.run()