import os
from django.shortcuts import reverse
from django.conf import settings
from common.constants import FFMPEG_CREATE_THUMBNAIL
from common.logger import Logger
from .models import Article, Summary

log = Logger('info')


def create_summary_from_article(art: Article, recommend=True, commit=True) -> Summary:
	# create default thumbnail
	preview = '/media/ckimage/default-thumbnail@640x280.jpg'
	# thumbnail_filename = os.path.join(settings.MEDIA_URL, 'thumbnail', f'art{art.id}.jpeg')
	# cmd = FFMPEG_CREATE_THUMBNAIL(thumbnail_filename)
	# try:
	# 	reader = os.popen(cmd)
	# except Exception as e:
	# 	log.error('create_summary_from_article os.popen error: {}', e)

	obj = Summary(
		type=Summary.TYPE_POST,
		url=reverse("post:article", args=(art.id,)),
		title=art.title,
		desc='',
		recommend=recommend,
		mainpage=True,
		preview=preview,	 # TODO generate preview
	)
	if commit:
		obj.save(force_insert=True)

	return obj
