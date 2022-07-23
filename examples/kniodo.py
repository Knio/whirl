import pathlib
import logging

import dominate
import whirl
import toml

from dominate import tags, util
from dominate.tags import *
# from whirl.domx import dx
dx = whirl.domx.dx

log = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)s] %(message)s')

class Todo:
  def __init__(self):
    self.tasks = {}
    self.load_tasks(pathlib.Path('./tasks'))

  def load_tasks(self, root):
    for p in root.glob('*.toml'):
      log.info('loading %s', p)
      t = toml.load(p)
      i = t['id']
      self.tasks[i] = t

todo = Todo()




@whirl.domx.route('/')
def index(url, handler, match):
  pg = dominate.document('KnioDo')
  with pg:
    div('Hello world')
    button('test', dx(target='#test', get='/test'))
    div(id='test')

    div(id='task_insert')
    view_tasks()

    add_task()


  return pg

@whirl.domx.route('/test')
def content(url, handler, match):
  return div('foobar')


@whirl.domx.route('/tasks')
def tasks(*args):
  return view_tasks()


@whirl.domx.route(r'/task/(\w+)')
def tasks(url, handler, match):
  task_id = match.group(1)
  return view_task(task_id)


@div(id='tasks')
def view_tasks():
  for task_id in todo.tasks.keys():
    view_task(task_id)


@div
def view_task(task_id):
  attr(id='task_{task_id}')
  pre(repr(todo.tasks[task_id]))

@div(id='new')
def add_task():
  with form():
    textarea(name='body', rows=10, cols=81)
    input_(type='text', name='contact')
    button('+', dx(target='#task_insert', get='/new', outer=True))


@whirl.domx.route('/new')
def new(url, handler, match):
  # TODO impliment post reading
  # body = handler.rfile.read()
  return whirl.domx.container(
    div(id='task_insert'),
    div('new new new', repr(url.args)),
  )


whirl.domx.main()

