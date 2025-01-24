import heapq
import json
import time
from difflib import get_close_matches
from flask import Flask, request, render_template

def load_data():
    with open('words_dictionary.json', 'r', encoding='utf-8') as file:
        words_dictionary = json.load(file)
        
    with open('urls_dictionary.json', 'r', encoding='utf-8') as file:
        urls_dictionary = json.load(file)

    with open('title.json', 'r', encoding='utf-8') as file:
        title_dict = json.load(file)

    with open('body.json', 'r', encoding='utf-8') as file:
        body_dict = json.load(file)

    with open('meta_description.json', 'r', encoding='utf-8') as file:
        meta_description_dict = json.load(file)

    return words_dictionary, urls_dictionary, title_dict, body_dict, meta_description_dict


def find_best_match(term, words_dict):
    if term in words_dict:
        return term, []

    one_char_diff_matches = [
        w for w in words_dict.keys()
        if len(w) == len(term) and sum(1 for a, b in zip(term, w) if a != b) == 1
    ]

    if one_char_diff_matches:
        best_match = max(one_char_diff_matches, key=lambda match: sum(words_dict[match][0].values()))
        return best_match, one_char_diff_matches

    close_matches = get_close_matches(term, words_dict.keys(), n=5, cutoff=0.8)
    close_matches = sorted(close_matches, key=lambda match: sum(words_dict[match][0].values()), reverse=True)

    all_matches = (one_char_diff_matches + close_matches)
    best_match = max(all_matches, key=lambda match: sum(words_dict[match][0].values()), default="")

    return best_match if best_match else term, one_char_diff_matches

def correct_query_with_substitution(query_terms, words_dict):
    corrected_terms = []
    all_one_char_diff_matches = []
    for term in query_terms:
        best_match, one_char_diff_matches = find_best_match(term, words_dict)
        corrected_terms.append(best_match)
        all_one_char_diff_matches.extend(one_char_diff_matches)

   
    alternative_queries = []
    for match in all_one_char_diff_matches:
        alt_query = query_terms.copy()
        for i, term in enumerate(query_terms):
            if term != corrected_terms[i]:
                alt_query[i] = match
        body_inter, title_inter = get_intersections(alt_query, words_dict)
        total_pages = len(body_inter) + len(title_inter)
        alternative_queries.append((total_pages, alt_query))

    
    if alternative_queries:
        alternative_queries.sort(reverse=True, key=lambda x: x[0])
        corrected_terms = alternative_queries[0][1]

    return corrected_terms, all_one_char_diff_matches



def get_intersections(query_words, words_dict):
    body_urls = set()
    title_urls = set()

    for word in query_words:
        if word in words_dict:
            body_urls.update(words_dict[word][0].keys())
            title_urls.update(words_dict[word][1].keys())


    body_inter = body_urls.intersection(*[words_dict[word][0].keys() for word in query_words if word in words_dict])
    title_inter = title_urls.intersection(*[words_dict[word][1].keys() for word in query_words if word in words_dict])

    return body_inter, title_inter


def score(body_inter, title_inter, query_words, words_dict):
    total_score = {}
    
    if len(query_words) < 2:
        word = query_words[0]
        if word in words_dict:
            for url in title_inter:
                total_score[url] = total_score.get(url, 0) + 50
            for url in body_inter:
                total_score[url] = total_score.get(url, 0) + 10

        return total_score

    for word in query_words:
        if word in words_dict:
            for url in title_inter:
                positions_w1 = list(words_dict[query_words[0]][1].keys())
                positions_w2 = list(words_dict[query_words[1]][1].keys())
                for p1 in positions_w1:
                    for p2 in positions_w2:
                        if p1 == p2:
                            total_score[url] = total_score.get(url, 0) + 50
                        else:
                            distance = abs(int(p1) - int(p2))
                            if distance == 1:
                                total_score[url] = total_score.get(url, 0) + 30  
                            elif distance > 1:
                                total_score[url] = total_score.get(url, 0) + (3 / distance) + 15  

            for url in body_inter:
                positions_w1 = list(words_dict[query_words[0]][0].keys())
                positions_w2 = list(words_dict[query_words[1]][0].keys())
                for p1 in positions_w1:
                    for p2 in positions_w2:
                        if p1 == p2:
                            total_score[url] = total_score.get(url, 0) + 10
                        else:
                            distance = abs(int(p1) - int(p2))
                            if distance == 1:
                                total_score[url] = total_score.get(url, 0) + 5  
                            elif distance > 1:
                                total_score[url] = total_score.get(url, 0) + (1 / distance) + 2

    for url in list(total_score.keys()):
        if not url in title_inter and not url in body_inter:
            del total_score[url]

    return total_score


def suggest_next_queries(words_dictionary, word):
    matching_words = []
    for w in words_dictionary:
        if w.startswith(word):
            matching_words.append(w)
    return matching_words


def number_to_url(number, url_dict):
    return next((key for key, value in url_dict.items() if value == number), None)


def get_value(url, dictionary):
    return dictionary.get(url)

def create_summary(body, query_terms):
    body = body.lower()

    
    positions = {term: body.find(term.lower()) for term in query_terms}
    

    valid_positions = {term: pos for term, pos in positions.items() if pos != -1}

    if valid_positions:
        if len(valid_positions) == 1:  
            term = next(iter(valid_positions))  
            index = valid_positions[term]
            start = max(0, index - 130)
            end = min(len(body), index + len(term) + 150)
            summary = body[start:end].replace(term.lower(), f"<b>{term}</b>")
            return summary
        
        else: 
            found_terms = list(valid_positions.keys())
            first_term_index = valid_positions[found_terms[0]]
            second_term_index = valid_positions[found_terms[1]]

            if abs(second_term_index - first_term_index) < 100:
                
                start = max(0, min(first_term_index, second_term_index) - 130)
                end = min(len(body), max(first_term_index, second_term_index) + 
                           max(len(found_terms[0]), len(found_terms[1])) + 150)
                summary = body[start:end]
                for term in query_terms:
                    summary = summary.replace(term.lower(), f"<b>{term}</b>")
                return summary
            
            else:
               
                start_first = max(0, first_term_index - 130)
                end_first = min(len(body), first_term_index + len(found_terms[0]) + 50)
                
                start_second = max(0, second_term_index - 50)
                end_second = min(len(body), second_term_index + len(found_terms[1]) + 130)
                
               
                if start_first < start_second:
                    summary = body[start_first:end_first] + '...' + body[start_second:end_second]
                else:
                    summary = body[start_second:end_second] + '...' + body[start_first:end_first]

                for term in query_terms:
                    summary = summary.replace(term.lower(), f"<b>{term}</b>")
                
                return summary

    return body[:250]  


template_dir = 'template'
app = Flask(__name__, template_folder=template_dir)


@app.route('/suggest', methods=['GET'])
def suggest():
    query = request.args.get('query', '')
    words = query.split(" ")
    with open('words_dictionary.json', 'r', encoding='utf-8') as file:
        words_dictionary = json.load(file)

    suggestions = [w for w in words_dictionary if w.startswith(words[-1])]
    return json.dumps(suggestions)

@app.route('/', methods=['GET', 'POST'])
def search():
    start_time = time.time()
    results = []
    query_message = ""
    no_results = False
    seen_titles = set()

    if request.method == 'POST':
        page = int(request.form.get('page', 1)) 
        query = request.form.get('query', '').strip()

        terms = query.split()

        words_dictionary, urls_dictionary, title_dict, body_dict, meta_description_dict = load_data()


        corrected_terms, all_one_char_diff_matches = correct_query_with_substitution(terms, words_dictionary)
        corrected_query = " ".join(corrected_terms)

        print("Original Query:", terms)
        print("Corrected Query:", corrected_terms)

     
        if corrected_terms != terms:
            query_message = f"آیا منظورتان {corrected_query} بود؟"

            print("One Character Different Matches:", all_one_char_diff_matches)

           
            for match in all_one_char_diff_matches:
            
                for i in range(len(terms)):
                    if terms[i] != corrected_terms[i]:
                        alternative_query = terms.copy()
                        alternative_query[i] = match
                        print("Alternative Query:", alternative_query)
                        
                        body_inter, title_inter = get_intersections(alternative_query, words_dictionary)
                        
                   
                        total_pages = len(body_inter) + len(title_inter)
                        print(f"Total pages for alternative query '{' '.join(alternative_query)}': {total_pages}")


        else:
            body_inter, title_inter = get_intersections(terms, words_dictionary)
            if not body_inter and not title_inter:
              
                alternative_queries = []

                combined_query = " ".join(terms)
                one_char_diff_matches = []

                for title in title_dict.values():
                    
                    words = title.split()
             
                    for i in range(len(words) - 1):
                        word_pair = f"{words[i]} {words[i + 1]}"
                 
                        if len(word_pair) == len(combined_query) and sum(1 for a, b in zip(combined_query, word_pair) if a != b) == 1:
                            one_char_diff_matches.append(word_pair)

                for body in body_dict.values():
                
                    words = body.split()
               
                    for i in range(len(words) - 1):
                        word_pair = f"{words[i]} {words[i + 1]}"
                       
                        if len(word_pair) == len(combined_query) and sum(1 for a, b in zip(combined_query, word_pair) if a != b) == 1:
                            one_char_diff_matches.append(word_pair)

                print("Found one character different matches:", one_char_diff_matches)

                for match in one_char_diff_matches:
                    alt_query = match.split()
                    body_urls, title_urls = get_intersections(alt_query, words_dictionary)
                    total_pages = len(body_urls) + len(title_urls)
                    alternative_queries.append((total_pages, alt_query))

                if alternative_queries:
                    alternative_queries.sort(reverse=True, key=lambda x: x[0])
                    corrected_terms = alternative_queries[0][1]
                    corrected_query = " ".join(corrected_terms)
                query_message = f"آیا منظورتان {corrected_query} بود؟"

        body_inter, title_inter = get_intersections(corrected_terms, words_dictionary)
        print("Body Intersection:", body_inter)
        print("Title Intersection:", title_inter)

        sc = score(body_inter, title_inter, corrected_terms, words_dictionary)
        print("Scores Calculated:", sc)
        top_results = heapq.nlargest(4000, sc.items(), key=lambda x: x[1])

        for key, _ in top_results:
            url = number_to_url(int(key), urls_dictionary)
            title = get_value(url, title_dict)
            body = get_value(url, body_dict)
            meta_description = get_value(url, meta_description_dict)

            if title not in seen_titles:
                seen_titles.add(title)
                summary = meta_description if meta_description else create_summary(body, corrected_terms)

                results.append({
                    'url': url,
                    'title': title,
                    'meta_description': summary
                })

        if not results:
            no_results = True
        num_results_per_page = 5
        total_pages = (len(results) + num_results_per_page - 1) // num_results_per_page
        search_time = round(time.time() - start_time, 3)
        start_index = (page - 1) * 5
        end_index = page * 5
        return render_template('results.html',results=results[start_index:end_index],query=query,query_message=query_message,no_results=no_results,search_time=search_time,num_results=len(results),page=page,total_pages=total_pages)

    return render_template('index.html')


if __name__ == '__main__':
    app.run()