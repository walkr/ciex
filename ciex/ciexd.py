# ciex daemon

import oi

from . import core
from . import worker


def main():
    program = oi.Program('my program', 'ipc:///tmp/ciex.sock')
    program.workers.append(worker.CIControlWorker(program))
    ci_core = core.Core(program)

    program.add_command(
        'reload', ci_core.reload,
        'reload daemon core')

    program.add_command(
        'start', ci_core.start,
        'start app <appname>')

    program.add_command(
        'stop', ci_core.stop,
        'stop app <appname>')

    program.add_command(
        'deploy', ci_core.deploy,
        'deploy remote repo <appname>')

    program.add_command(
        'build', ci_core.build,
        'make build <appname>')

    program.add_command(
        'upgrade', ci_core.upgrade,
        'upgrade the app <appname>')

    program.add_command(
        'downgrade', ci_core.downgrade,
        'downgrade the app <appname>')

    program.add_command(
        'last', ci_core.last,
        'show last task <appname>')

    program.add_command(
        'list', ci_core.list,
        'list app names')

    program.add_command(
        'ping', lambda: 'pong',
        'ping daemon')

    program.run()


if __name__ == '__main__':
    main()
