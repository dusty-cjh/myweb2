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
*)
  echo "You can use bellow:"
  cfg_help
  ;;
  esac
