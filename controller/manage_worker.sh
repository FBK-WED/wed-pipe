#!/usr/bin/env bash



echo Stopping all first ...
ps aux | grep celeryd | awk '{print $2}' | xargs kill -9
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
webui/manage.py celery worker --app scheduler.scheduler --events --loglevel=info > celeryworker.log 2>&1 || { echo "Celeryd Server start failed"; exit 1; } &
echo Started celeryd with PID $!

echo Starting CeleryCam ...
webui/manage.py celerycam > celerycam.log 2>&1 || { echo "CeleryCam start failed"; exit 1; } &
echo Started CeleryCam with PID $!
echo CeleryCam ready
