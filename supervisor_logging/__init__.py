#!/usr/bin/env python
#
# Copyright 2014  Infoxchange Australia
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Forked from https://github.com/infoxchange/supervisor-logging and modified to log to graylog by Peter Froehlich
#

"""
Send received events to graylog over GELF/UDP.
"""

from __future__ import print_function

import logging
import logging.handlers
import os
import sys
import re

import graypy

# log format "D2018/02/15 10:31:07 orders.go:168: order callback was finished success order=1078 old_status=9 new_status=10 duration=1.857546628s"
#
# returns D
#         filename.go
#         linenumber
#         tail data
split_regex = re.compile("(D|E).* ([\w]+.go):([\d]{1,5}): (.*)")

def get_headers(line):
    """
    Parse Supervisor message headers.
    """

    return dict([x.split(':') for x in line.split()])


def eventdata(payload):
    """
    Parse a Supervisor event.
    """

    headerinfo, data = payload.split('\n', 1)
    headers = get_headers(headerinfo)
    return headers, data


def supervisor_events(stdin, stdout):
    """
    An event stream from Supervisor.
    """

    while True:
        stdout.write('READY\n')
        stdout.flush()

        line = stdin.readline()

        headers = get_headers(line)

        payload = stdin.read(int(headers['len']))
        event_headers, event_data = eventdata(payload)

        yield event_headers, event_data

        stdout.write('RESULT 2\nOK')
        stdout.flush()


def split_msg_and_get_log_level(event_data, level_match):
    """
    Strip out syslog timestamp and try to match the level to the syslog level
    """

    match_obj = level_match.match(event_data)

    # D/E
    try:
        if match_obj.group(1) == "D":
            level = logging.DEBUG
        else:
            level = logging.ERROR
    except IndexError:
        level = logging.DEBUG

    # filename.go
    try:
        filename = match_obj.group(2)
    except IndexError:
        filename = ""

    # lineno
    try:
        lineno = match_obj.group(3)
    except IndexError:
        lineno = 0

    # body
    try:
        body = match_obj.group(4)
    except IndexError:
        body = event_data

    return level, filename, lineno, body


def main():

    env = os.environ

    try:
        host = env['GRAYLOG_SERVER']
        port = int(env['GRAYLOG_PORT'])

    except KeyError:
        sys.exit("GRAYLOG_SERVER and GRAYLOG_PORT are required.")

    sys.stderr.write("Starting with host: %s, port: %d" % (host, port))
    sys.stderr.flush()

    handler = graypy.GELFHandler(host, port)

    for event_headers, event_data in supervisor_events(sys.stdin, sys.stdout):
        level, filename, lineno, body = split_msg_and_get_log_level(event_data, split_regex)

        event = logging.LogRecord(
            name=event_headers['processname'],
            level=level,
            pathname=filename,
            lineno=lineno,
            msg=body,
            args=(),
            exc_info=None,
            )
        event.process = int(event_headers['pid'])
        handler.handle(event)


if __name__ == '__main__':
    main()
