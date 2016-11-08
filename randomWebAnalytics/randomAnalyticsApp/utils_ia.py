# File to define all the functions

# Importing the required libraries and models
import os
import json
import string
import collections
import numpy as np
from PIL import Image
from scipy.misc import imread
from operator import itemgetter
from matplotlib import pyplot as plt
import matplotlib.patches as mpatches
from wordcloud import WordCloud, STOPWORDS
from flask import render_template, request


###############################################################################
##      Some basic tests to check the proper working of the script           ##
###############################################################################
cached_files = r'./cached_files/'
scripts_path = r'./scripts/'
cached_images = r'./randomAnalyticsApp/static/img/cached_images/'
server_images = os.path.join('..','static','img','cached_images')


###############################################################################
##           Analysis based functions are defined in this section            ##
###############################################################################
def username_or_hashtag(q_str):
    '''
    Function that tests if its a username or a hashtag
    If the first letter is # then we treat it as a hashtag, if the first
    letter is @ then we treat it as a username. If the first letter is
    neither of above, we first look into username and then into hashtag.
    If no data is found, we first run spider treating it as a username
    and if the username does not exist, we do a hashtag based search
    @params
    q_str: string to be tested for username/hashtag
    '''
    f_letter = q_str[0]
    if f_letter == "#":
        return "hashtag"
    elif f_letter == "@":
        return "username"
    else:
        return "TBD"


def gen_basicStats_wordcloud(json_fdir, json_query, query_type):
    '''
    Function that prepares wordcloud plots from a given
    instaquery.json
    @params
    json_fdir: cached directory that contains data for the query
    json_query: query that is searched
    query_type: whether hashtag or username
    @output
    Generates 3 word clouds: One each for hashtags, usernames
    and other words
    '''
    # Loading the data
    json2open = os.path.join(json_fdir, json_query+".json")
    with open(json2open, 'r') as j2o:
        query_data = json.load(j2o)[0]
    
    # Extracting all the basic information from the profile
    query_images = query_data['images']
    
    # Captions have a lot of hashtags, usernames and normal words
    # We split the captions into 3 categories
    word_cat = {'h_tags':[], 'u_names':[], 'gen_words':[]}
    image_details_list = []
    
    # A string with all the punctuation marks
    p_marks = string.punctuation
    p_marks = p_marks.replace("#","")
    p_marks = p_marks.replace("@","")
    
    # Categorizing the words
    for image in query_images:
        image_details_list.append([image['url'], image['likes'], image['comments']])
        tmp_caption = image['caption']
        tmp_caption = tmp_caption.encode('utf-8').translate(string.maketrans("",""), p_marks)
        all_words = tmp_caption.split()
        for word in all_words:
            if word[0]=="#":
                word_cat['h_tags'].append(word)
            elif word[0]=="@":
                word_cat['u_names'].append(word)
            else:
                word_cat['gen_words'].append(word)
    
    # Now we need to create word clouds from the obtained wordlists
    cloud_mask = np.array(Image.open('./randomAnalyticsApp/static/img/cloud_mask.png'))
    
    server_image_loc = os.path.join(cached_images, query_type+'s', json_query)
    if not os.path.isdir(server_image_loc):
        os.mkdir(server_image_loc)
    
    for key, value in word_cat.iteritems():
        wc = WordCloud(
                       stopwords=STOPWORDS, 
                       background_color='white',
                       width=1800, height=1400,
                       mask=cloud_mask
                       ).generate((" ").join(value))
        fig, ax = plt.subplots()
        plt.imshow(wc, extent=(0,1,1,0))
        ax.xaxis.set_major_locator(plt.NullLocator())
        ax.yaxis.set_major_locator(plt.NullLocator())
        plt.axis("tight")
        plt.axis("off")
        plt.savefig(os.path.join(server_image_loc,'wordcloud_'+key+'.png'),
                    dpi=600, bbox_inches='tight', pad_inches = 0)
        plt.close()
    
    # Generate a list with dictionary items for plotting the histograms for likes
    # and comments using d3.js 
    d3_data = [{'url':img[0], 'likes':img[1], 'comments':img[2]} for img in image_details_list]
    sort_likes_5 = sorted(image_details_list, key=itemgetter(1), reverse=True)[0:6]
    sort_comments_5 = sorted(image_details_list, key=itemgetter(2), reverse=True)[0:6]
    likes_list = [img[1] for img in image_details_list]
    comments_list = [img[2] for img in image_details_list]
    total_likes = np.sum(likes_list)
    total_comments = np.sum(comments_list)
    avg_likes = float(total_likes)/query_data['total_posts']
    avg_comments = float(total_comments)/query_data['total_posts']
    # Creating a dictionary to save for cache
    profile_basics = {'last_crawled':query_data['date_crawled'], 'total_posts':query_data['total_posts'],
                      'following':query_data['following'], 'followers':query_data['followers'],
                      'profile_pic':query_data['profile_picture'], 'fullname':query_data['fullname'],
                      'username':query_data['username'], 'total_likes':total_likes,
                      'avg_likes':int(avg_likes), 'total_comments':total_comments, 'avg_comments':int(avg_comments),
                      'bio':query_data['bio'], 'l_list':likes_list, 'c_list':comments_list,
                      'top_liked':sort_likes_5, 'top_commented':sort_comments_5,
                      'd3_data':d3_data}
    
    # Saving the profile basics in cache
    with open(os.path.join(server_image_loc,'profile.json'), 'w') as pb:
        pb.write(json.dumps(profile_basics, indent=1))

    return None
    
    
def gen_color_palette(json_fdir, json_query, query_type):
    """ Visualize the color palette
    @params
    json_fdir: cached directory that contains data for the query
    json_query: query that is searched
    query_type: whether hashtag or username
    @output
    Generates a color palette
    """
    # Loading the data
    json2open = os.path.join(json_fdir, json_query+"_colors.json")
    with open(json2open, 'r') as j2o:
        palette = json.load(j2o)["km_clus"]
    # Create a dictionary that will be fed to the html template to display the color palette
    palette = {",".join([str(int(i)) for i in color]):tuple([int(i) for i in color]) for color in palette}
    return palette


def create_tSNE_grid(json_fdir, json_query, query_type):
    '''
    Function that prepares wordcloud plots from a given
    instaquery.json
    @params
    json_fdir: cached directory that contains data for the query
    json_query: query that is searched
    query_type: whether hashtag or username
    @output
    Generate the data that can be directly plotted on the tSNE plot
    '''
    # Loading the data
    json2open = os.path.join(json_fdir, json_query+"_colors.json")
    with open(json2open, 'r') as j2o:
        query_colordata = json.load(j2o)
    
    tSNEx = query_colordata['t_SNEx']
    tSNEy = query_colordata['t_SNEy']
    rgb = query_colordata['rgb']
    likes = query_colordata['likes']
    comments = query_colordata['comments']
    urls = query_colordata['img_url']
    colnames = query_colordata['colorname']
    
    tSNEx_min = np.min(tSNEx)
    tSNEx_max = np.max(tSNEx)
    tSNEy_min = np.min(tSNEy)
    tSNEy_max = np.max(tSNEy)

    #print query_colordata.keys()
    #print "------------"
    #print tSNEx_min, tSNEx_max
    #print tSNEy_min, tSNEy_max
    
    tSNEx_grid = np.linspace(np.floor(tSNEx_min), np.ceil(tSNEx_max), 16, endpoint=True)
    tSNEy_grid = np.linspace(np.floor(tSNEy_min), np.ceil(tSNEy_max), 16, endpoint=True)
    #print 'tSNExgrid', tSNEx_grid
    #print 'tSNEygrid', tSNEy_grid    
    
    n_grids=(len(tSNEx_grid)-1)*(len(tSNEy_grid)-1)
    #print 'n_grids', n_grids
    
    grid_data_array = []
    
    for gr in range(n_grids):
        grid_data_array.append({"marker":"None","grid_points":[], "id":gr})
        gr_xid = gr%(len(tSNEx_grid)-1)
        gr_yid = int(gr/(len(tSNEx_grid)-1))
        #print gr, gr_xid, gr_yid
        tIDs_found = []
        for tID in range(len(tSNEx)):
            if tSNEx_grid[gr_xid]<tSNEx[tID]<tSNEx_grid[gr_xid+1] and tSNEy_grid[gr_yid]<tSNEy[tID]<tSNEy_grid[gr_yid+1]:
                if grid_data_array[gr]["marker"]=="None":
                    grid_data_array[gr]["marker"] = {"tSNEx":tSNEx[tID],"tSNEy":tSNEy[tID],
                                                         "rgb":rgb[tID], "colname":colnames[tID],
                                                         "likes":likes[tID], "comments":comments[tID],
                                                         "url":urls[tID]}
                grid_data_array[gr]["grid_points"].append({"tSNEx":tSNEx[tID],"tSNEy":tSNEy[tID],
                                                               "rgb":rgb[tID], "colname":colnames[tID],
                                                               "likes":likes[tID], "comments":comments[tID],
                                                               "url":urls[tID]}
                                                               )
                tIDs_found.append(tID)
        
        # remove all the iDs that have been alloted
        tSNEx = [x for i,x in enumerate(tSNEx) if i not in tIDs_found]
        tSNEy = [x for i,x in enumerate(tSNEy) if i not in tIDs_found]
        rgb = [x for i,x in enumerate(rgb) if i not in tIDs_found]
        likes = [x for i,x in enumerate(likes) if i not in tIDs_found]
        comments = [x for i,x in enumerate(comments) if i not in tIDs_found]
        urls = [x for i,x in enumerate(urls) if i not in tIDs_found]
        colnames = [x for i,x in enumerate(colnames) if i not in tIDs_found]
    
    total_points = 0
    total_markers=0
#    for key,value in grid_data_dict.iteritems():
#        print key, value['marker']
#        if value['marker'] != None:
#            total_markers += 1
#       total_points += len(value['grid_points'])
#    print total_points
#    print total_markers

    # A dictionary that can be directly plotted using Plotly
    plotlyDict = {'tSNEx':[], 'tSNEy':[], 'tSNErgbcol':[], 'tSNEcolname':[],
                  'tSNElikes':[], 'tSNEcomments':[], 'numGridPts':[], 'gridPts':[], 'text':[]}
    for idx, valx in enumerate(grid_data_array):
        if valx['marker'] != "None":
            plotlyDict['tSNEx'].append(valx['marker']['tSNEx'])
            plotlyDict['tSNEy'].append(valx['marker']['tSNEy'])
            plotlyDict['tSNErgbcol'].append("rgb("+",".join([str(i) for i in valx['marker']['rgb']])+")")
            plotlyDict['tSNEcolname'].append(valx['marker']['colname'])
            plotlyDict['tSNElikes'].append(valx['marker']['likes'])
            plotlyDict['tSNEcomments'].append(valx['marker']['comments'])
            plotlyDict['numGridPts'].append(len(valx['grid_points']))
            plotlyDict['gridPts'].append(valx['grid_points'])
            plotlyDict['text'].append("Color:"+valx['marker']['colname']+'<br>'+"Images:"+str(len(valx['grid_points'])))

    server_image_loc = os.path.join(cached_images, query_type+'s', json_query)
    if not os.path.isdir(server_image_loc):
        os.mkdir(server_image_loc)
    
    # Saving the profile basics in cache
    with open(os.path.join(server_image_loc,'tSNE_data.json'), 'w') as tsd:
        tsd.write(json.dumps({"grids":grid_data_array, "x_range":[np.floor(tSNEx_min), np.floor(tSNEx_max)],
                                                      "y_range":[np.floor(tSNEy_min), np.floor(tSNEy_max)],
                                                      "plotlyData":plotlyDict}, indent=1))
    
    return None