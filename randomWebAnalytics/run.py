#!flask/Scripts/python
from randomAnalyticsApp import app

#Run the app only if called directly
if __name__=='__main__':
    app.run(port=9080, debug=True)