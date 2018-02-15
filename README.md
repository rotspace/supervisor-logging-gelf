Supervisor-logging
==================

A [supervisor] plugin to stream events to an external Graylog instance.

Installation
------------

```
git clone https://github.com/peterfroehlich/supervisor-logging.git
cd supervisor-logging
python setup.py install
```

Usage
-----

Script allow to parse logs with next format:
`Edatetime filename.go:1: log body`

I.e. `D2018/02/15 10:31:07 orders.go:168: order callback was finished success order=1078 old_status=9 new_status=10 duration=1.857546628s`. This fork supports only `logging.DEBUG` and `logging.ERROR` levels (log line should begin with one the letters `D` or `E`).

The Graylog server to send the events to is configured with the environment
variables:

* `GRAYLOG_SERVER`
* `GRAYLOG_PORT`

Add the plugin as an event listener:

```
[eventlistener:logging]
command = supervisor_logging
events = PROCESS_LOG
```

Enable the log events in your program:

```
[program:yourprogram]
stdout_events_enabled = true
stderr_events_enabled = true
```

[supervisor]: http://supervisord.org/
