from django.contrib import admin
from django.contrib.auth.models import Group
from django.http.response import JsonResponse
from simpleui.admin import AjaxAdmin

from .models import MyUser


@admin.register(MyUser)
class OneBookUserAdmin(AjaxAdmin):
	list_display = ['username', 'sex', 'province', 'city', '_groups', 'last_login', ]
	list_per_page = 80
	search_fields = ['username', 'remark', 'city', ]
	actions = ['act_modify_group', ]

	def _groups(self, obj):
		ret = ''
		for data in obj.groups.values('name'):
			ret += data['name']+'/'
		return ret[:-1]
	_groups.short_description = '所属组'

	def act_modify_group(self, request, queryset):
		data = dict(request.POST)
		remark = data['remark'][0]
		option = data['option'][0]

		groups = []
		for r in remark.split(';'):
			group, is_created = Group.objects.get_or_create(name=r)
			groups.append(group)

		ids = request.POST['_selected']
		if not ids:
			return JsonResponse(data={
				'status': 'error',
				'msg': '请先选中数据！'
			})
		queryset.filter(id__in=ids.split(','))

		if option == '添加':
			for obj in queryset:
				obj.groups.add(*groups)
				obj.save()
		elif option == '删除':
			for obj in queryset:
				obj.groups.remove(*groups)
				obj.save()

		return JsonResponse({
			'status': 'success',
			'msg': option + '成功！',
		})

	act_modify_group.short_description = '修改组'
	act_modify_group.confirm = '确定为这些用户修改组吗？'
	act_modify_group.short_description = '修改组'
	act_modify_group.type = 'success'

	# 指定一个输入参数，应该是一个数组

	# 指定为弹出层，这个参数最关键
	act_modify_group.layer = {
		# 这里指定对话框的标题
		'title': '添加组',
		# 提示信息
		'tips': '注意：多个标签以英文分号(;)隔开。',
		# 确认按钮显示文本
		'confirm_button': '确定',
		# 取消按钮显示文本
		'cancel_button': '取消',
		'width': '40%',
		'labelWidth': "80px",
		'params': [{
			'type': 'input',
			'key': 'remark',
			'label': '标签',
			'require': True
		}, {
			'type': 'radio',
			'key': 'option',
			'label': '操作',
			'require': True,
			'options': [{
				'key': '0',
				'label': '删除'
			}, {
				'key': '1',
				'label': '添加'
			}, ]
		}, ]
	}
