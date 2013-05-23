# pylint: disable=E1103,R0904,C0111,C0103,E1101,C0302,W0232,R0201,W0212

from mock import MagicMock

from django.utils import unittest

from webui.scheduler.admin import SchedulerAdmin
from webui.scheduler.models import Scheduler


class TestAdmin(unittest.TestCase):
    def test_SchedulerAdmin_status_renderer(self):
        scheduler = MagicMock()
        schedulerAdmin = SchedulerAdmin(Scheduler, MagicMock())
        scheduler.status = 'S'
        self.assertEqual('<font color="green">Success</font>',
                         schedulerAdmin.status_renderer(scheduler))
        scheduler.status = 'I'
        self.assertEqual('<font color="yellow">Invalid</font>',
                         schedulerAdmin.status_renderer(scheduler))
        scheduler.status = 'F'
        self.assertEqual('<font color="red">Fail</font>',
                         schedulerAdmin.status_renderer(scheduler))
        scheduler.status = 'R'
        self.assertEqual('<font color="orange">Running</font>',
                         schedulerAdmin.status_renderer(scheduler))
