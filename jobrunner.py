#!/usr/bin/env python
"""Run all commands extracted from environment variables when they should."""

from __future__ import unicode_literals

import logging
import re
import smtplib
import sys

from datetime import datetime
from os import environ, path
from subprocess import CalledProcessError, check_output, STDOUT


logging.basicConfig(level=logging.INFO)

# Get expected periodicity from this script's placement
periodicity = path.basename(path.dirname(path.abspath(__file__)))
logging.info("Running %s jobs", periodicity)

# Get email settings
host = environ.get("SMTP_HOST")
port = environ.get("SMTP_PORT")
from_ = environ.get("EMAIL_FROM")
to = environ.get("EMAIL_TO")
subject = environ.get("EMAIL_SUBJECT")

# Get the commands we need to run
to_run = dict()
for key, when in environ.items():
    match = re.match(r"^JOB_(\d+)_WHEN$", key)
    if match and periodicity in when.split():
        njob = int(match.group(1))
        to_run[njob] = environ["JOB_{}_WHAT".format(njob)]

# Run commands in order
message = [
    "From: {}".format(from_),
    "To: {}\r\n".format(to),
]
failed = False
for njob, command in sorted(to_run.items()):
    start = datetime.now()
    logging.info("Running job %d: `%s`", njob, command)
    try:
        result = check_output(command, stderr=STDOUT, shell=True)
    except CalledProcessError as error:
        failed = True
        logging.exception("Failed!")
        result = str(error) + "\n" + error.output
    end = datetime.now()
    message += [
        "",
        "===================================",
        "Job {}: `{}`".format(njob, command),
        "Started: {!s}".format(start),
        "Finished: {!s}".format(end),
        "",
        result,
    ]


# Report results
if all((host, port, from_, to, subject)) and len(message) > 2:
    logging.info("Sending email report")
    message.insert(0, "Subject: {}".format(subject.format(
        periodicity=periodicity,
        result="ERROR" if failed else "OK",
    )))
    try:
        smtp = smtplib.SMTP(host, port)
        smtp.sendmail(from_, to, message.join("\r\n"))
    finally:
        smtp.quit()
else:
    logging.info("Finished")

if failed:
    sys.exit("At least one job failed")
