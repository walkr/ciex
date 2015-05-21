# Models

import time
import enum
import logging
import functools

from . import error
from . import compat
from . import util


class AppSetting(object):
    """ An AppSetting object contains the information related
    to a single app's configuration described in the "--config" file """

    def __init__(self, name, **kwargs):
        super(AppSetting, self).__init__()
        self.name = name
        self.__dict__.update(kwargs)

    @classmethod
    def validate(cls, section):
        """ Ensure keys are present in the section """
        known_options = [
            'repo', 'src_path', 'install_path',
            'worker_dirpath', 'worker_modname', 'worker_classname'
        ]

        for key in known_options:
            if section.get(key) is None:
                raise error.AppSettingError(
                    '{} missing from section {}'.format(key, section))

    @classmethod
    def new(cls, section):
        """ Create a new AppSetting object from a config section """

        cls.validate(section)
        name = section.name.replace('settings.app.', '')
        kwargs = {k: v.strip('"').strip() for k, v in section.items()}
        return cls(name, **kwargs)


class TaskStatus(enum.Enum):
    """ Task Status """
    pending = 0
    success = 1
    failure = 2


class Task(object):
    """ Work to be executed by the CI Workers """

    def __init__(self, app_name, command, status=None, error=None,
                 env=None, start=None, finish=None):
        super(Task, self).__init__()
        self.app_name = app_name
        self.command = command
        self.status = status or TaskStatus.pending
        self.error = None

        self.env = env
        self.start = start or time.time()
        self.finish = None

    def __str__(self):
        t = '<Task(app_name={}, command={}, status={}, error={}, start={}, finish={})>'
        return t.format(
            self.app_name, self.command, self.status,
            self.error, self.start, self.finish)

    def finished(self):
        """ Mark finish timestamp """
        self.finish = time.time()
        return self

    def pending(self):
        """ Mark task as pending """
        self.status = TaskStatus.pending
        return self

    def success(self):
        """ Mark task as successfully completed """
        self.status = TaskStatus.success
        return self.finished()

    def failure(self):
        """ Mark task as failure """
        self.status = TaskStatus.failure
        return self.finished()


class TaskRouter(object):
    """ Control the task going in / going out """

    def __init__(self, apps_sts, new, last):
        super(TaskRouter, self).__init__()
        self.apps_sts = apps_sts  # apps settings
        self.new = new  # app task queues
        self.last = last  # app last

    @classmethod
    def new(cls, apps_sts):
        """ Create a new TaskRouter object from app configs """

        new, last = {}, {}

        for s in apps_sts.values():
            new[s.name] = compat.Queue()
            # Add default blank tasks
            last[s.name] = Task(s.name, 'nothing', TaskStatus.success)

        return cls(apps_sts, new, last)

    def approve_new(self, task):
        """ Approve a new task"""
        return self.last[task.app_name] != TaskStatus.pending

    def put_new(self, task):
        """ Put a task on the new queue (to be executed later) """
        self.new[task.app_name].put(task)

    def take_new(self, app_name):
        """ Take a new task for `app_name` and put it on the last
        executed (its status should be pending) """
        task = self.new[app_name].get()
        self.last[app_name] = task
        return task

    def put_finished(self, task):
        """ Put an already executed task (task was executed) """
        assert task.status != TaskStatus.pending
        self.last[task.app_name] = task


def maybe_init(fun):
    """ This decorator is used to initialize the Core object - provided
    is was not already initialized.

    We add the core command (build, upgrade, downgrade, etc) to the
    oi.Program, however, we don't have access to the program configuration
    until the program is actually started, therefore we need to
    delay the initialization until we have the config """

    @functools.wraps(fun)
    def wrapper(self, *args, **kwargs):
        if not self.initialized:
            self.initialize()
        return fun(self, *args, **kwargs)
    return wrapper


class Core(object):
    """ The `Core` object gets initialized when the very fist command
    is launched. It will read the config file, load ci workers, create
    task queue, etc. """

    def __init__(self, program):
        self.program = program
        self.initialized = False

    # == HELPERS =======================================================

    def initialize(self):
        """ Create the task router and load ci workers """

        apps_sts = self.load_apps_sts(self.program.config)
        self.program.state.apps_sts = apps_sts
        self.program.state.task_router = TaskRouter.new(apps_sts)
        self.program.state.ci_workers = self.load_ci_workers(apps_sts)
        self.initialized = True

    def load_apps_sts(self, config_parser):
        """ Read the configuration for each app """

        logging.debug('* Reading config file')
        apps_sts = {}
        parser = config_parser
        for section in parser.sections():
            if section.startswith('settings.app'):
                s = AppSetting.new(parser[section])
                apps_sts[s.name] = s
        logging.debug('* Configurations: {}'.format(apps_sts))
        return apps_sts

    def load_ci_workers(self, apps_sts):
        """ Load python worker classes """
        logging.debug('* Loading custom app workers ...')
        workers = []

        for s in apps_sts.values():
            worker_class = util.load_worker(
                s.worker_dirpath,
                s.worker_modname,
                s.worker_classname
            )
            instance = worker_class(self.program, s.name, self.task_router)
            workers.append(instance)
        return workers

    @property
    def task_router(self):
        return self.program.state.task_router

    def create_task(self, app_name, command):
        """ Create work for app's worker """
        task = Task(app_name, command)
        task.env = self.program.state.apps_sts[app_name]

        # Unless a pending task exists, add task to new queue
        ok = self.task_router.approve_new(task)
        if ok:
            self.task_router.put_new(task)
            return True, task
        return False, 'There is a current pending task'

    # == SUPPORTED COMMANDS ============================================

    def reload(self):
        """ Reload core """
        try:
            self.initialize()
        except Exception as e:
            return 'Err: {}'.format(e)
        return 'ok'

    @maybe_init
    def start(self, app_name):
        """ start app """
        # NOTE: worker's `start` method is for threading
        # therefore we will trigger the command `start_`
        ok, res = self.create_task(app_name, 'start_')
        return ok, str(res)

    @maybe_init
    def stop(self, app_name):
        """ stop app """
        ok, res = self.create_task(app_name, 'stop')
        return ok, str(res)

    @maybe_init
    def deploy(self, app_name):
        """ clone remote repo """
        ok, res = self.create_task(app_name, 'deploy')
        return ok, str(res)

    @maybe_init
    def build(self, app_name):
        """ build app """
        ok, res = self.create_task(app_name, 'build')
        return ok, str(res)

    @maybe_init
    def upgrade(self, app_name):
        """ upgrade app """
        ok, res = self.create_task(app_name, 'upgrade')
        return ok, str(res)

    @maybe_init
    def downgrade(self, app_name):
        """ downgrade the app """
        ok, res = self.create_task(app_name, 'downgrade')
        return ok, str(res)

    @maybe_init
    def last(self, app_name):
        """ show last task for `app_name` """
        return str(self.program.state.task_router.last[app_name])

    @maybe_init
    def list(self):
        """ List all registered apps """
        return list(self.program.state.task_router.last.keys())
