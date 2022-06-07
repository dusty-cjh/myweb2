# shellcheck disable=SC2046
# shellcheck disable=SC2006

# stop web instance
OLD_INSTANCE_PID=`netstat -anp | grep 9090 | awk '{print $7}' | grep -E -e '^[0-9]+' -o`
if [ $OLD_INSTANCE_PID ]
then
  echo "[build] killing old instance: $OLD_INSTANCE_PID}"
  kill -9 $OLD_INSTANCE_PID
else
  echo "[build] no running instance"
fi


# run
(gunicorn myweb2.wsgi:application -w 3 -k gthread -b 127.0.0.1:9090 --max-requests=1024 &)

#
