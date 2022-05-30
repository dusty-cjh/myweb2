## onebot plugin configuration admin

## async message handling 

1。 
`lpush` message into Redis list while it's coming.

job instance will create an async future to wait for new message coming, 

event loop will enquiry Redis list every 5 seconds to get fresh data.

2. every server instance will publish new message to rabbitMQ,

job instance will create a temporary listening queue and try to consume new message during session is active, after that, queue will be closed.

2.1 could I get only one message per operation when announced a consumer ?

try to get user message, if not exist, `asleep` for a while and try again

## background

currently we got no plugin config admin, we need that.

our existing plugin load strategy is to iterate each file or dir in plugin dir.
and then import it as a module

we're import plugin config using 

## async job

pseudo code 

```python3
@async_task(
    job_name='cjh',
    max_lifetime=300,
    use_db=True,
    max_retry=3,
)
async def my_async_job(*args, **kwargs):
    await some_task()
    msg = await get_message(user_id=432432, group_id=432432532)
    pass
```

```
event loop 
|
|

```
