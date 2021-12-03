import os, re
import pathlib
import sys

WSA_ROOT = "/Users/jiahaochen/shopee/beeshop_web"
WSA_STATIC_ROOT = os.path.join(WSA_ROOT, "mall/static_dev")
WSA_TEMPLATES_ROOT = os.path.join(WSA_ROOT, "mall/templates")

SPM_ROOT = "/Users/jiahaochen/shopee/shopee_payment_module"
SPM_STATIC_ROOT = os.path.join(SPM_ROOT, "admin/static")
SPM_TEMPLATES_ROOT = os.path.join(SPM_ROOT, "admin/templates")

path_map = {
    'static': [WSA_STATIC_ROOT, SPM_STATIC_ROOT],
    'include': [WSA_TEMPLATES_ROOT, SPM_TEMPLATES_ROOT],
    'transify_js': [WSA_STATIC_ROOT, SPM_STATIC_ROOT],
}

django_raw = [x for x in """
{% extends 'buyer/wsa_base.html' %}
{% load staticfiles %}
{% load transify %}
{% block headscripts %}
{%static "jslib/libphonenumber.js" %}
{%static "jsutil/country.js" %}
{%static "jsutil/phone.js" %}
{% endblock %}
{% block content_head_notifications %}
{% if channel_notifications %}
{% include 'content_head_notifications.html' with notifications=channel_notifications %}
{% endif %}
{%endblock%}
{% block page_bottom %}
{% include 'rate_limit_loader_box.html' %}
{% endblock %}
{% extends 'buyer/base.html'  %}
{% load staticfiles %}
{% load transify %}
{% load common_tags %}
{% block content %}
{% transify 'text_please_ensure_correct' %}
{% transify 'label_name' %}
{% if LOCALE == "VN" %}tel{% else %}text{% endif %}' name='icno' maxlength=32 placeholder="{% transify 'label_icno' %}
{% if bank_account.ic_number %}{{ bank_account.ic_number }}{% else %}{{ bank_account.company_id }}{% endif %}
{% if LOCALE == "TW" %}
{% transify "label_birthday" %}
{% if not isShopee %}input-birthday-pc{% endif %}" type='date' name='birthday' id="input-birthday" placeholder="{% transify 'label_birthday' %}
{% if bank_account.extra_data.extra_info.tw_birthday %}
{% with bank_account.extra_data.extra_info.tw_birthday|to_datetime_with_division as birthday %}
{% endwith %}{% endif %}
{% transify 'label_residence_address' %}
{% include "seller/module/fill_address.html" with address=bank_account.address %}
{% endif %}
{% transify 'label_next' %}
{% endblock %}
{% block extrastyle %}
{%static "css/buyer/bank/add.css" %}
{% static "css/seller/module/fill_address.css" %}
{% endblock %}
{% block extrascripts %}
{% static "jslib/libphonenumber.js" %}
{% static "jsutil/BJphone.js" %}
{% static "jsutil/validators.js" %}
{% static "pagejs/seller/module/tw_address_zip_map.js" %}
{% transify_js "pagejs/seller/module/fill_address.js" %}
{% static "pagejs/common/custom_select_wrapper.js" %}
{% transify_js "pagejs/buyer/bank/fill_ic.js" %}
{% endblock %}
""".split('\n') if len(x)]

if __name__ == '__main__':
    m = re.compile(r'^\s*\{% *(\w+) [\"\'](.*)[\"\'] *(?:with .*)? *%\}\s*$')
    for line in django_raw:
        res = m.match(line)
        if res == None:
            if not ('if' in line or 'block' in line or 'with' in line or 'endif' in line or 'load' in line):
                print("line not match any tags: {}".format(line))
            continue
        tag_name, value = res.groups()
        # print(tag_name, value)

        # ignore useless tags
        if not tag_name in path_map:
            continue

        # mkdir recursively and copy file
        src_path, dst_path = [os.path.join(x, value) for x in path_map[tag_name]]
        if not os.path.exists(os.path.dirname(dst_path)):
            os.makedirs(os.path.dirname(dst_path), 0o775)
        print('cp {} {}'.format(src_path, dst_path))
        os.system('cp {} {}'.format(src_path, dst_path))
