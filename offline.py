import json
import re
import time
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

tree = ET.parse('sample.xml')
root = tree.getroot()
html_pages = root.findall('page')
urls_dictionary = {}
words_dictionary = {}
titles_dictionary = {}
bodies_dictionary = {}
meta_description_dictionary = {}  
index = 0
count = 0

def normalizer(text):
    char_map = {
        "ي": "ی",
        "ك": "ک",
    }
    normalized_text = text
    for old_char, new_char in char_map.items():
        normalized_text = normalized_text.replace(old_char, new_char)
 
    normalized_text = re.sub(r"[;,.+\-()]", "", normalized_text)
    
    return normalized_text

def url_dict_generator():
    global count, url, page
    for page in html_pages:
        url = page.find('url').text
        urls_dictionary[url] = count
        count = count + 1

start_time = time.time()
url_dict_generator()

for page in html_pages:
    url = page.find('url').text
    content = page.find('content').text
    soup = BeautifulSoup(content, 'html.parser')
    body = normalizer(soup.get_text(separator=' ').lower())
    bodies_dictionary[url] = body

    title = ""
    if soup.title:
        title = normalizer(soup.title.text.lower())
        titles_dictionary[url] = title
    
    meta_description = ""
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and meta_tag.get('content'):
        meta_description = normalizer(meta_tag['content'].lower())
        meta_description_dictionary[url] = meta_description

    body_words = re.findall(r'\b\w+\b', body)
    titles_words = re.findall(r'\b\w+\b', title)

    for word in body_words:
        if len(word) != 1:
            words_dictionary.setdefault(word, ({}, {}))
            words_dictionary[word][0][urls_dictionary[url]] = words_dictionary[word][0].get(urls_dictionary[url], 0) + 1

    for t in titles_words:
        if len(t) != 1:
            words_dictionary.setdefault(t, ({}, {}))
            words_dictionary[t][1][urls_dictionary[url]] = words_dictionary[t][1].get(urls_dictionary[url], 0) + 1

for key, value in words_dictionary.items():
    print(key)
    print(value)
    print()

with open('words_dictionary.json', 'w', encoding='utf-8') as file:
    json.dump(words_dictionary, file, ensure_ascii=False)
with open('urls_dictionary.json', 'w', encoding='utf-8') as file:
    json.dump(urls_dictionary, file, ensure_ascii=False)
with open('title.json', 'w', encoding='utf-8') as file:
    json.dump(titles_dictionary, file, ensure_ascii=False)
with open('body.json', 'w', encoding='utf-8') as file:
    json.dump(bodies_dictionary, file, ensure_ascii=False)
with open('meta_description.json', 'w', encoding='utf-8') as file:  
    json.dump(meta_description_dictionary, file, ensure_ascii=False)

end_time = time.time()
total_time = round((end_time - start_time), 2)
print(total_time)
