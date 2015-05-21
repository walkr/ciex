import os
from contextlib import contextmanager


@contextmanager
def src_path(task):
    """ Change to app src parent directory """
    yield os.chdir(task.env.src_path)


@contextmanager
def local_repo(task):
    """ Change to local repo directory """
    path = os.path.join(task.env.src_path, task.app_name)
    yield os.chdir(path)


@contextmanager
def local_release(task, tag):
    """ Go to a release's directory """
    path = os.path.join(task.env.install_path, task.app_name, 'release', tag)
    yield os.chdir(path)


@contextmanager
def local_release_bin(task):
    """ Local release main bin directory (not versioned) """
    path = os.path.join(
        task.env.src_path, task.app_name, 'rel', task.app_name, 'bin')
    yield os.chdir(path)
