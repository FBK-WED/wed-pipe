#!/usr/bin/env bash



echo Stopping all first ...
ps aux | grep celery | grep -v grep | awk '{print $2}' | xargs -r kill -9
# rabbitmqctl stop
echo Stop done

if [ "$1" == 'stop' ]; then
	echo Stop completed
	exit 0
fi

# echo Starting RabbitMQ ...
# rabbitmq-server -detached > rabbitmq-server.log 2>&1 || { echo "RabbitMQ Server start failed"; exit 1; }
# echo Rabbitmq Started

echo Starting Worker ...
./manage.py celery worker --events --loglevel=info > celeryworker.log 2>&1 || { echo "Celery workers start failed or stopped"; exit 1; } &
echo Started celery worker with PID $!

echo Starting CeleryCam ...
./manage.py celerycam > celerycam.log 2>&1 || { echo "Celery cam start failed or stopped"; exit 1; } &
echo Started celery cam with PID $!
