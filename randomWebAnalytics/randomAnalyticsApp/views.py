###############################################################################
## This is a handler that responds to the requests from browsers
__author__ = "Anshumaan Bajpai"
__email__ = "bajpai.anshumaan@gmail.com"


## Importing the required objects and libraries
from randomAnalyticsApp import app
from flask import render_template


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
    Renders the base webpage for this application
    '''
    return render_template('base.html')