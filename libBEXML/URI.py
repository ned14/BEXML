# URI
# Provides a useful URI object
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

import urlparse, urllib, urllib2, os, logging
from DictViewOfList import DictViewOfList

log=logging.getLogger(__name__)

class URI(object):
    """Holds a Uniform Resource Identifier and lets you do things with it.
    Saves having to arse around with python's urlparse which I don't think
    well designed. Use URI like this:

    URI("http://www.python.org/")
    URI(scheme="http", hostname="www.python.org")
    
    If you want it as a string, just do str(URI).

    >>> x=URI("HTTP://niall:pass@nedprod.com:42/some/path/?q=5&s=Niall&r=++Doug%7elas#Megan")
    >>> print x
    http://niall:pass@nedprod.com:42/some/path/?q=5&s=Niall&r=++Doug%7Elas#Megan
    >>> print x.scheme
    http
    >>> print x.netloc
    niall:pass@nedprod.com:42
    >>> print x.username
    niall
    >>> print x.password
    pass
    >>> print x.hostname
    nedprod.com
    >>> print x.port
    42
    >>> print x.path
    /some/path/
    >>> print x.params
    <BLANKLINE>
    >>> print x.queryl
    [('q', '5'), ('s', 'Niall'), ('r', '  Doug~las')]
    >>> print x.query
    {'q': '5', 's': 'Niall', 'r': '  Doug~las'}
    >>> print x.fragment
    Megan
    >>> y=URI(scheme='http', username='niall', password='pass', hostname='nedprod.com', port=42, path='/some/path/', query={'q': '5', 's': 'Niall', 'r': '  Doug~las'}, fragment='Megan')
    >>> assert x==y
    >>> print hash(x), hash(y)
    27760230 27760230
    >>> x.username='ned'
    >>> print x
    http://ned:pass@nedprod.com:42/some/path/?q=5&s=Niall&r=++Doug%7Elas#Megan
    >>> x.netloc='www.google.com'
    >>> print x
    http://www.google.com/some/path/?q=5&s=Niall&r=++Doug%7Elas#Megan
    >>> x.username='ned'
    >>> print x
    http://ned@www.google.com/some/path/?q=5&s=Niall&r=++Doug%7Elas#Megan
    >>> x.query['g']='& an; %par'
    >>> print x
    http://ned@www.google.com/some/path/?q=5&s=Niall&r=++Doug%7Elas&g=%26+an%3B+%25par#Megan
    """

    def __init__(self, *pars, **kpars):
        uri=pars[0] if len(pars)>0 else None
        if uri is not None and not isinstance(uri, str):
            uri=str(uri)
        if isinstance(uri, str):
            up=urlparse.urlparse(uri)
            assert up.scheme is not ""
            if up.scheme.lower()=="file":
                up=(up.scheme.lower(), os.path.abspath(up.netloc).replace(os.sep, '/'), up.path, up.params, up.query, up.fragment)
                uri2=urlparse.urlunparse(up)
                if uri!=uri2:
                    log.warn("Fixed up URI '"+uri+"' to '"+uri2+"'")
                uri=uri2
                up=urlparse.urlparse(uri)
            self.__unpack(up)
        else:
            self.__unpack(urlparse.urlparse(''))
        for par in kpars:
            setattr(self, par, kpars[par])

    def __unpackconv(self, up):
        self.__username=up.username
        self.__password=up.password
        self.__hostname=up.hostname
        self.__port=up.port if self.__scheme!='file' else None
        self.__dirty=False

    def __unpack(self, up):
        self.__scheme=up.scheme
        self.__netloc=up.netloc
        self.__path=up.path
        self.__params=up.params
        self.__query=urlparse.parse_qsl(up.query)
        self.__fragment=up.fragment
        self.__unpackconv(up)

    def __undirty(self):
        if self.__dirty:
            netloc=""
            if self.__username is not None:
                netloc+=self.__username
            if self.__password is not None:
                netloc+=':'+self.__password
            if self.__hostname is not None:
                if len(netloc)>0: netloc+='@'
                netloc+=self.__hostname
            if self.__port is not None:
                netloc+=':'+str(self.__port)
            self.__netloc=netloc
            self.__dirty=False

    def __pack(self, undirty=True):
        if undirty: self.__undirty()
        return (self.__scheme, self.__netloc, self.__path, self.__params, urllib.urlencode(self.__query), self.__fragment)

    def __str__(self):
        """Returns the URI as a string"""
        return urlparse.urlunparse(self.__pack())

    def __hash__(self):
        return hash(str(self))

    def __lt__(self, other): return str(self)<other
    def __le__(self, other): return str(self)<=other
    def __eq__(self, other): return str(self)==other
    def __ne__(self, other): return str(self)!=other
    def __gt__(self, other): return str(self)>other
    def __ge__(self, other): return str(self)>=other

    @property
    def scheme(self):
        """The scheme used by this URI"""
        return self.__scheme
    @scheme.setter
    def scheme(self, value):
        self.__scheme=value

    @property
    def netloc(self):
        """The network location used by this URI. Setting this also sets username, password, hostname and port"""
        self.__undirty()
        return self.__netloc
    @netloc.setter
    def netloc(self, value):
        self.__netloc=value
        self.__unpackconv(urlparse.urlparse(self.__scheme+'://'+self.__netloc))

    @property
    def path(self):
        """The path used by this URI"""
        return self.__path
    @path.setter
    def path(self, value):
        self.__path=value

    @property
    def params(self):
        """The params used by this URI"""
        return self.__params
    @params.setter
    def params(self, value):
        self.__params=value

    @property
    def queryl(self):
        """An ordered list of tuples reflecting the query performed by this URI"""
        return self.__query
    @queryl.setter
    def queryl(self, value):
        self.__query=value

    @property
    def query(self):
        """An ordered dictionary reflecting the query performed by this URI. Note that
        using this property will not be able to set duplicates in the query parameters."""
        return DictViewOfList(self.__query)
    @query.setter
    def query(self, value):
        self.__query=value.items()

    @property
    def fragment(self):
        """The fragment used by this URI"""
        return self.__fragment
    @fragment.setter
    def fragment(self, value):
        self.__fragment=value

    @property
    def username(self):
        """The username used by this URI"""
        return self.__username
    @username.setter
    def username(self, value):
        self.__username=value
        self.__dirty=True

    @property
    def password(self):
        """The password used by this URI"""
        return self.__password
    @password.setter
    def password(self, value):
        self.__password=value
        self.__dirty=True

    @property
    def hostname(self):
        """The hostname used by this URI"""
        return self.__hostname
    @hostname.setter
    def hostname(self, value):
        self.__hostname=value
        self.__dirty=True

    @property
    def port(self):
        """The port used by this URI"""
        return self.__port
    @port.setter
    def port(self, value):
        self.__port=value
        self.__dirty=True

    @property
    def pathname(self):
        """Returns the filing system pathname represented by this URI, or None if scheme is not file"""
        if self.scheme!='file': return None
        # Windows can pass a drive letter through, unfortunately this causes urlparse to misparse
        path=(self.netloc+self.path) if self.netloc[-1]==':' else self.netloc
        return urllib.url2pathname(path)
    @pathname.setter
    def pathname(self, value):
        self.__unpack(urlparse.urlparse('file://'+urllib.pathname2url(value)))

if __name__=="__main__":
    import doctest
    doctest.testmod()
