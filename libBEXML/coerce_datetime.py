# BEXML, a fast Bugs Everywhere parser with RESTful API and other issue tracker backends
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: March 2012

import re
from datetime import timedelta, datetime

def coerce_datetime(x):
    if isinstance(x, datetime):
        return x
    if isinstance(x, str):
        if re.search("[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}", x):
            # ISO 8601 format
            return datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f %z")
        elif re.search("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+\-][0-9]{2}:[0-9]{2}", x):
            # ISO 8601 format e.g. 2012-03-22T19:37:44+01:00
            offset=int(x[-6:-3]+x[-2:])
            delta=timedelta(hours=offset/100)
            ret=datetime.strptime(x[:-6], "%Y-%m-%dT%H:%M:%S")
            ret-=delta
            return ret
        elif re.search(".{4} [0-9]+ .{3} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2}", x):
            # BE format
            offset=int(x[-5:])
            delta=timedelta(hours=offset/100)
            ret=datetime.strptime(x[:-6], "%a, %d %b %Y %H:%M:%S")
            ret-=delta
            return ret
        else:
            raise Exception, "Unknown datetime string: '"+x+"'"

