###############################################################################
## This is the basic file that calls and runs the entire applications


## Importing the Flask object to create an application variable
from flask import Flask
app = Flask(__name__)


## Import the views from the application folder
from randomAnalyticsApp import views
