import logging

import whirl.domx_server as dx
from dominate.tags import *

class Hello(dx.Page):
  @div
  def hello():
    h1('Hello world')


if __name__ == '__main__':
  logging.basicConfig(level=logging.DEBUG)
  dx.run(Hello)
