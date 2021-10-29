from django.db import models
from wechatpy.replies import EmptyReply, TextReply, ImageReply, VideoReply, VoiceReply


class Content(models.Model):
    TEXT = 1
    IMAGE = 2
    AUDIO = 3
    VIDEO = 4
    CONTENT_TYPE = (
        (TEXT, '文本'),
        (IMAGE, '图片'),
        (AUDIO, '音频'),
        (VIDEO, '视频'),
    )

    name = models.CharField(max_length=20, verbose_name='名称')
    content = models.CharField(max_length=256, verbose_name='回复内容')
    content_type = models.SmallIntegerField(verbose_name='内容类型', choices=CONTENT_TYPE, default=TEXT)

    class Meta:
        verbose_name = verbose_name_plural = '消息内容'

    def __repr__(self):
        return '{}({})'.format(self.name, self.get_content_type_display())

    def __str__(self):
        return self.__repr__()

    def get_reply(self, msg):
        reply = EmptyReply()
        if self.content_type == self.TEXT:
            reply = TextReply(content=self.content, message=msg)
        elif self.content_type == self.IMAGE:
            reply = ImageReply(media_id=self.content, message=msg)
        elif self.content_type == self.AUDIO:
            reply = VoiceReply(media_id=self.content, message=msg)
        elif self.content_type == self.VIDEO:
            reply = VideoReply(media_id=self.content, message=msg)

        return reply


class WxAutoReply(models.Model):
    REPLY_ALL = 1
    REPLY_RANDOM = 0
    REPLY_TYPE = (
        (REPLY_RANDOM, '随机回复一条'),
        (REPLY_ALL, '全部回复'),
    )

    rule = models.CharField(max_length=20, unique=True, verbose_name='规则名称')
    keyword = models.CharField(max_length=20, unique=True, verbose_name='关键词')
    contents = models.ManyToManyField(Content, verbose_name='内容')
    reply_type = models.SmallIntegerField(verbose_name='回复方式', choices=REPLY_TYPE, default=REPLY_ALL)

    class Meta:
        verbose_name = verbose_name_plural = '自动回复'

    def __str__(self):
        return '{}/{}'.format(self.rule, self.keyword)


class Retail(models.Model):
    STATUS_WAIT_PAY = 1
    STATUS_PAYED = 2
    STATUS_REFUNDED = 3
    STATUS = (
        (STATUS_WAIT_PAY, '待付款'),
        (STATUS_PAYED, '已付款'),
        (STATUS_REFUNDED, '已退款'),
    )

    total_fee = models.PositiveIntegerField(verbose_name='实付款')
    out_trade_no = models.SlugField(max_length=64, verbose_name='微信订单号', default='', blank=True)
    status = models.PositiveIntegerField(verbose_name='订单状态', choices=STATUS, default=STATUS_WAIT_PAY, blank=True)
    created_time = models.DateTimeField(auto_now_add=True, blank=True)
    # ps = models.CharField(verbose_name='备注', default='', max_length=20)

    class Meta:
        verbose_name = verbose_name_plural = '零售订单'
        ordering = ['-created_time', '-total_fee', ]

    def __str__(self):
        return str(self.total_fee)
