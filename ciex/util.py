# Utility functions

import sys

from ciex.contrib.workers.elixir import *
from ciex.contrib.workers.golang import *


def load_contrib_worker(worker_name):
    """ Load a local worker """
    return globals()[worker_name]


def load_other_worker(worker_dirpath, worker_modname, worker_name):
    """ Add path to sys.path and load worker """

    if worker_dirpath not in sys.path:
        sys.path.append(worker_dirpath)
    mod = __import__(worker_modname)
    return getattr(mod, worker_name)


def load_worker(worker_dirpath, worker_modname, worker_name):
    """ Load worker class """

    # Local
    if worker_dirpath == worker_modname == '.':
        return load_contrib_worker(worker_name)

    # Other
    return load_other_worker(worker_dirpath, worker_modname, worker_name)
