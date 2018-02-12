These are not meant to be runnable code - but just the end of alot of Research
Right now i am figuring out the right framework for the job

Should we be focusing on celery of python redis queue for 
task queing for the extraction of the data from sources

8888888888888888888888888888888888888



@task                                                                                             
def fetch(pattern, src):                                                                                  
    fetcher = LogFetcher(pattern)                                                                         
    return fetcher.register(src, fetcher.fetch(src)).id                                                   
                                                                                                          
                                                                                                          
@task                                                                                             
def convert_tsv_blocks(tsv_id_list):                                                                                                                    
    return group([aggregate.s(tsv_id) for tsv_id in                             
                  tsv_id_list])()                                                                
                                                                                                          
                                                                                                          
process_file = fetch.s() | to_tsv.s() | convert_tsv_blocks.s()                               
                                                                                                          
                                                                                                          
@task                                                                                             
def update_pattern(pattern):                                                                              
    return group([process_file(pattern, src) for src, _ in                            
LogFetcher(pattern).list_new()])


___________________________________________________

 tasks.py
from time import sleep
from celery.utils.log import get_task_logger
from celery.decorators import task
from celery import group, chain
from django.apps import apps
from django.utils import timezone

logger = get_task_logger(__name__)

@task()
def execute_analysis(id_):
    task1 = startup_task.si(id_)
    task2 = group(parallel_task.si(i) for i in range(10))
    task3 = reducer_task.si(id_)
    return chain(task1, task2, task3)()


@task()
def startup_task(id_):
    logger.info('-----> starter task started')
    sleep(2)
    logger.info('-----> starter task complete')


@task()
def parallel_task(id_):
    logger.info('-------> parallel task started %s' % id_)
    sleep(2)
    logger.info('-------> parallel task complete %s' % id_)


@task
def reducer_task(id_):
    logger.info('-----> reducer task started')
    sleep(2)
logger.info('-----> reducer task complete')



___________________________________________________

https://stackoverflow.com/questions/17461374/celery-stop-execution-of-a-chain

workflow = chain(
    t.task1.s(),
    chord(
        [
            t.task2.s(),
            chain(
                t.task3.s(),
                chord(
                    [t.task4.s(), t.task5.s()],
                    t.task6.s()
                ),
                t.task3.s()
            )
        ],
        t.task7.s()
    )
)

This is for linear execution of a chain thats non parallel

 run.py
from celery import chain

from django.core.management.base import BaseCommand

from . import tasks


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        source_file = args[0]
        chain(
            tasks.fetch.s(source_file),         # Fetch data from remote source
            tasks.blacklist.s(),                # Remove blacklisted records
            tasks.transform.s(),                # Transform raw data ready for loading
            tasks.load.s(),                     # Load into DB
        ).apply_async()
tasks.py
import shutil


# os.rename("path/to/current/file.foo", "path/to/new/desination/for/file.foo")
# shutil.move("path/to/current/file.foo", "path/to/new/destination/for/file.foo")
# this is the shutil man

import os

from celery import task


@task()
def fetch(fixture_path):
    """
    Fetch a file from a remote location
    """
    destination = "/tmp/source.csv"
    print "Fetching data from %s - saving to %s" % (fixture_path, destination)
    shutil.copyfile(fixture_path, destination)
    return destination


@task()
def blacklist(source_path):
    base, ext = os.path.splitext(source_path)
    destination = "%s-afterblacklist%s" % (base, ext)
    print "Transforming data in %s to %s" % (source_path, destination)
    shutil.copyfile(source_path, destination)
    return destination


@task()
def transform(source_path):
    base, ext = os.path.splitext(source_path)
    destination = "%s-transformed%s" % (base, ext)
    print "Transforming data in %s to %s" % (source_path, destination)
    shutil.copyfile(source_path, destination)
    return destination


@task()
def load(filepath):
    print "Loading data in %s and removing" % filepath
os.remove(filepath)



https://gist.github.com/jmhobbs/5358101


___________________________________________________
 main.py
from foo import add
from time import sleep

job = add.delay(1, 2)

print("i do some other stuff")


sleep(3)

print(job.result)
worker.py
from rq.decorators import job
from redis import Redis
from time import sleep


@job('default', connection=Redis(), timeout=100)
def add(x, y):
    sleep(2)
return x + y


https://gist.github.com/spjwebster/6521272

________________________-


 rqretryworker.py
#!/usr/bin/env python

import os, sys
sys.path.append(os.getcwd())

import logging
import rq

MAX_FAILURES = 3

logger = logging.getLogger(__name__)

queues = None

def retry_handler(job, exc_type, exc_value, traceback):
    job.meta.setdefault('failures', 0)
    job.meta['failures'] += 1

    # Too many failures
    if job.meta['failures'] >= MAX_FAILURES:
        logger.warn('job %s: failed too many times times - moving to failed queue' % job.id)
        job.save()
        return True

    # Requeue job and stop it from being moved into the failed queue
    logger.warn('job %s: failed %d times - retrying' % (job.id, job.meta['failures']))

    for queue in queues:
        if queue.name == job.origin:
            queue.enqueue_job(job, timeout=job.timeout)
            return False

    # Can't find queue, which should basically never happen as we only work jobs that match the given queue names and
    # queues are transient in rq.
    logger.warn('job %s: cannot find queue %s - moving to failed queue' % (job.id, job.origin))
    return True


with rq.Connection():
    queues = map(rq.Queue, sys.argv[1:]) or [rq.Queue()]
_____________________________________________________________

 python-rq with tornado asynchronous
jobs.py
#!/usr/bin/env python
# encoding: utf-8

import time

def test(interval):
    for i in xrange(int(interval)):
        print i
        time.sleep(1)

        return interval
main.py
#!/usr/bin/env python
# encoding: utf-8

# http://tornadogists.com/3849257/

import tornado.ioloop
import tornado.httpserver
import tornado.web
import tornado.gen
import redis
import tornado.options
from rq import Queue
import jobs

r = redis.Redis()

@tornado.gen.coroutine
def get_result(job):
    while True:
        yield tornado.gen.sleep(0.1)
        if job.result is not None or job.status == 'failed':
            break
    raise tornado.gen.Return(job)


class IndexHandler(tornado.web.RequestHandler):

    @tornado.gen.coroutine
    def get(self, interval=10):

        q = Queue(connection=r)

        job = q.enqueue(jobs.test)
        job = yield get_result(job)

        self.write(str(job.result))


if __name__ == '__main__':
    tornado.options.parse_command_line()
    application = tornado.web.Application(handlers=[
        (r"/(\d+)", IndexHandler)
    ], debug=True)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8881)

tornado.ioloop.IOLoop.instance().start()

https://gist.github.com/cloverstd/9fd590f683c80cdf6255#file-main-py-L30

_____________________________________________________________


