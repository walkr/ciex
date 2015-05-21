# Import certain modules based on python version

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
