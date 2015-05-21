ciex (alpha)
=========
a simple, lightweight and probably dumb CI system, written in Python.

**To extend it**, write your own python `ci workers` modules, then define them in the daemon's configuration file.

**An example** scenario would be to install the `ciex daemons` on multipe machines, then trigger the checkout command or build, upgrade, etc from another machine, say after you're pushing new code to the master branch.

# Quickstart
 Note: You need [nanomsg](https://github.com/nanomsg/nanomsg) installed on your system.

```shell
$ pip install ciex
$ ciexd --config /path/to/config/ciex.config
$ ciextl ping
pong
```

# Installation
If you have have [nanomsg](https://github.com/nanomsg/nanomsg) installed on your system, the installation should be pretty easy.

**Requirements**

* [nanomsg](https://github.com/nanomsg/nanomsg) - requirement for nanoservice
* [nanoservice](https://github.com/walkr/nanoservice) - for interprocess comm.
* [oi](https://github.com/walkr/oi) - for command line interface


**Install options**

```shell
# Using pip
$ pip install ciex

# Or using the makefile
$ git clone git@github.com:walkr/ciex.git
$ cd ciex
$ make install
```


# High level overview

The system has two separate components:

1. A daemon process `ciexd`
2. A command line interface `ciexctl`


### 1. Daemon

The daemon is running continuously awaiting for commands.
When a command is received, it is tranformed into a task,
then it is placed onto the `new queue`. **CI Workers** take tasks
from the `new queue` and do their work. When the work associated
with that task is finished, the CI Worker will mark the task as
`success` OR `failure`, then it will send it back to the task router.

The daemon accepts a configuration file, where you can define the settings
for each of your apps, as different apps have different needs.

**Example config file**

```ini
[settings.app.my_app]
localpath = /apps/my_app
repo = git@github.com:walkr/test.git

worker_dirpath = /apps/myapp/ci
worker_modname = workers
worker_classname = CustomWorker
```

**Starting the daemon**

```shell
$ ciexd --config /etc/ciex.config  # optional --debug flag
```


### 2. Command line interface

The command line interface accepts commands and forwards them to the daemon

**Usage Example:**

```shell
$ ciextl ping
pong

$ ciexctl
ctl > list
['appname1', 'appname2']

ctl > status appname1
<Task app_name:appname1, command:checkout, status:TaskStatus.success>

ctl > upgrade appname1
Task triggered ...

ctl > status appname1
<Task app_name:appname, command:upgrade, status:TaskStatus.pending>

# While a task is running, you cannot fire up another task
ctl > upgrade appname1
Deny. Taks already running
```


That's it. Enjoy!

**MIT License**