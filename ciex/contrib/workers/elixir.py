import os
import functools
import logging


from ciex.worker import CIWorker
from ciex import context


def with_path(attr_or_function):
    """ Change working dir to `path` if path is not callable,
    or path(task) if path is callabele """
    def decorator(fun):
        @functools.wraps(fun)
        def wrapper(self, *args, **kwargs):
            if callable(attr_or_function):
                path = attr_or_function(*args)
            else:
                task = args[0]
                path = getattr(task.env, path)
            os.chdir(path)
            return fun(self, *args, **kwargs)
        return wrapper
    return decorator


def ensure_path(fn):
    """ Check if path exists or create it """
    def decorator(fun):
        @functools.wraps(fun)
        def wrapper(self, *args, **kwargs):
            path = fn(*args, **kwargs)
            if not os.path.exists(path):
                os.makedirs(path)
            return fun(self, *args, **kwargs)
        return wrapper
    return decorator


class ElixirCIWorker(CIWorker):
    """ Do work required to upgrade, downgrade the app """

    def start_(self, task):
        with context.local_release_bin(task):
            code = os.system('./{} start'.format(task.app_name))
            assert code is 0
        return task.success()

    def stop(self, task):
        with context.local_release_bin(task):
            code = os.system('./{} stop'.format(task.app_name))
            assert code is 0
        return task.success()

    # Ensure install folder exists on the machine
    @ensure_path(lambda task: os.path.join(task.env.src_path))
    def deploy(self, task):
        """ Create dir if necessary and clone repo """

        with context.src_path(task) as code:
            logging.debug('* Cloning ...')
            code = os.system('git clone {}'.format(task.env.repo))
            logging.debug('* git clone: {}'.format(code))
            assert code == 0
            return task.success()

    def pull(self, task):
        """ Pull changes remote repository """

        with context.local_repo(taks):
            code = os.system('git pull')
            logging.debug('* git pull: {}'.format(code))
            assert code == 0
        return task.success()

    def build(self, task):
        """ Make release """

        with context.local_repo(task):
            os.system('mix deps.get')
            os.environ['MIX_ENV'] = 'prod'
            os.system('mix release')
        return task.success()

    def upgrade(self, task, tag):
        """ Upgrade app """
        pass

    def downgrade(self, task, tag):
        """ Downgrade app """
        with context.local_bin(task):
            os.system('./{} upgrade "{}"'.format(task.app_name, tag))
