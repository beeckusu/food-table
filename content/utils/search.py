import re

from django.contrib.postgres.search import SearchQuery

# Matches runs of characters that aren't word characters, used to strip
# tsquery operators (&, |, !, (, ), :, ') out of each user-supplied term
# before it's interpolated into a raw tsquery string.
_TSQUERY_UNSAFE_CHARS = re.compile(r'[^\w]+')


def build_prefix_search_query(query):
    """
    Build a raw prefix-matching tsquery SearchQuery from a free-text search string.
    Each term is sanitized and given its own :* suffix so multi-word queries like
    "Al Pas" become the valid raw tsquery "Al:* & Pas:*" instead of the unparseable
    "Al Pas:*". Returns None if no usable terms remain after sanitizing.
    """
    terms = [t for t in (_TSQUERY_UNSAFE_CHARS.sub('', t) for t in query.split()) if t]
    if not terms:
        return None
    prefix_query = ' & '.join(f'{term}:*' for term in terms)
    return SearchQuery(prefix_query, search_type='raw')
