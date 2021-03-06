from django.db import models


class PostBase(models.Model):
    STATUS_VISIBLE = 1
    STATUS_INVISIBLE = 2
    STATUS = (
        (STATUS_VISIBLE, '可见'),
        (STATUS_INVISIBLE, '不可见'),
    )

    title = models.CharField(verbose_name='标题', max_length=50)
    content = models.TextField(verbose_name='正文')
    status = models.PositiveSmallIntegerField(verbose_name='状态', choices=STATUS, default=STATUS_VISIBLE)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    class Meta:
        ordering = ['-created_time']
        abstract = True

    def __str__(self):
        return self.title


class Post(PostBase):
    class Meta:
        verbose_name = verbose_name_plural = '文章'


class Goods(PostBase):
    price = models.FloatField(verbose_name='价格')
    previews = models.CharField(verbose_name='商品预览', max_length=640)
    visit = models.PositiveIntegerField(verbose_name='访问量', default=0)
    sales = models.PositiveIntegerField(verbose_name='销量', default=0)

    class Meta:
        verbose_name = verbose_name_plural = '商品'

    def get_previews(self):
        return self.previews.split('*')


class Summary(models.Model):
    TYPE_POST = 1
    TYPE_PICT = 2
    TYPE_VIDEO = 3
    TYPE_AUDIO = 4
    TYPE_SHOP =5
    TYPE = (
        (TYPE_POST, '文章'),
        (TYPE_PICT, '照片'),
        (TYPE_VIDEO, '视频'),
        (TYPE_AUDIO, '音频'),
        (TYPE_SHOP, '商品'),
    )

    type = models.PositiveSmallIntegerField(verbose_name='类型', choices=TYPE)
    url = models.CharField(verbose_name='链接', max_length=200)
    created_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    title = models.CharField(verbose_name='标题', max_length=50)
    desc = models.CharField(verbose_name='描述', max_length=200)
    recommend = models.BooleanField(verbose_name='是否推荐', default=False, help_text='如果作为推荐，则加入推荐系统')
    mainpage = models.BooleanField(verbose_name='是否首页可见', default=False, help_text='是否首页可见，否则只能在后台看到')
    preview = models.CharField(verbose_name='预览', help_text='图/音视频', max_length=200)

    class Meta:
        verbose_name = verbose_name_plural = '摘要'
        ordering = ['-created_time']

    def __str__(self):
        return self.title

    @classmethod
    def get_mainpage(cls):
        return cls.objects.filter(mainpage=True)

    @classmethod
    def get_recommend(cls):
        return cls.objects.filter(recommend=True)