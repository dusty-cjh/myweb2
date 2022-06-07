from myweb2.celery import app


@app.task
def say_hello(msg):
    ret = 'hello {}'.format(msg)
    print(ret)
    return ret


