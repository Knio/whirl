import pathlib
import logging
import datetime
import dateutil.tz
import time
import threading

import dominate
import whirl

from dominate import tags, util
from dominate.tags import *

import task_store # pwd


dx = whirl.domx.dx

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)s] %(message)s')


root = pathlib.Path(__file__).parent

task_fn = root / 'tasks.toml'
tasks = []
tasks_time = 0

def save():
  task_store.dump(tasks, task_fn)
  tasks_time = task_fn.stat().st_mtime


def load():
  global tasks_time
  global tasks

  if task_fn.stat().st_mtime == tasks_time:
    return
  tasks = task_store.load(task_fn)
  tasks_time = task_fn.stat().st_mtime
  log.info(repr(tasks))

load()

def load_check():
  while 1:
    load()
    time.sleep(1)


load_th = threading.Thread(target=load_check)
load_th.daemon = True
load_th.start()


def new_task_id():
  return 'task-' + datetime.datetime.utcnow().strftime('%G.%V.%u%H%M%S')[2:]

@whirl.domx.template
class kniodo(dominate.document):
  def __init__(self, _title='', *a, **kw):
    title = 'KnioDo'
    if _title:
      title += ' - ' + _title
    super(kniodo, self).__init__(title, *a, **kw)

    self.head += link(rel="stylesheet", href="https://cdn.simplecss.org/simple.min.css")
    # self.head += link(rel="stylesheet", href="https://unpkg.com/@picocss/pico@1.5.3/css/pico.min.css")

    self.head += style(util.include(root / 'kniodo.css'))

    # wrappers for pico
    self['data-theme'] = 'dark'
    container = main(cls='container')
    self.body += container
    self._entry = container



@whirl.domx.route('/')
def index(url, handler, match):
  div('Hello world')

  button('test', dx(target='#test', get='/test'))
  button('stop', dx(target='#test', get='/stop'))


  div(id='test')

  div(add_task(), id='task_insert')
  view_tasks()


@whirl.domx.route('/stop')
def route_content(url, handler, match):
  raise KeyboardInterrupt


@whirl.domx.route('/test')
def route_content(url, handler, match):
  return div('foobar')


@whirl.domx.route('/tasks')
def route_tasks(*args):
  return view_tasks()


@whirl.domx.route(r'/task/(.+)$')
def route_task(url, handler, match):
  task_id = match.group(1)
  return view_task(task_id)


@div(id='tasks')
def view_tasks():
  # TODO toposort
  for task_id in reversed(tasks.keys()):
    view_task(task_id)

@details(cls='task')
def view_task(task_id):
  html_id = task_id.replace('.', '-')
  attr(id=html_id)
  task = tasks[task_id]

  body = task['body'].split('\n', 1)
  local = task['created'].astimezone(dateutil.tz.tzlocal())

  with summary():
    # button('☑')
    # TODO move to finished
    input_(
      dx(target='#' + html_id, get='/finish/' + task_id, outer=True),
      type='checkbox',
      checked=task['finished'])
    util.text(body[0])
    span(local.strftime('%y-%m-%d %H:%M')[3:])
    span(task['created'].strftime('%G.%V')[2:])
    span(' ' .join(task['contact']))

  with code(cls='body'):
    p(body[1] if len(body) > 1 else '')

  pre(repr(task))


@div(id='new')
def add_task():
  with form():
    textarea(name='body')
    textarea(name='contact')
    button('+', dx(target='#task_insert', get='/new', outer=True))


@whirl.domx.route('/new')
def new(url, handler, match):
  # TODO impliment post reading
  # body = handler.rfile.read()

  task = dict(
    created = datetime.datetime.now(tz=datetime.timezone.utc),
    finished = False,
    active = True,
    active_time = 0,
    sort_after = False,
    contact = map(str.strip, url.args['contact'].split('\n')),
    body = url.args['body'],
  )
  tid = new_task_id()
  tasks[tid] = task

  save()

  add_task()
  div(id='task_insert')
  view_task(tid)


@whirl.domx.route(r'/finish/(.+)$')
def route_finish(url, handler, match):
  task_id = match.group(1)
  task = tasks[task_id]
  task['finished'] = datetime.datetime.now(tz=datetime.timezone.utc)

  save()






whirl.domx.main()

