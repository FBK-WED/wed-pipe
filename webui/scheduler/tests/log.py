# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212

import logging

import simplejson as json
from mock import patch, MagicMock

from webui.scheduler.log import get_redis_logger
from webui.tests import TestCase


class GetRedisLoggerTestCase(TestCase):
    def test_it_pushes_to_redis(self):
        identity = MagicMock(return_value='testkey')
        logger = logging.getLogger('test_logger')
        logger.handlers = []
        get_task_logger = MagicMock(return_value=logger)
        redis = MagicMock()
        Redis = MagicMock(return_value=redis)

        with patch.multiple(
            'webui.scheduler.log',
            Redis=Redis,
            get_redis_key=identity,
            get_task_logger=get_task_logger
        ):
            logger_ = get_redis_logger('test')
            logger_.info('LOG THIS')

            self.assertEqual(redis.rpush.call_count, 1)
            self.assertEqual(redis.rpush.call_args[0][0], 'testkey')
            record = json.loads(redis.rpush.call_args[0][1])
            self.assertEqual(record['msg'], 'LOG THIS')
