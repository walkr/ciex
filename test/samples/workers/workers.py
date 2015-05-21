from ciex.worker import CIWorker


class CustomWorker1(CIWorker):
    def checkout(self, task):
        """ Checkout repository """
        task.success()  # or task.failure()
        return task

    def upgrade(self, task):
        """ Checkout code and upgrade app """
        task.success()
        return task

    def downgrade(self, task):
        """ Downgrade app """
        task.success()
        return task


class CustomWorker2(CustomWorker1):
    pass
