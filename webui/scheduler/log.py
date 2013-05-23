"""
Custom logging handler and formatter that stores logs as json in redis lists.
"""

import logging
from hashlib import md5

import simplejson as json
from redis import Redis, RedisError

from celery.utils.log import get_task_logger


END = 'THIS MESSAGE ENDS THE OUTPUT'


def get_redis_key(task_id):
    """
    Given a string task_id, returns a prefixed stable redis key. Stable means
    that s1 == s2 => f(s1) == f(s2).
    """
    prefix = 'SCHEDULER_LOGS_'

    return prefix + md5(task_id).hexdigest()


class RedisFormatter(logging.Formatter):
    def format(self, record):
        """
        JSON-encode a record for serializing through redis.

        Convert date to iso format, and stringify any exceptions.
        """

        data = vars(record)

        # # serialize the datetime date as utc string
        # data['time'] = data['time'].isoformat()
        #
        # stringify exception data
        if data.get('exc_info'):
            data['exc_info'] = self.formatException(data['exc_info'])

        return json.dumps(data)


class RedisHandler(logging.Handler):
    def __init__(self, task_id, level=logging.NOTSET):
        logging.Handler.__init__(self, level)
        self.redis = Redis()
        self.task_id = task_id or ''
        # self.task_id = '1'
        self.formatter = RedisFormatter()

    def emit(self, record):
        redis = self.redis
        key = get_redis_key(self.task_id)
        # import pdb ; pdb.set_trace()

        try:
            redis.rpush(key, self.format(record))
        except RedisError:
            pass


def get_redis_logger(id_):
    loggy = get_task_logger(id_)
    loggy.setLevel(logging.DEBUG)
    loggy.propagate = False
    loggy.handlers = []
    loggy.addHandler(RedisHandler(id_))
    # for test purposes:
    # loggy.addHandler(logging.StreamHandler())
    return loggy
