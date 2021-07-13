#!/usr/bin/env python3

import os
import glob
import base64
import pathlib
import logging
import subprocess

import pineapple.helpers.opkg_helpers as opkg
import pineapple.helpers.notification_helpers as notifier

from datetime import datetime
from pineapple.jobs import Job, JobManager
from pineapple.modules import Module, Request
from pineapple.helpers.opkg_helpers import OpkgJob

# CONSTANTS

_LOGGING = logging.DEBUG

_OPKG_INSTALL_SSLSPLIT = 'sslsplit'

_CERTIFICATE_FILE = '/root/sslsplit/openssl/self-signed_certificate.crt'
_CERTIFICATE_FILE_PATHLIB = pathlib.Path(_CERTIFICATE_FILE)

_GENERATE_CERTIFICATE_SCRIPT = '/pineapple/modules/sslsplit/assets/scripts/generate-certificate.sh'
_START_SSLSPLIT_SCRIPT = '/pineapple/modules/sslsplit/assets/scripts/start-sslsplit.sh'
_STOP_SSLSPLIT_SCRIPT = '/pineapple/modules/sslsplit/assets/scripts/stop-sslsplit.sh'

_LOGS_DIRECTORY = '/root/sslsplit/logs/'
_LOGS_DIRECTORY_PATHLIB = pathlib.Path(_LOGS_DIRECTORY)

# OBJECTS

module = Module('sslsplit', _LOGGING)

job_manager = JobManager(
    name='sslsplit', 
    module=module, 
    log_level=_LOGGING
)

# CLASSES

class BashJob(Job[bool]):

    def __init__(self, argument: str):
        super().__init__()
        self.argument = argument

    def do_work(self, logger: logging.Logger) -> bool:
        subprocess.call(['/bin/bash', self.argument])
        return True

# EVENTS

@module.on_start()
def on_start():
    return True

@module.on_shutdown()
def on_shutdown():
    return True

# EXTRAS

# NOTIFICATIONS

def notify_dependencies_installed(job: OpkgJob):
    if not job.was_successful:
        module.send_notification(job.error, notifier.ERROR)
    else:
        module.send_notification('SSLsplit installed', notifier.INFO)   

# HANDLES

@module.handles_action('check_dependencies')
def check_dependencies(request: Request):
    module.logger.debug('[+] sslsplit-module : Check required dependencies')
    sslsplit_installed = opkg.check_if_installed(_OPKG_INSTALL_SSLSPLIT, module.logger)
    return {
        'dependency_sslsplit': sslsplit_installed
    }

@module.handles_action('install_dependencies')
def install_dependencies(request: Request):
    module.logger.debug('[+] sslsplit-module : Install required dependencies')
    job_id = job_manager.execute_job(OpkgJob(_OPKG_INSTALL_SSLSPLIT, True), callbacks=[ notify_dependencies_installed ])
    return {
        'job_id': job_id
    }

@module.handles_action('poll_dependencies')
def poll_dependencies(request: Request):
    job_id = request.job_id
    is_complete = False
    if len(job_manager.jobs) >= 1:
        for job, runner in job_manager.jobs.items():
            if job == job_id and runner.job.is_complete:
                is_complete = True
                break
    return {
        'is_complete': is_complete
    }

@module.handles_action('check_certificate')
def check_certificate(request: Request):
    module.logger.debug('[+] sslsplit-module : Check required certificate')
    selfSigned_certificate_generated = _CERTIFICATE_FILE_PATHLIB.exists()
    return {
        'certificate_sslsplit': selfSigned_certificate_generated
    }

@module.handles_action('generate_certificate')
def generate_certificate(request: Request):
    module.logger.debug('[+] sslsplit-module : Generate required certificate')
    job_id = job_manager.execute_job(BashJob(_GENERATE_CERTIFICATE_SCRIPT))
    return {
        'job_id': job_id
    }

@module.handles_action('poll_certificate')
def poll_certificate(request: Request):
    job_id = request.job_id
    is_complete = False
    if len(job_manager.jobs) >= 1:
        for job, runner in job_manager.jobs.items():
            if job == job_id and runner.job.is_complete:
                is_complete = True
                break
    return {
        'is_complete': is_complete
    }

@module.handles_action('start_sslsplit')
def start_sslsplit(request: Request):
    job_id = job_manager.execute_job(BashJob(_START_SSLSPLIT_SCRIPT))
    return {
        'job_id': job_id
    }

@module.handles_action('poll_sslsplit')
def poll_sslsplit(request: Request):
    job_id = request.job_id
    is_complete = False
    if len(job_manager.jobs) >= 1:
        for job, runner in job_manager.jobs.items():
            if job == job_id and runner.job.is_complete:
                is_complete = True
                break
    return {
        'is_complete': is_complete
    }

@module.handles_action('stop_sslsplit')
def stop_sslsplit(request: Request):
    os.system(f'/bin/bash {_STOP_SSLSPLIT_SCRIPT}')
    return True

@module.handles_action('output_sslsplit')
def output_sslsplit(request: Request):
    # Fetch current log file : by date - by output - by process ?
    return {
        'sslsplit_output': "ABCD"
    }

@module.handles_action('check_logs')
def check_logs(request: Request):
    if _LOGS_DIRECTORY_PATHLIB.exists():
        logs = glob.glob(f'{_LOGS_DIRECTORY}*.log')
        return {
            'sslsplit_logs': logs
        }
    else:
        return {
            'sslsplit_logs': False
        }

@module.handles_action('view_log')
def view_log(request: Request):
    log = request.log
    with open(log, 'rb') as reader:
        content = base64.b64encode(reader.read())
        content = content.decode('ascii')
        return {
            'log_output': content
        }

@module.handles_action('delete_log')
def delete_log(request: Request):
    log = request.log
    os.remove(log)
    return True

if __name__ == '__main__':
    module.start()