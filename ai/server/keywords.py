from collections import Counter

def filter_keywords_by_reccurency(query, keywords, n_keywords_max=1):
    """
    Filters keywords from a query based on their frequency of occurrence.
    Args:
        query (str): The input query string.
        keywords (str): An string of keywords to filter.
        n_keywords_max (int): The minimum number of times a keyword must appear to be included.
    Returns:
        list: A list of keywords that appear at least n_keywords_max times in the query.
    """

    words = query.replace(',','').replace('.','').split()
    word_counts = Counter([word for word in words if word in keywords.replace(',', '').replace('.', '').split()])
    
    # Filter words that appear at least n_keywords_max times
    filtered_keywords = [word for word, count in word_counts.items() if count >= n_keywords_max]
    return filtered_keywords
