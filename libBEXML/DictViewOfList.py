# DictViewOfList
# Provide a dictionary view of a list
# (C) 2012 Niall Douglas http://www.nedproductions.biz/
# Created: April 2012

from collections import MutableMapping, Iterator

class DictViewOfList(MutableMapping):
    """Provides a mutable dictionary view of a two-tuple list. This lets you return
    a list with a dictionary interface for convenience, and moreover if someone
    modified the dictionary view it also updates the original list.
    """

    class DictViewOfListIter(Iterator):
        """Provides an iterator of a dictionary view of a list"""

        def __init__(self, l):
            self.__iter=iter(l)

        def __iter__(self):
            return self

        def next(self, *pars):
            return self.__iter.next(*pars)[0]

    def __init__(self, l):
        self.__list=l

    def __repr__(self):
        ret='{'
        for _k, _v in self.__list:
            if len(ret)>1:
                ret+=', '
            ret+=repr(_k)+': '+repr(_v)
        ret+='}'
        return ret

    def __len__(self):
        return len(self.__list)

    def __contains__(self, k):
        for _k, _v in self.__list:
            if _k==k:
                return True
        return False

    def __iter__(self):
        return DictViewOfListIter(self.__list)

    def __getitem__(self, k):
        for _k, _v in self.__list:
            if _k==k:
                return _v
        raise KeyError("Key '%s' not found" % k)

    def __setitem__(self, k, v):
        i=0
        for _k, _v in self.__list:
            if _k==k:
                self.__list.pop(i)
                self.__list.insert(i, (k, v))
                return
            i+=1
        self.__list.append((k, v))

    def __delitem__(self, k):
        i=0
        for _k, _v in self.__list:
            if _k==k:
                self.__list.pop(i)
                return
            i+=1
        raise KeyError("Key '%s' not found" % k)


if __name__=="__main__":
    import doctest
    doctest.testmod()
