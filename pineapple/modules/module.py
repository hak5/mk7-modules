import os
import socket
import json
import abc
import logging
import functools
import signal
from typing import Tuple, Any, Callable, Optional

from pineapple.logger import get_logger
from pineapple.modules.request import Request


class Module:

    def __init__(self, name: str, log_level: int = logging.WARNING):
        """
        :param name: The name of the module. Example `cabinet`
        :param log_level: The level of logging you wish to show. Default WARNING
        """
        self.logger = get_logger(name, log_level)  # logger for feedback.
        self.name = name  # the name of the module

        self.logger.debug(f'Initializing module {name}.')

        self._running: bool = False  # set to False to stop the module loop

        self._module_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)  # api requests will be received over this socket
        self._module_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._module_socket_path = f'/tmp/{name}.sock'  # apth to the socket

        # if the socket already exists attempt to delete it.
        try:
            os.unlink(self._module_socket_path)
        except OSError:
            if os.path.exists(self._module_socket_path):
                self.logger.error('Could not remove existing socket!')
                raise FileExistsError('Could not remove existing socket!')

        # If a SIGINT is received preform a clean shutdown by calling `shutdown()`
        signal.signal(signal.SIGINT, self.shutdown)

    def _receive(self) -> Optional[dict]:
        """
        Receive data over a socket and attempt to json deserialize it.
        If the deserialization fails, None will be returned
        :return: A dictionary containing the data received over the socket or None if json deserialization fails.
        """
        connection, _ = self._module_socket.accept()
        data = connection.recv(4096)
        decoded_data = data.decode('utf-8')

        try:
            return json.loads(decoded_data)
        except ValueError:
            self.logger.warning('Non-JSON Received')

        return None

    def _json_to_bytes(self, message) -> bytes:
        """
        json deserialize a message and then decode it.
        Use this to convert your json message to bytes before publishing it over the socket
        :param message: A json serializable list or a dict
        :return: bytes
        """
        if not (type(message) is list or type(message) is dict):
            self.logger.error(f'Expected a list or dict but got {type(message)} instead.')
            raise TypeError(f'Expected a list or dict but got {type(message)} instead.')

        d = json.dumps(message)
        return d.encode('utf-8')

    def _publish(self, message: bytes):
        """
        Publish a message `message` to over `_module_socket`.
        Call this method to respond to a request.
        :param message: Bytes of a message that should be sent
        :return: None
        """

        self.logger.debug('Accepting on module socket')
        connection, _ = self._module_socket.accept()

        try:
            self.logger.debug(f'Sending response {str(message, "utf-8")}')
            connection.sendall(message)
        except ValueError:
            self.logger.error('Could not send response!')

    def start(self):
        """
        Main loop for the module which will run as long as `_running` is True.
        This will listen for data coming over `_module_socket` and deserialize it to a `Request` object.
        That object is then passed to `handle_request` for further processing.

        If an exception is thrown, this loop will stop working and attempt to do a clean shutdown of the module by
        calling `shutdown`.
        :return: None
        """
        self.logger.info('Starting module...')

        self.logger.debug(f'Binding to socket {self._module_socket_path}')
        self._module_socket.bind(self._module_socket_path)
        self._module_socket.listen(1)
        self.logger.debug('Listening on socket!')

        self._running = True
        while self._running:
            try:
                request_dict: Optional[dict] = self._receive()
                if not request_dict:
                    self.logger.debug("Received non-json data over the socket.")
                    continue

                self.logger.debug('Processing request.')
                request = Request()
                request.__dict__ = request_dict
                self.handle_request(request)
            except OSError as os_error:
                self.logger.warning(f'An os error occurred: {os_error}')
            except Exception as e:
                self.logger.critical(f'A fatal `{type(e)}` exception was thrown: {e}')
                self.shutdown()

    def shutdown(self, sig=None, frame=None):
        """
        Attempt to clean shutdown the module.
        If your module has anything it needs to close or otherwise cleanup upon shutdown, please override this
        and do what you need to here. Be sure you call `super.shutdown()` in your new implementation.

        This method may also be called to handle signals such as SIGINT. If it was called as a signal handler the
        signal `sig` and frame `frame` will be passed into this method.
        :param sig: Optional signal that triggered a signal handler
        :param frame: Optional frame
        :return: None
        """
        self.logger.info(f'Shutting down module. Signal: {sig}')
        self._running = False
        self._module_socket.close()

    def notify(self, level: int, message: str) -> bool:
        """
        Send a notification over the WiFi Pineapples notification socket

        :param level: Notification level
        :param message: Notification message
        :param module_name: The name of the calling module
        :return: bool
        """
        notify_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        notify_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        notify_socket_path = '/tmp/notifications.sock'

        module_notification = {'level': level, 'message': message, 'module_name': self.name}
        socket_message = self._json_to_bytes(module_notification)
        status = True

        try:
            notify_socket.connect(notify_socket_path)
        except ValueError:
            self.logger.error('Could not connect to notifications socket!')
            return False

        try:
            notify_socket.sendall(socket_message)
        except ValueError:
            self.logger.error('Could not send notification!')
            status = False

        notify_socket.close()

        return status

    @abc.abstractmethod
    def handle_request(self, request: Request):
        """
        Each time a request is made, this method will be invoked with that request passed in.
        Your module MUST Implement this method to handle requests.

        The request object `request` will have an `action`, `module` and whatever other fields are passed from the
        web app on it.
        :param request: The request to handle
        :return: None
        """
        raise NotImplementedError()

    @staticmethod
    def respond(func: Callable[[Any], Tuple[bool, Any]]):
        """
        A decorator to automatically publish the return value of a function to the socket.
        Simply add `@respond` to use it.

        The decorated function must return a tuple with a boolean as the first value and
        whatever your response data is as the second value.

        If the value of the boolean is True then `payload` will be in response object with your data in it.
        Example: { "payload": {"directories": ["/var", "/lib", "/root"]}}

        If the value if the boolean is False then `error` will be in the object with your data as the value.
        Example: { "error": "No directory found with that name" }
        :param func: The function to decorate
        :return:
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            module: Module = args[0]
            module.logger.debug('Picked up response...')
            success, data = func(*args, **kwargs)

            response_dict = {}

            if success:
                response_dict['payload'] = data
            else:
                response_dict['error'] = data

            message_bytes = module._json_to_bytes(response_dict)
            module._publish(message_bytes)

        return wrapper
