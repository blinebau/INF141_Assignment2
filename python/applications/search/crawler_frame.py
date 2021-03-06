import logging
import lxml
import bs4
from bs4 import BeautifulSoup
from datamodel.search.datamodel import ProducedLink, OneUnProcessedGroup, robot_manager
from spacetime_local.IApplication import IApplication
from spacetime_local.declarations import Producer, GetterSetter, Getter
from lxml import html,etree
from lxml.html.soupparser import fromstring
import re, os
from time import time
import requests

try:
    # For python 2
    from urlparse import urlparse, parse_qs
except ImportError:
    # For python 3
    from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)
LOG_HEADER = "[CRAWLER]"
url_count = (set() 
    if not os.path.exists("successful_urls.txt") else 
    set([line.strip() for line in open("successful_urls.txt").readlines() if line.strip() != ""]))
MAX_LINKS_TO_DOWNLOAD = 100 
'''
link_counter = 0
subdomain_track = dict()
outlink_track = ('', 0)
'''
@Producer(ProducedLink)
@GetterSetter(OneUnProcessedGroup)
class CrawlerFrame(IApplication):

    def __init__(self, frame):
        self.starttime = time()
        # Set app_id <student_id1>_<student_id2>...
        self.app_id = "49831189_94909076_72333079"
        # Set user agent string to IR W17 UnderGrad <student_id1>, <student_id2> ...
        # If Graduate studetn, change the UnderGrad part to Grad.
        self.UserAgentString = "IR W17 UnderGrad 49831189, 94909076, 72333079"
		
        self.frame = frame
        assert(self.UserAgentString != None)
        assert(self.app_id != "")
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def initialize(self):
        self.count = 0
        l = ProducedLink("http://www.ics.uci.edu/faculty/area/", self.UserAgentString)
        print l.full_url
        self.frame.add(l)

    def update(self):
        for g in self.frame.get(OneUnProcessedGroup):
            print "Got a Group"
            outputLinks, urlResps = process_url_group(g, self.UserAgentString)
            for urlResp in urlResps:
                if urlResp.bad_url and self.UserAgentString not in set(urlResp.dataframe_obj.bad_url):
                    urlResp.dataframe_obj.bad_url += [self.UserAgentString]
            for l in outputLinks:
                if is_valid(l) and robot_manager.Allowed(l, self.UserAgentString):
                    lObj = ProducedLink(l, self.UserAgentString)
                    self.frame.add(lObj)
        if len(url_count) >= MAX_LINKS_TO_DOWNLOAD:
            self.done = True

    def shutdown(self):
        #global link_counter
        #f = open('crawler_stats.txt', 'w')
        #f.write('Here are a list of the subdomains and how often they appear.')
        #for i in sorted(subdomain_track):
         #   try:
          #      f.write('\nThe url is ' + str(i) + ' which appears : '+ str(subdomain_track[i]) + " times.")
           # except UnicodeError:
            #    link_counter += 1
             #   print("Unicode Error for this url")
                
        
       # f.write("\nHere is the amount of invalid links that were found: " +str(link_counter))
        #f.write("\nThe page with the most outlinks is " + outlink_track[0]+ " with " + str(outlink_track[1]) + " links.")
        #f.close()
        print "downloaded ", len(url_count), " in ", time() - self.starttime, " seconds."
        pass

def save_count(urls):
    global url_count
    urls = set(urls).difference(url_count)
    url_count.update(urls)
    if len(urls):
        with open("successful_urls.txt", "a") as surls:
            surls.write(("\n".join(urls) + "\n").encode("utf-8"))

def process_url_group(group, useragentstr):
    rawDatas, successfull_urls = group.download(useragentstr, is_valid)
    save_count(successfull_urls)
    return extract_next_links(rawDatas), rawDatas
    
#######################################################################################
'''
STUB FUNCTIONS TO BE FILLED OUT BY THE STUDENT.
'''
def extract_next_links(rawDatas):
    outputLinks = list()
    '''
    rawDatas is a list of objs -> [raw_content_obj1, raw_content_obj2, ....]
    Each obj is of type UrlResponse  declared at L28-42 datamodel/search/datamodel.py
    the return of this function should be a list of urls in their absolute form
    Validation of link via is_valid function is done later (see line 42).
    It is not required to remove duplicates that have already been downloaded. 
    The frontier takes care of that.

    Suggested library: lxml
    '''
    #global subdomain_track
    #global outlink_track
    

    for resp in rawDatas:
        url = urlparse(resp.url)
        '''
        if url.netloc not in subdomain_track:
            subdomain_track[url.netloc] = 1
        else:
            subdomain_track[url.netloc] += 1
        if not url.query:
            resp.bad_url = true
        '''
        html = BeautifulSoup(resp.content, "lxml")
        html_links = html.find_all('a')
        for link in html_links:
            if link.get('href') is None:
                continue
            outputLinks.append(link.get('href'))
            '''
            if len(html_links) > len(outlink_track):
                outlink_track = (resp.url, len(html_links))
            '''
    return outputLinks

def is_valid(url):
    '''
    Function returns True or False based on whether the url has to be downloaded or not.
    Robot rules and duplication rules are checked separately.

    This is a great place to filter out crawler traps.
    '''
    #global link_counter
    parsed = urlparse(url)
    
    if parsed.scheme not in set(["http", "https"]):
        #link_counter +=1
        return False
    elif "calendar" in parsed.hostname:
        #link_counter +=1
        return False
    elif requests.get(url).status_code != requests.codes.ok:
        #link_counter +=1
        return False
    elif not parsed.query:
        #link_counter +=1
        return False
    try:
        return ".ics.uci.edu" in parsed.hostname \
            and not re.match(".*\.(css|js|bmp|gif|jpe?g|ico" + "|png|tiff?|mid|mp2|mp3|mp4"\
            + "|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf" \
            + "|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso|epub|dll|cnf|tgz|sha1" \
            + "|thmx|mso|arff|rtf|jar|csv"\
            + "|rm|smil|wmv|swf|wma|zip|rar|gz|h5)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
