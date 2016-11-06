# Spider to crawl instagram for a given username
# Can be used as a sample module for a more extensive spider

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
class instagramProfileItem(scrapy.Item):
    date_crawled = scrapy.Field()
    is_private = scrapy.Field()
    username = scrapy.Field()
    fullname = scrapy.Field()
    bio = scrapy.Field()
    website = scrapy.Field()
    profile_picture = scrapy.Field()
    total_posts = scrapy.Field()
    followers = scrapy.Field()
    following = scrapy.Field()
    images = scrapy.Field()
    image_urls = scrapy.Field()
    

#################################################
# Defining the spider
class instagramProfileSpider(scrapy.Spider):
    '''
    scrapy crawl instagram_user
    ''' 
    name = "instagram_user"
    allowed_domains = ["instagram.com"]
    date_crawled = datetime.strftime(datetime.today(),'%Y-%m-%d')
    user2crawl = "eliesaabworld"
    start_urls = ["https://www.instagram.com/"+user2crawl+"/"]


    def parse(self, response):
        # Add the code here and edit the start_urls if multiple hashtags
        # are to be explored
        yield scrapy.Request(response.url, callback=self.parse_user)


    def parse_user(self, response):
        '''
        Extracts data for an instagram user
        Input:
            response--Response from a instagram user page of type:
                      https://www.instagram.com/nike/
        Output:
            instagramProfileItem
        '''
        user_instagram_url = response.url
        javascript = "".join(response.xpath('//script[contains(text(), "sharedData")]/text()').extract())
        json_data = ujson.loads("".join(re.findall(r'window._sharedData = (.*);', javascript)))
        user_dictionary = json_data['entry_data']['ProfilePage'][0]['user']

        item = instagramProfileItem()
        item['date_crawled'] =  self.date_crawled
        item['is_private'] = self.try_catch(user_dictionary, 'is_private')
        item['username'] = self.try_catch(user_dictionary, 'username')
        item['fullname'] = self.try_catch(user_dictionary, 'full_name')
        item['bio'] = self.try_catch(user_dictionary, 'biography')
        item['website'] = self.try_catch(user_dictionary, 'external_url')
        item['profile_picture'] =  self.try_catch(user_dictionary, 'profile_pic_url')
        item['total_posts'] = self.try_catch(user_dictionary, 'media')
        item['followers'] = self.try_catch(user_dictionary, 'followed_by')
        item['following'] = self.try_catch(user_dictionary, 'follows')
        for key_val in ['total_posts', 'followers', 'following']:
            if item[key_val] != 'NA':
                item[key_val] = item[key_val]['count']

        # Collecting all the images is a bit tricky. Instagram has infinite
        # scrolling with page loading more and more as we scroll down and
        # also when we click "Load More" button. This one isn't as straight
        # forward as Vogue_UK where we had a query that we could use       
        item['images'] = []
        image_ids = []
        
        # Data from first display page
        data_first_page = self.extract_user_data(user_dictionary['media']['nodes'])
        item['images'] += data_first_page['image_details']
        image_ids += data_first_page['im_ids']

        # At this stage we only have the images from the first page of the site
        # We need the image ids to be able to iteratively get all the images
        # The image with the least id value when used in a url as 
        # username/?max_id=..... leads us to the next page
        while len(image_ids) < item['total_posts']:
            url_to_scrape = urlparse.urljoin(user_instagram_url, '?max_id='+str(sorted(image_ids)[0]))
            new_images, new_image_ids = self.get_more_images(url_to_scrape)
            item['images'] += new_images
            image_ids += new_image_ids

        item['image_urls'] = [img['url'] for img in item['images']]
        
        yield item    
        
        
    def get_more_images(self, url2scrape):
        '''
        Extracts data from subsequent pages of an instagram user
        Input:
            url2scrape--url from a user with images
        Output:
            (image_details, image_ids)
        '''
        response_obj = requests.get(url2scrape)
        javascript_n = "".join(Selector(text=response_obj.text).xpath('//script[contains(text(), "sharedData")]/text()').extract())
        json_data_n = ujson.loads("".join(re.findall(r'window._sharedData = (.*);', javascript_n)))
        user_dictionary_n = json_data_n['entry_data']['ProfilePage'][0]['user']

        new_data = self.extract_user_data(user_dictionary_n['media']['nodes'])
        new_imgs = new_data['image_details']
        new_img_ids = new_data['im_ids']
            
        return (new_imgs, new_img_ids)


    def extract_user_data(self, image_data_dict):
        '''
        Extracts info to be loaded into instagramProfileItem['images']
        Input:
            image_data_dict--a list of dictionary objects containing details about the images
        Output:
            A dictionary with image_details and image_ids as key
        '''
        image_details = []
        im_ids = []
        for img_dict in image_data_dict:
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
            im_ids.append(int(img_dict['id']))
        
        return {'image_details': image_details, 'im_ids': im_ids}


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
