import time
import requests
import re
import xml.sax.saxutils as sax_utils


disallowed_patterns = [
    r'.css',
    r'/#',
    r'.png',
    r'.jpg',
    r'/images',
    r'.jpeg',
    r'/svg',
    r'sentry',
    r'/api-v2',
    r'/shipping',
    r'/payment',
    r'/search\?q=.*',
    r'/profile.*',
    r'/.*utm_.*',
    r'/product/comment/.*',
    r'/rss',
    r'/services',
    r'/temp',
    r'/testservice',
    r'/upload',
    r'/web%20references',
    r'/bin-copy',
    r'/.*product/dkpi-.*',
    r'/cart/.*',
    r'/waiting/.*',
    r'/checkout/.*',
    r'/addcomment/.*',
    r'/compare/.*',
    r'/imagecompare/.*',
    r'/invalidrequest',
    r'/user/.*',
    r'/mobilecheckout/.*',
    r'/creditcard/.*',
    r'/cartinfo/.*',
    r'/guid/.*',
    r'/unsubscribe/.*',
    r'/oldproduct/.*',
    r'/onlinepayment/.*',
    r'/load/.*',
    r'/additionalinfo/.*',
    r'/mag/readme',
    r'/static'
]

visit_count = 0
url = 'Enter the desired domain'
url_count = 0
headers = {}
nodes = {}
url_crawl_count = 4000

class Node:
    def __init__(self, url, visited=False):
        self.url = url
        self.visited = visited

def parser(html):
    pattern = re.compile(r'href="(.+?)"')
    hrefs = pattern.findall(html)
    urls = []
    for href in hrefs:
        if not any(re.search(p, href) for p in disallowed_patterns):
            if href.startswith('/'):
                href = url + href
            urls.append(href) 
    return uniqueness_checker(urls)

def uniqueness_checker(links):
    unique_links = set(links)  
    return list(unique_links)

def fetch_html(url):
    global headers
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +https://www.google.com/bot.html)'}
    
    try:
        response = requests.get(url, headers=headers)  
        content_type = response.headers.get('Content-Type', '')


        if 'text/html' in content_type:  
            return response.text
        else:
            return ""  

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return ""  

def exists(key):
    return key in nodes  

def bfs(start_url):
    global url_count
    global visit_count
    node = Node(start_url, False)
    queue = [node]
    nodes[start_url] = node
    
    while queue and visit_count < url_crawl_count:
        n = queue.pop(0)
        if not n.visited:
            n.visited = True
            visit_count += 1
            html_content = fetch_html(n.url) 
            
     
            if html_content:
                with open('sample.xml', 'a', encoding='utf-8') as f:  
                    if visit_count == 1:
                        f.write("""<?xml version="1.0" encoding="UTF-8"?>""")
                        f.write("<pages>")

                    f.write(f'<page><url>{sax_utils.escape(n.url)}</url><content>{sax_utils.escape(html_content)}</content></page>')
                    if visit_count == url_crawl_count:
                        f.write("</pages>")

                for link in parser(html_content):
                    if not exists(link):
                        node = Node(link)
                        nodes[link] = node
                        queue.append(node)
                        url_count += 1

    print(f'queue length : {len(queue)}')
    print(f'urls: {url_count}')


if __name__ == "__main__":
    start_time = time.time()
    bfs(url)
    end_time = time.time()
    print(f'time: {end_time - start_time}')
    print(visit_count)
