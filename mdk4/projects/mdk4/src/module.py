#!/usr/bin/env python3

import subprocess
import logging
import pathlib
import os
from datetime import datetime

from typing import List, Tuple, Optional

from pineapple.helpers.opkg_helpers import OpkgJob
from pineapple.modules import Module, Request
from pineapple.helpers import network_helpers as net
from pineapple.helpers import opkg_helpers as opkg
import pineapple.helpers.notification_helpers as notifier
from pineapple.jobs import Job, JobManager


# CONSTANTS
_HISTORY_DIRECTORY_PATH = '/root/.mdk4'
_HISTORY_DIRECTORY = pathlib.Path(_HISTORY_DIRECTORY_PATH)
# CONSTANTS

module = Module('mdk4', logging.DEBUG)
job_manager = JobManager('mdk4', logging.DEBUG)


class Mdk4Job(Job[bool]):

    def __init__(self, command: List[str], file_name: str, input_interface: str, output_interface: str):
        super().__init__()
        self.file_name = file_name
        self.command = command
        self.mdk4_file = f'{_HISTORY_DIRECTORY_PATH}/{file_name}'
        self.input_interface = input_interface
        self.output_interface = output_interface

    def do_work(self, logger: logging.Logger) -> bool:
        logger.debug('mdk4 job started.')

        monitor_input_iface = None
        monitor_output_iface = None
        output_file = open(self.mdk4_file, 'w')

        if self.input_interface and self.input_interface != '' and self.input_interface[-3:] != 'mon':
            logger.debug(f'starting monitor mode on interface {self.input_interface}')
            if os.system(f'airmon-ng start {self.input_interface}') == 0:
                for index, substr in enumerate(self.command):
                    if substr == self.input_interface:
                        self.command[index] = f'{self.input_interface}mon'
                        monitor_input_iface = f'{self.input_interface}mon'
            else:
                self.error = 'Error starting monitor mode for input interface.'
                return False

        if self.output_interface and self.output_interface != '' and self.output_interface[-3:] != 'mon':
            logger.debug(f'starting monitor mode on interface {self.output_interface}')
            if os.system(f'airmon-ng start {self.output_interface}') == 0:
                for index, substr in enumerate(self.command):
                    if substr == self.output_interface:
                        self.command[index] = f'{self.output_interface}mon'
                        monitor_output_iface = f'{self.output_interface}mon'
            else:
                self.error = 'Error starting monitor mode for output interface.'
                return False

        logger.debug(f'Calling mdk4 and writing output to {self.mdk4_file}')
        subprocess.call(self.command, stdout=output_file, stderr=output_file)
        logger.debug('Mdk4 Completed.')

        if monitor_input_iface:
            logger.debug(f'stopping monitor mode for interface {monitor_input_iface}')
            os.system(f'airmon-ng stop {monitor_input_iface}')
        if monitor_output_iface:
            logger.debug(f'stopping monitor mode for interface {monitor_output_iface}')
            os.system(f'airmon-ng stop {monitor_output_iface}')

        return True


def _make_history_directory():
    if not _HISTORY_DIRECTORY.exists():
        _HISTORY_DIRECTORY.mkdir(parents=True)


def _get_last_background_job() -> dict:
    last_job_id: Optional[str] = None
    last_job_type: Optional[str] = None
    last_job_info: Optional[str] = None

    if len(job_manager.jobs) > 0:
        last_job_id = list(job_manager.jobs.keys())[-1]
        last_job = job_manager.get_job(last_job_id, remove_if_complete=False)
        if type(last_job) is Mdk4Job:
            last_job_type = 'mdk4'
            last_job_info = last_job.file_name
        elif type(last_job) is OpkgJob:
            last_job_type = 'opkg'
        else:
            last_job_type = 'unknown'

    return {
        'job_id': last_job_id,
        'job_type': last_job_type,
        'job_info': last_job_info
    }


def _notify_dependencies_finished(job: OpkgJob):
    if not job.was_successful:
        module.send_notification(job.error, notifier.ERROR)
    elif job.install:
        module.send_notification('Mdk4 finished installing.', notifier.INFO)


@module.handles_action('poll_job')
def poll_job(request: Request) -> Tuple[bool, dict]:
    job = job_manager.get_job(request.job_id)

    if not job:
        return False, 'No job found by that id'

    return True, {'is_complete': job.is_complete, 'result': job.result, 'job_error': job.error}


@module.handles_action('start')
def start(request: Request) -> Tuple[bool, dict]:
    command = request.command.split(' ')

    filename = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}"
    job_id = job_manager.execute_job(Mdk4Job(command, filename, request.input_iface, request.output_iface))

    return True, {
        'job_id': job_id,
        'output_file': filename
    }


@module.handles_action('stop')
def stop(request: Request) -> Tuple[bool, str]:
    if os.system('killall -9 mdk4') == 0:
        return True, 'Mdk4 stopped.'
    else:
        return False, 'Error stopping Mdk4.'


@module.handles_action('load_history')
def load_history(request: Request) -> Tuple[bool, List[str]]:
    return True, [item.name for item in _HISTORY_DIRECTORY.iterdir() if item.is_file()]


@module.handles_action('load_output')
def load_output(request: Request) -> Tuple[bool, str]:
    output_path = f'{_HISTORY_DIRECTORY_PATH}/{request.output_file}'
    if not os.path.exists(output_path):
        return False, 'Could not find scan output.'

    with open(output_path, 'r') as f:
        return True, f.read()


@module.handles_action('delete_result')
def delete_result(request: Request) -> Tuple[bool, bool]:
    output_path = pathlib.Path(f'{_HISTORY_DIRECTORY_PATH}/{request.output_file}')
    if output_path.exists() and output_path.is_file():
        output_path.unlink()

    return True, True


@module.handles_action('clear_history')
def clear_history(request: Request) -> Tuple[bool, bool]:
    for item in _HISTORY_DIRECTORY.iterdir():
        if item.is_file():
            item.unlink()

    return True, True


@module.handles_action('check_dependencies')
def check_dependencies(request: Request) -> Tuple[bool, bool]:
    return True, opkg.check_if_installed('mdk4', module.logger)


@module.handles_action('manage_dependencies')
def manage_dependencies(request: Request) -> Tuple[bool, dict]:
    return True, {
        'job_id': job_manager.execute_job(OpkgJob('mdk4', request.install), callbacks=[_notify_dependencies_finished])
    }


@module.handles_action('startup')
def startup(request: Request) -> Tuple[bool, dict]:
    return True, {
        'has_dependencies': opkg.check_if_installed('mdk4', module.logger),
        'interfaces': net.get_interfaces(),
        'last_job': _get_last_background_job()
    }


if __name__ == '__main__':
    _make_history_directory()
    module.start()
