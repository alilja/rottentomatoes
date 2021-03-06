#!/usr/bin/env python

"""
Rotten Tomatoes API:  http://developer.rottentomatoes.com/

Main file for interacting with the Rotten Tomatoes API.
"""

from urllib import urlencode
import zlib
import os

try:
    import json
except ImportError:  # pragma: no cover
    # For older versions of Python.
    import simplejson as json

try:
    from urllib2 import urlopen
except ImportError:  # pragma: no cover
    # For Python 3.
    from urllib.request import urlopen

try:
    from rottentomatoes_api_key import API_KEY
except ImportError:
    API_KEY = os.environ.get('RT_KEY')


class RT(object):
    """
    An easy-to-use Python wrapper for the Rotten Tomatoes API.

    >>> RT('my-api-key').search('the lion king')

    Or, if your API key is stored in the `rottentomatoes_api_key.py` file,
    the RT class can be initialized like so:

    >>> RT().search('the lion king')
    """

    def __init__(self, api_key='', version=1.0):
        if not api_key:
            self.api_key = API_KEY
        else:
            self.api_key = api_key
        assert self.api_key != None, "No API Key"

        if isinstance(version, float):
            version = str(version)  # Eliminate any weird float behavior.
        self.version = version
        BASE_URL = 'http://api.rottentomatoes.com/api/public/v%s/' % version
        self.BASE_URL = BASE_URL
        self.lists_url = BASE_URL + 'lists'
        self.movie_url = BASE_URL + 'movies'

    def _load_json_from_url(self, url):
      """
      A wrapper around the api call. The response might be gzipped,
      which this will abstract away.
      Returns a json-decoded object.
      """
      response = urlopen(url).read()

      # the response might be gzip'd
      try:
        # explanation of magic number:
        # http://stackoverflow.com/a/2695466/474683
        response = zlib.decompress(response, 16+zlib.MAX_WBITS)
      except zlib.error:
        # if there's an error, it's probably not gzip'd
        pass

      return json.loads(response)

    def search(self, query, datatype='movies', **kwargs):
        """
        Rotten Tomatoes movie search. Returns a list of dictionaries.
        Possible kwargs include: `page` and `page_limit`.

        >>> RT().search('the lion king')

        Or, for the total count of search results:

        >>> RT().search('disney', 'total')
        """
        search_url = [self.movie_url, '?']
        kwargs.update({'apikey': self.api_key, 'q': query})
        search_url.append(urlencode(kwargs))
        data = self._load_json_from_url(''.join(search_url))
        return data[datatype]

    def lists(self, directory=None, sub=None, **kwargs):
        """
        Displays the lists available in the Rotten Tomatoes API.

        >>> RT().lists()
        {u'links': {u'movies': u'http://link-to-movies'
                    u'dvds': u'http://link-to-dvds'}
        >>> RT().lists('dvds')
        {u'links': {u'new_releases': u'http://link-to-new-releases'}
        >>> RT().lists('dvds', 'new_releases')
        """
        lists_url = [self.lists_url]
        if directory:
            if sub:
                lists_url.append('/%s/%s' % (directory, sub))
            else:
                lists_url.append('/%s' % directory)
        kwargs.update({'apikey': self.api_key})
        lists_url.extend(['.json?', urlencode(kwargs)])
        data = self._load_json_from_url(''.join(lists_url))
        return data

    def info(self, id_num, specific_info=None):
        """
        Return info for a movie given its `id`.
        Arguments for `specific_info` include `cast` and `reviews`.

        >>> fight_club = u'13153'
        >>> RT().info(fight_club)
        >>> # For cast info
        ... RT().info(fight_club, 'cast')
        """
        if isinstance(id_num, int):
            id_num = str(id_num)
        movie_url = [self.movie_url]
        movie_url.append('/%s' % id_num)
        if specific_info:
            movie_url.append('/%s' % specific_info)
        end_of_url = ['.json?', urlencode({'apikey': self.api_key})]
        movie_url.extend(end_of_url)
        data = self._load_json_from_url(''.join(movie_url))
        return data

    def new(self, kind='movies', **kwargs):
        """
        Short method to return just opened theatrical movies or newly
        released dvds. Returns a list of dictionaries.

        >>> RT().new('dvds', page_limit=5)
        """
        if kind == 'movies':
            return self.lists('movies', 'opening', **kwargs)['movies']
        elif kind == 'dvds':
            return self.lists('dvds', 'new_releases', **kwargs)['movies']

    def movies(self, sub='in_theaters', **kwargs):
        """
        Short method for returning specific movie lists.
        Possible sub aruments include: `box_office`, `in_theaters`,
        `opening`, and `upcoming`.

        >>> RT().movies('in_theaters', page_limit=5)
        """
        return self.lists('movies', sub, **kwargs)['movies']

    def dvds(self, sub='new_releases', **kwargs):
        """
        Short method for returning specific movie lists.
        Currently, only one sub argument is possible: `new_releases`.

        >>> RT().dvds(page_limit=5)
        """
        return self.lists('dvds', sub, **kwargs)['movies']

    def feeling_lucky(self, search_term):
        """
        Similar to Google's **I'm Feeling Lucky** button.
        Returns first instance of search term.

        >>> RT().feeling_lucky('memento')
        """
        return self.search(search_term, page_limit=1)[0]
