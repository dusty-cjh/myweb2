## onebot plugin configuration admin

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
