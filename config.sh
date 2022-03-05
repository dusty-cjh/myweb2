#!/bin/bash


# global variable
nginx_conf="/www/server/nginx/conf/nginx.conf"
nginx_conf_root="/www/server/panel/vhost/nginx/"
myweb2_conf="${nginx_conf_root}myweb2.conf"

function cfg_help(){
  echo "    nginx        Will open the nginx.conf"
  echo "    myweb2       Will open the myweb2.conf"
  echo "    reload       Will reload nginx configuration"
  echo "    -new [file]  Will create a new nginx config in $nginx_conf_root"
  echo "    runserver    Will start server by gunicorn in daemon process"
}


case $1 in
-h)
  cfg_help
  ;;
nginx)
  echo "opening file: $nginx_conf"
  vim $nginx_conf
  ;;
myweb2)
  echo "opening file: $myweb2_conf"
  vim $myweb2_conf
  ;;
reload)
  echo "start reload nginx config"
  nginx -s reload
  ;;
-new)
  if [ $2 ]
  then
    vim "${nginx_conf_root}$2"
  else
    echo "Please enter a new config file name"
  fi
  ;;
runserver)
  (gunicorn myweb2.wsgi:application -w 3 -k gthread -b 127.0.0.1:9090 --max-requests=1024 &)
  ;;
*)
  echo "You can use bellow:"
  cfg_help
  ;;
  esac
