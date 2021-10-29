# 待实现的需求

A. 预览图编辑：类似微信公众号，可上传并裁剪图片

在Admin中文章编辑页嵌入A，并在文章保存时自动生成Summary实例

在Admin中Summary编辑页嵌入A

微信公众号回复Resource名获取下载链接，且该链接仅24小时有效

制作商品详情页，并在上面售卖自己的二手物品

编译Qt2020，使用C++协程编写事件循环，制作高并发静态文件服务器并测试性能

# 待解决的BUG

#### SimpleUI 无法自定义action

在UserAdmin中总是无法获取当前对象的ID，导致无法提交action
> 正常的url：http://localhost/admin/auth/user/1157/
> 目前的结果：http://localhost/admin/auth/user/None

解决方式：在admin中添加simple ui的ajax admin，呵呵，真是个小傻逼

#### 无法使用Rest Test模块
报错：
> RuntimeError: Model class django.contrib.contenttypes.models.ContentType doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS.

解决：PyCharm中未给Tests配置settings，配置好后就可以了


#### rest_framework在Nginx下无法正确路由接口

总会出现：http://backend/<api-path> 这样的情况

# 文件结构

目录名     |       内容      
-------|----------
media   | 前端多媒体文件
media / js | javascript文件
media / icon | 图标文件
media / material | 物料（后端文件上传目录）
templates  | 前端html代码
templates / base.html | 网页基本模板
templates / post | 博客代码
templates / post / index.html | 博客首页
templates / post / about.html | 关于我
templates / post / shop.html | 商店
templates / post / support.html | 支持一下
其余目录 | 后端代码文件


# 如何部署？

> 注：此处省略关于Nginx、Gunicorn等外部工具的配置

本项目后台基于Django SimpleUI，版本要求Django==3.1.8，SimpleUI==latest
1. 必须使用django3.0+版本
2. 替换目录<code>django/contrib/auth/</code>下的<code>user.py</code>和<code>admin.py</code>

为了不影响其他项目的使用，须首先[建立虚拟环境](https://docs.python.org/zh-cn/3/library/venv.html)
```sh
python3 -m venv <venv root>
source <venv root>/bin/activate
```

安装包依赖

```py 
pip install -r <proj root>/requirements.txt
```

部署Django数据库
```py 
python3 manage.py makemigrations && python3 manage.py migrate
```

# 前端文件管理器
名称 | 优点 | 缺点
----|-----|-----
[ckfinder](https://ckeditor.com/ckfinder/demo/) | 最先进 | 文档晦涩
[xayah](https://learnku.com/articles/24285) | 基于VUE、结构简单 | 不靠谱
[django-filebrowser](https://github.com/sehmaschine/django-filebrowser) | 开箱即用 | 难以拓展
[django-filer](https://github.com/divio/django-filer) | 集成度高 | 功能不完善

# 搭建属于本项目的MySQL数据库

```mysql
create database myweb2 character set 'utf8mb4';
create user 'cjh'@'%' identified by '123456';
grant all on myweb2.* TO 'cjh'@'%';
```

# 个人商店开发

Goods表包含：
商品id，首页预览图，标题，内容，价格，数量

Order表包含：
商品id，数量，状态，用户名

# 启动命令

```shell script
cd $PROJ_ROOT
gunicorn myweb2.wsgi:application -w 3 -k gthread -b 127.0.0.1:9090 --max-requests=1024
```