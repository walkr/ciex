import time
import unittest


from ciex import core
from ciex import error
from ciex import compat

import oi


class TestAppSetting(unittest.TestCase):

    def setUp(self):
        pass

    def test_new_read_app_configs(self):
        config = compat.configparser.ConfigParser()
        config.read('test/samples/etc/ciex.config.sample')

        assert len(config.sections()) is 3
        for section in config.sections():
            if section.startswith('settings.app'):
                x = core.AppSetting.new(config[section])
                self.assertIsInstance(x, core.AppSetting)

    def test_missing_key(self):
        config = compat.configparser.ConfigParser()
        config.read('test/samples/etc/ciex.config.err.sample')

        section = config['settings.app.error']
        with self.assertRaises(error.AppSettingError):
            core.AppSetting.new(section)


class TestTask(unittest.TestCase):

    def setUp(self):
        self.t = core.Task('app_name', 'command', core.TaskStatus.pending)

    def test_init(self):
        self.assertIsInstance(self.t, core.Task)

    def test_update_status(self):
        self.t.pending()
        self.assertEqual(self.t.status, core.TaskStatus.pending)
        self.assertIsNone(self.t.finish)

        self.t.failure()
        self.assertEqual(self.t.status, core.TaskStatus.failure)
        self.assertIsNotNone(self.t.finish)

        self.t.success()
        self.assertEqual(self.t.status, core.TaskStatus.success)
        self.assertIsNotNone(self.t.finish)

    def test_finished(self):
        time.sleep(0.01)
        self.t.finished()
        self.assertGreater(self.t.finish, self.t.start)


class TaskRouter(unittest.TestCase):

    def setUp(self):
        self.config = compat.configparser.ConfigParser()
        self.config.read('test/samples/etc/ciex.config.sample')

        self.program = oi.Program('test program', None)
        self.program.config = self.config

        self.core = core.Core(self.program)
        self.core.initialize()
        self.router = self.core.task_router

    def test_create_new_task_router(self):
        apps_sts = self.core.load_apps_sts(self.program.config)
        new_router = core.TaskRouter.new(apps_sts)
        self.assertIsInstance(new_router, core.TaskRouter)

    def test_put_new(self):
        t = core.Task('appname1', 'command')
        self.router.put_new(t)

    def test_take_new(self):
        self.test_put_new()
        t = self.router.take_new('appname1')
        self.assertEqual(t.status, core.TaskStatus.pending)
        self.assertIsInstance(t, core.Task)

    def test_put_finished_task(self):
        self.test_put_new()
        t = self.router.take_new('appname1')
        t.success()
        self.router.put_finished(t)

    def test_put_finished_task_still_pending(self):
        self.test_put_new()
        t = self.router.take_new('appname1')
        with self.assertRaises(AssertionError):
            self.router.put_finished(t)


class TestCore(unittest.TestCase):

    def setUp(self):
        addr = None
        self.program = oi.Program('Test program', addr)
        self.program.config = compat.configparser.ConfigParser()
        self.program.config.read('test/samples/etc/ciex.config.sample')
        self.core = core.Core(self.program)
        self.core.initialize()

    def test_initialization(self):
        new_core = core.Core(self.program)
        self.assertFalse(new_core.initialized)

        # Check core
        new_core.initialize()
        self.assertTrue(new_core.initialized)
        self.assertIsInstance(new_core, core.Core)

        # Check task router
        router = new_core.program.state.task_router
        self.assertIsInstance(router, core.TaskRouter)

        # Check workers
        workers = new_core.program.state.ci_workers
        self.assertEqual(len(workers), 2)

    def create_task(self):
        ok, task = self.core.create_task('appname1', 'command')
        self.assertTrue(ok)
        self.assertIsNotNone(task.env)

        ok, task = self.core.create_task('appname1', 'command')
        self.assertFalse(ok)

    def test_ci_commands_with_tasks(self):
        app_name = 'appname1'
        for c in ['start', 'stop', 'deploy', 'build', 'upgrade', 'downgrade']:
            fun = getattr(self.core, c)
            ok, res = fun(app_name)
            self.assertTrue(ok)
            self.assertTrue('pending' in res)

    def test_ci_commands_other(self):
        # List apps
        items = self.core.list()
        self.assertEqual(len(items), 2)

        # Create task, then take it, to force
        # it to be in the pending state
        self.core.build('appname1')
        self.core.task_router.take_new('appname1')

        # Status should be pending now
        last = self.core.last('appname1')
        self.assertIsNotNone(last)
        self.assertTrue('pending' in last)


if __name__ == '__main__':
    unittest.main()
