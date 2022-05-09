# MyBot PRD

## auto_approve - 自动通过

### request handler

* 加好友请求、申请加群请求、邀请加群请求，全部自动通过。
* 为了规避 tx 的风控，对加群请求进行排队，每 10s 通过一条。

#### 对燕山大学校园加群申请进行自动验证

1. 当用户申请加群时，自动通过
2. 主动给用户通过群聊发送临时会话，请求返回姓名和学号
```text
注意！
本消息为Ji器人例行公事，非真人。

你可以直接留言，管理员看到会回复。
```
```text
hello,
我是{group_name}的群管理。

为防止营销号、广告进入，
本群已开启实名认证。

请回复我：姓名+学号，
例如：202011010704，李小明

10min 内验证失败将踢出群聊呦~
```
3. 验证失败可以重试一次，再次失败后踢出群聊
   1. 内容无数字
```text
您所发的消息不含学号！请重新发送
```
```text
验证失败！
您还有一次重试机会
```

4. 验证超过 2min 没有成功，则踢出群聊

5. 群管理可通过命令 `auto_approve ysu_check [target_qq_number]` 来主动对成员进行身份验证

6. 自动检索 pending 状态的加群请求，并依次处理

Tech Design:

curl 请求：
```shell
curl -X POST --location "http://202.206.243.8/StuExpbook/AutoCompleteServletSrtp" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "word=2018110&index=4&currentPage=1&sql=stuSql&building=undefined&srtp_teacher_project_num=undefined&planyear=undefined"
```
response:
```xml
<words>
    <word>201811050349-徐梓坤</word>
    <val>201811050349</val>
    <word>201811050348-张薇格</word>
    <val>201811050348</val>
    <word>201811050347-仲洋杰</word>
    <val>201811050347</val>
    <word>201811050346-闫语</word>
    <val>201811050346</val>
    <word>201811050345-戴佳岑</word>
    <val>201811050345</val>
    <word>201811050344-赵妹</word>
    <val>201811050344</val>
    <word>201811050343-柴哲鹏</word>
    <val>201811050343</val>
    <word>201811050388-李亮</word>
    <val>201811050388</val>
    <word>201811050387-马孟娇</word>
    <val>201811050387</val>
    <word>201811050386-韩欢</word>
    <val>201811050386</val>
    <page>&lt;div style="float: right;" &gt;第1/501页&lt;a href="#"
        onclick="pageTo('3','stuSql','undefined','undefined','undefined','4')"&gt; &gt;&gt;&lt;/a&gt;&lt;/div&gt;
    </page>
</words>
```

#### Next step 

今日校园是否允许开发者接入？
通过姓名 + 学号的方式查询该同学是否在本校，最终自动验证通过。

Tech Design:

1. 使用正则从验证消息中获取学号: `(\d+)`
2. 通过学号查询对应学校，查看是否存在该用户
3. 使用 `username in validation_message` 的方式，验证用户是否为本校学生
4. 为防止同一个学号重复被使用，有两条解决方案
   1. 缓存已被使用过的学号，7 天内不允许重复使用
   2. 存到数据库里，并 `unique key (user_id, school_id)`，如果有账号被冒名顶替 / 小号加群，则只能联系 admin 操作 DB 解决。

### message handler

* only handle message having `自动通过` or `auto_approve` prefix
* only allow guys in whitelist or root manager to execute command

#### add manager

syntax:
> (自动通过|auto_approve)(add|监听)[groupid]

add [groupid] to monitor list if provided, else means start global monitor

> (自动通过|auto_approve)(del|取消)[groupid]

delete [groupid] from monitor list if provided, else means stop global monitor
 
> (自动通过|auto_approve)(ls|列表)

show current monitoring group list

> (自动通过|auto_approve)(ls|列表)

