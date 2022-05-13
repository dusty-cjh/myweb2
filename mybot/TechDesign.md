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
