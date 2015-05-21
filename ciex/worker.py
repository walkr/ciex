# Continuous Integration Workers

import time
import logging

import oi.worker


class CIControlWorker(oi.worker.Worker):
    """ This worker will start all other ci workers """

    def run(self):
        while True:
            # Since the core's initialization might be delayed
            # wait until ci workers are ready
            if not self.program.state.get('ci_workers'):
                time.sleep(0.1)
                continue

            # Start and wait workers
            [w.start() for w in self.program.state.ci_workers]
            [w.join() for w in self.program.state.ci_workers]


class CIWorker(oi.worker.Worker):
    """ Subclass this and write your own upgrade/downgrade routines """

    def __init__(self, program, app_name, task_router, **kwargs):
        super(CIWorker, self).__init__(program, **kwargs)
        self.app_name = app_name
        self.task_router = task_router

    def execute(self, task):
        function = getattr(self, task.command)

        try:
            return function(task)
        except Exception as e:
            task.error = str(e)
            task.failure()
            logging.error('* Task {} failed: {}'.format(task, e), exc_info=1)
        return task

    def run(self):
        """ Check work from the queue and do processing """

        # self.set_cwd(self.app_name)
        while True:
            logging.debug('* {} is getting a new task'.format(self))
            task = self.task_router.take_new(self.app_name)
            logging.debug('* Got work for {}'.format(self.app_name))
            task = self.execute(task)
            self.task_router.put_finished(task)
            time.sleep(0.1)

    # -- NOTE ------------------------------------------

    # Your subclass should implement the ci operations:
    # - deploy
    # - build
    # - start
    # - etc ...
    # See `ciex.contrib.workers` for more details
