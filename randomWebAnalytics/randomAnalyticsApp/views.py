###############################################################################
## This is a handler that responds to the requests from browsers
__author__ = "Anshumaan Bajpai"
__email__ = "bajpai.anshumaan@gmail.com"


## Importing the required objects and libraries
from randomAnalyticsApp import app, utils_ia
from flask import render_template, request, jsonify
import os
import json
from wordcloud import WordCloud, STOPWORDS

## Some Constant values
fpath_WMAPI = r'./randomAnalyticsApp/WorldMap_key.txt'
cached_files = r'./cached_files/'
scripts_path = r'./scripts/'
cached_images = r'./randomAnalyticsApp/static/img/cached_images/'
server_images = os.path.join('..','static','img','cached_images')
cached_traffic = r'./randomAnalyticsApp/static/trafficData/'

###############################################################################
## Defining Web address links

###############################################################################
## Front page/Index
@app.route('/')
@app.route('/index/')
def index():
    '''
    Function that renders the basic front page of the website

    @params
    None
    
    @returns
    Renders the base webpage for this application
    '''
    return render_template('index.html')
    
###############################################################################
## Instagram analysis section
###############################################################################
@app.route('/instanalyze/')
def instanalyze():
    '''
    Function that renders the basic front page of the website

    @params
    None
    
    @returns
    Renders the base webpage for this application
    '''

    return render_template('instaHome.html')

# Defining the results page
@app.route('/instaResult/', methods=['POST'])
def instaResult():
    '''
    Function takes in the submitted form from "instaHome.html" and performs the
    instagram analysis for the given query and present the results
    
    @params
    None
    
    @returns
    Renders the Webpage with the results for a given query
    '''
    # Extracting the form queries
    instaquery = request.form['instaquery']
    emailId = request.form['emailId']
    full_name = request.form['full_name']
    
    # Test if instaquery is a hashtag or a username:
    instaquery_type = utils_ia.username_or_hashtag(instaquery)
    
    # Check if the query has been performed before
    instaquery_exists = False
    instaquery_dir = os.path.join(cached_files, instaquery_type+'s',instaquery[1:])
    if instaquery_type != "TBD":
        instaquery_key = instaquery[1:]
        if os.path.isdir(instaquery_dir):
            instaquery_exists = True
    #else:
    #    process instaquery and save the results in instaquery_dir

    
    calculated_dir = os.path.join(cached_images, instaquery_type+'s',instaquery[1:])
    server_calculated_dir = os.path.join(server_images, instaquery_type+'s',instaquery[1:])    
    ###########################################################################
    ## Generating plots and other files from raw and annotated data if new query
    if os.path.isdir(calculated_dir):
        pass
    else:
        utils_ia.gen_basicStats_wordcloud(instaquery_dir, instaquery_key, instaquery_type)
        utils_ia.create_tSNE_grid(instaquery_dir, instaquery_key, instaquery_type)
    
    # Basics tab
    with open(os.path.join(calculated_dir, 'profile.json'), 'r') as basic_data:
        profile=json.load(basic_data)
    
    # Text tab
    gen_source = os.path.join(server_calculated_dir, 'wordcloud_gen_words.png').replace("\\","/")
    h_source = os.path.join(server_calculated_dir, 'wordcloud_h_tags.png').replace("\\","/")
    u_source = os.path.join(server_calculated_dir, 'wordcloud_u_names.png').replace("\\","/")
    cloudSource = {'gen_source':gen_source, 'h_source':h_source, 'u_source':u_source}
    

    # Colors tab
    colorPalette_src = utils_ia.gen_color_palette(instaquery_dir, instaquery_key, instaquery_type)
    with open(os.path.join(calculated_dir, 'tSNE_data.json'), 'r') as tsd:
        tSNE_data=json.load(tsd)
    tSNE_result = [i for i in tSNE_data["grids"] if i['marker']!="None"]
    
    ## rendering the page
    return render_template('instaResult.html',
                           instaquery=instaquery, #title for the result
                           profile=profile, # basics tab
                           cloudSource=cloudSource, # data for text analysis
                           colorPalette_src=colorPalette_src, # data for color tab
                           results=tSNE_result,
                           tSNE_data=tSNE_data)

    
    
###############################################################################
## Traffic analysis section
###############################################################################
@app.route('/traffic/')
def traffic():
    '''
    Function that renders the traffic analysis aspect of this web application

    @params
    None
    
    @returns
    Renders the traffic webpage for this application
    '''
    # Obtain the Google Map Key
    with open(fpath_WMAPI, 'r') as fpWMA:
        WMPasswd = fpWMA.readline()

    return render_template('traffic.html', GMAPI=WMPasswd)
    
    
@app.route('/getCityData/')
def getCityData():
    '''
    Function returns the data for a queried city
    
    @params
    None: Cityname is passed as an argument in the request object
    
    @returns
    Sends the data to the javascript function placeMarker in traffic.html
    '''
    cityname = request.args.get('cityname', 0, type=str)
    cityFileLoc = os.path.join(cached_files, "traffic", cityname)
    # Generating processed data for city if not generated already
    processedCityDataLoc = os.path.join(cached_traffic, cityname)
    if os.path.isdir(processedCityDataLoc):
        pass
    else:
        utils_ia.genCityData(cityFileLoc, cityname)
    
    # Loading the markers and all the location codes
    allCityProFiles = os.listdir(processedCityDataLoc)
    allCityProFiles.remove("codes.json")
    
    with open(os.path.join(processedCityDataLoc, "codes.json")) as cj:
        locCodes = json.load(cj)

    # Converting the location code dictionary to a list where each element is a dictionary with
    # all information about the given point
    locationList = []
    keysList = locCodes.keys()
    for locId in range(len(locCodes['code'])):
        locationList.append({"code":locCodes['code'][locId], "location":locCodes['location'][locId],
                             "geoCode":locCodes['geoCode'][locId], "name":locCodes['name'][locId], "color":locCodes['color'][locId]})
       
    return jsonify(locationList)
    
   
@app.route('/getThisRoute/')
def getThisRoute():
    '''
    Function returns the data for a specific requested route
    @params
    None: pt1C, pt2C, pt1V, pt2V are passed as the argument for the request and are 
    the point codes and names for the two points that have been selected by the user
    
    @returns
    Send the data for the requested route to the javascript function obtainAnalysisData in traffic.html
    '''
    # Location codes
    pt1Cd = request.args.get('pt1C', 0, type=str)
    pt2Cd = request.args.get('pt2C', 0, type=str)
    # Location names
    pt1Vl = request.args.get('pt1V', 0, type=str)
    pt2Vl = request.args.get('pt2V', 0, type=str)
    # City
    cityname = request.args.get('citygTR', 0, type=str)
    
    # Obtain the data in the required form
    # Read data for from pt1 to pt2
    cityDataDir = os.path.join(cached_traffic, cityname)
    file1to2 = os.path.join(cityDataDir, pt1Cd+"-"+pt2Cd+".json")
    
    heatMapData = utils_ia.cityHeatMapData(file1to2)
        
    data2ret = {"origin":pt1Vl, "dest":pt2Vl, "data":heatMapData}
    
    return jsonify(data2ret)