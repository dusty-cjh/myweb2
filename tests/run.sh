
HOST=localhost:8000

curl -i -XPOST -F 'file=@../media/test.jpg' "http://$HOST/resource/upload_image/"
