# ciex command line interface

import oi


def main():
    ctl = oi.CtlProgram('ctl program', 'ipc:///tmp/ciex.sock')
    ctl.run()


if __name__ == '__main__':
    main()
