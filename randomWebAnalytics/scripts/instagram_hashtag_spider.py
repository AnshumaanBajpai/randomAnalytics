# Spider to crawl instagram for a given hashtag
# Can be used as a sample module for a more extensive spider

# Reported Error:
# 1) I obtained the following error sometimes
#   Error: [Errno 10051] A socket operation was attempted to an unreachable network.

__author__ = "Anshumaan Bajpai (intern)"

# Importing the required libraries
import re
import ujson
import scrapy
import requests
import urlparse
import unicodedata
import dateutil.parser
from datetime import datetime
from scrapy.selector import Selector


#################################################
# Defining the item
class instagramHashtagItem(scrapy.Item):
    date_crawled = scrapy.Field()
    total_posts = scrapy.Field()
    hashtag_name = scrapy.Field()
    # images is a list with dictionary objects having
    # detailed info about each image
    images = scrapy.Field()
    
    # image_urls only has image_urls to be used for downloading the images
    image_urls = scrapy.Field()
    

#################################################    
# Defining the spider
class instagramHashtagSpider(scrapy.Spider):
    '''
    scrapy crawl instagram_hashtag
    '''
    name = "instagram_hashtag"
    allowed_domains = ["instagram.com"]
    date_crawled = datetime.strftime(datetime.today(),'%Y-%m-%d')
    
    # n_images is the approximate number of images to be downloaded.
    # To get all the images set this number to a large number greater
    # than the actual no. of images
    n_images = 5000000
    ht2crawl = "eliesaab" # hashtag to crawl
    start_urls = ["https://www.instagram.com/explore/tags/"+ht2crawl+"/"]
    

    def parse(self, response):
        # Add the code here and edit the start_urls if multiple hashtags
        # are to be explored
        yield scrapy.Request(response.url, callback=self.parse_hashtag)
        

    def parse_hashtag(self, response):
        '''
        Extracts all the images for a given hashtag
        Input:
            response--Response from an instagram hyperlink
        Output:
            instagramHashtagItem
        '''
        hashtag_instagram_url = response.url
        javascript = "".join(response.xpath('//script[contains(text(), "sharedData")]/text()').extract())
        json_data = ujson.loads("".join(re.findall(r'window._sharedData = (.*);', javascript)))
        hashtag_dictionary = json_data['entry_data']['TagPage'][0]['tag']
        
        # Populating the item
        item = instagramHashtagItem()
        item['date_crawled'] = self.date_crawled
        item['total_posts'] = self.try_catch(hashtag_dictionary, 'media')
        item['hashtag_name'] = self.try_catch(hashtag_dictionary, 'name')
        
        for key_val in ['total_posts']:
            if item[key_val] != 'NA':
                item[key_val] = item[key_val]['count']

        # Collecting all the images is a bit tricky. Instagram has infinite
        # scrolling with page loading more and more as we scroll down and
        # also when we click "Load More" button. This one isn't as straight
        # forward as Vogue_UK where we had a query that we could use

        # As we load more pages, the display always has a top_posts section
        # that remains unchanged as we load more images. And there is recent
        # posts section that updates every time we follow 'Load More' button
        item['images'] = []
        
        # Data from first display_page
        item['images'] += self.extract_nodes_data(hashtag_dictionary['top_posts']['nodes'])['image_details']
        item['images'] += self.extract_nodes_data(hashtag_dictionary['media']['nodes'])['image_details']

        # end_cursor is the keyword that we need to move onto the next page
        end_cursor = hashtag_dictionary['media']['page_info']['end_cursor']
        has_next_page = hashtag_dictionary['media']['page_info']['has_next_page']
        
        # Now we need to iterate as long as we have 'has_next_page' as True and 
        # number of images is less than what we need
        while has_next_page==True and len(item['images'])<self.n_images:
            url_to_scrape = urlparse.urljoin(hashtag_instagram_url, '?max_id='+end_cursor)
            new_images, end_cursor, has_next_page = self.get_more_images(url_to_scrape)
            item['images'] += new_images
            #print 'has_next_page: ', has_next_page, 'end_cursor: ', end_cursor

        item['image_urls'] = [img['url'] for img in item['images']]
        
        yield item
            
        
    def get_more_images(self, url2scrape):
        '''
        Extracts data from subsequent pages of an instagram hashtag
        Input:
            url2scrape--url from a hashtag with images
        Output:
            (image_details, end_cursor, has_next_page)
        '''
        response_obj = requests.get(url2scrape)
        javascript_n = "".join(Selector(text=response_obj.text).xpath('//script[contains(text(), "sharedData")]/text()').extract())
        json_data_n = ujson.loads("".join(re.findall(r'window._sharedData = (.*);', javascript_n)))
        hashtag_dictionary_n = json_data_n['entry_data']['TagPage'][0]['tag']

        new_imgs = self.extract_nodes_data(hashtag_dictionary_n['media']['nodes'])['image_details']
        new_end_cursor = hashtag_dictionary_n['media']['page_info']['end_cursor']
        new_has_next_page = hashtag_dictionary_n['media']['page_info']['has_next_page']
            
        return (new_imgs, new_end_cursor, new_has_next_page)
            

    def extract_nodes_data(self, nodes):
        '''
        Extracts info to be loaded into instagramHashtagItem['images']
        Input:
            nodes--a list of dictionary objects containing details about the images
        Output:
            A dictionary with image_details list
        '''
        image_details = []
        for img_dict in nodes:
            img_summary = {}
            img_summary['comments'] = self.try_catch(img_dict, 'comments')
            img_summary['caption'] = self.try_catch(img_dict, 'caption')
            img_summary['likes'] = self.try_catch(img_dict, 'likes')
            img_summary['date'] = self.try_catch(img_dict, 'date')
            img_summary['id'] = self.try_catch(img_dict, 'id')
            img_summary['url'] = self.try_catch(img_dict, 'display_src')
            img_summary['is_video'] = self.try_catch(img_dict, 'is_video')
            if str(img_summary['is_video']) == 'True':
                img_summary['video_views'] = self.try_catch(img_dict, 'video_views')
            
            for key_val in ['comments', 'likes']:
                if img_summary[key_val] != 'NA':
                    img_summary[key_val] = img_summary[key_val]['count']
                    
            image_details.append(img_summary)
        
        return {'image_details': image_details}


    def try_catch(self, dict_obj, key):       
        '''
        A try catch block useful for populating the image list.
        Input:
            dict_obj--The dictionary object containing all the
            information
            key--key that we are looking for in the given directory
        Output:
            a string with the appropriate value if the key is available
            and "NA" if not
        '''
        try:
            return dict_obj[key]
        except (KeyError, NameError):
            return 'NA'
