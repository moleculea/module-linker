# -*- coding: utf-8  -*-
import sys
import itertools
import collections

def list2dict(l):
    """
    Convert list to ordered dictionary, where adjacent elements become key and value
    Example: [1, 2, 3, 4] --> {1: 2, 2: 4}
    """
    return collections.OrderedDict(itertools.izip_longest(*[iter(l)] * 2))

def list2tuplelist(l):
    """
    Convert list to list of tuples, where adjacent elements become a pair
    Example: [1, 2, 3, 4] --> [(1, 2), (3, 4)]
    """
    return list(itertools.izip_longest(*[iter(l)] * 2))

def tuplelist2list(l):
    """
    Reverse list2tuplelist()
    """
    r = []
    for t in l:
        r.append(t[0])
        r.append(t[1])
    return r

def getduplicate(l):
    """
    Locate the duplicate element(s) of a list, and return them as a list
    """
    counter = collections.Counter(l)
    t = filter(lambda x: x[1] > 1, counter.most_common())
    return [x[0] for x in t]

class output(object):
    """
    ANSI console colored output:
        * error (red)
        * warning (yellow)
        * debug (green)
    """
    
    RED     = 1
    GREEN   = 2
    YELLOW  = 3
    ERROR   = 4
    DEBUG   = 5
    WARNING = 6
    @staticmethod
    def __out(type, msg):
        if type == output.ERROR:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" % (30 + output.RED, "Error", msg))
        if type == output.DEBUG:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" % (30 + output.GREEN, "Debug", msg))
        if type == output.WARNING:
            sys.stdout.write("\033[%dm [%s] %s\033[m\n" % (30 + output.YELLOW, "Warning", msg))
    @staticmethod
    def error(msg):
        output.__out(output.ERROR, msg)
    @staticmethod    
    def debug(msg):
        output.__out(output.DEBUG, msg)
    @staticmethod   
    def warning(msg):
        output.__out(output.WARNING, msg)
        
if __name__ == '__main__':
    utilities.output.warning("Please run main.py script from project's directory.")        