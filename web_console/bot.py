# -*- coding: utf-8 -*-
from __future__ import absolute_import

import logging
import re
import time

from six.moves import _thread
from web_console.manager import PluginsManager
from web_console.slackclient import SlackClient

from web_console import settings
from web_console.dispatcher import MessageDispatcher


class Bot(object):
    def __init__(self):
        self._client = SlackClient(
            settings.API_TOKEN,
            bot_icon=settings.BOT_ICON if hasattr(settings,
                                                  'BOT_ICON') else None,
            bot_emoji=settings.BOT_EMOJI if hasattr(settings,
                                                    'BOT_EMOJI') else None
        )
        self._plugins = PluginsManager()
        self._dispatcher = MessageDispatcher(self._client, self._plugins,
                                             settings.ERRORS_TO)

    def run(self):
        self._plugins.init_plugins()
        self._dispatcher.start()
        self._client.rtm_connect()
        _thread.start_new_thread(self._keepactive, tuple())
        logging.info('connected to slack RTM api')
        self._dispatcher.loop()

    def _keepactive(self):
        logging.info('keep active thread started')
        while True:
            time.sleep(30 * 60)
            self._client.ping()


def respond_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['respond_to'][
            re.compile(matchstr, flags)] = func
        logging.info('registered respond_to plugin "%s" to "%s"', func.__name__,
                    matchstr)
        return func

    return wrapper


def listen_to(matchstr, flags=0):
    def wrapper(func):
        PluginsManager.commands['listen_to'][
            re.compile(matchstr, flags)] = func
        logging.info('registered listen_to plugin "%s" to "%s"', func.__name__,
                    matchstr)
        return func

    return wrapper


# def default_reply(matchstr=r'^.*$', flags=0):
def default_reply(*args, **kwargs):
    """
    Decorator declaring the wrapped function to the default reply hanlder.

    May be invoked as a simple, argument-less decorator (i.e. ``@default_reply``) or
    with arguments customizing its behavior (e.g. ``@default_reply(matchstr='pattern')``).
    """
    invoked = bool(not args or kwargs)
    matchstr = kwargs.pop('matchstr', r'^.*$')
    flags = kwargs.pop('flags', 0)

    if not invoked:
        func = args[0]

    def wrapper(func):
        PluginsManager.commands['default_reply'][
            re.compile(matchstr, flags)] = func
        logging.info('registered default_reply plugin "%s" to "%s"', func.__name__,
                    matchstr)
        return func

    return wrapper if invoked else wrapper(func)
