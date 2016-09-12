###############################################################################
## This is a handler that responds to the requests from browsers
__author__ = "Anshumaan Bajpai"
__email__ = "bajpai.anshumaan@gmail.com"


## Importing the required objects and libraries
from randomAnalyticsApp import app


###############################################################################
## Defining Web address links

@app.route('/')
@app.route('/index')
def index():
    '''
    Function that renders the basic front page of the website

    @params
    None
    
    @returns
    Renders the webpage
    '''
    return "Hello world!"