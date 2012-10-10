"""
Celery client configuration.

See: http://docs.celeryproject.org/en/latest/configuration.html
"""

#BROKER_URL = "amqp://guest:guest@localhost:5672//"
#CELERY_IMPORTS = ("scheduler.scheduler", )
#CELERY_RESULT_BACKEND = "amqp"
#CELERY_TASK_RESULT_EXPIRES = 3600


from __future__ import absolute_import

from celery import Celery

celery = Celery(
	'scheduler',
	broker='amqp://guest:guest@localhost:5672/',
	backend='amqp://guest:guest@localhost:5672/',
	include=['scheduler.scheduler'])

# Optional configuration, see the application user guide.
celery.conf.update(
	CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
	celery.start()

