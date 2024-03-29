import argparse
import http.server
import logging
import pathlib
import re
import socketserver
import sys
import traceback

import dominate
import toml
from dominate import tags, util


import whirl
# from whirl import domx_server

log = logging.getLogger(__name__)
static_root = pathlib.Path(__file__).parent


# TODO move to dominate.utils
class container(dominate.dom_tag.dom_tag):
  def _render(self, sb, *a, **kw):
    self._render_children(sb, *a, **kw)
    return sb


class dx(tags.dom_tag):
  pass


# this is exported as whirl.domx
class DomxServer(
    socketserver.ThreadingMixIn,
    http.server.BaseHTTPRequestHandler):
  dx = dx
  container = container

  template_cls = dominate.document
  routes = []

  @classmethod
  def template(cls, t):
    cls.template_cls = t
    return t

  @classmethod
  def route(cls, route, cb=None):
    if cb:
      cls.routes.append((route, cb))
    else:
      def add(cb):
        cls.routes.append((route, cb))
        return cb
      return add


  @classmethod
  def run(cls, addr=('', 8888)):
    class SS(socketserver.TCPServer):
      def handle_timeout(self):
        super().handle_timeout()
        raise TimeoutError

    httpd = SS(addr, cls, bind_and_activate=False)
    httpd.allow_reuse_address = True
    httpd.daemon_threads = True
    httpd.timeout = 0.1
    httpd.server_bind()
    httpd.server_activate()
    log.info('Serving at {}'.format(addr))
    try:
      while 1:
        try:
          # httpd.serve_forever() # poll_timeout doesnt work
          httpd.handle_request()
        except TimeoutError as e:
          pass
        except KeyboardInterrupt as e:
          log.info(f'Stopping server: {e!r}')
          break
    finally:
      httpd.server_close()



  @classmethod
  def main(cls, ip='', port=8888):
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)s] %(message)s')
    parser = argparse.ArgumentParser(
      description=__doc__,
      formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--port', type=int)
    parser.add_argument('--ip', type=str)
    args = parser.parse_args()

    cls.run((args.ip or ip, args.port or port))


  def do_GET(self):
    return self.do('get')


  def do_POST(self):
    return self.do('post')


  def do(self, method):
    host = self.headers.get('Host', '')
    url = whirl.url(self.path)

    xhr = False
    parts = list(url.path.parts)
    if len(parts) > 1 and parts[1] == 'domx':
      del parts[1]
      parts[0] = ''
      url = whirl.url(url, path='/'.join(parts))
      xhr = True

    r = 200
    cb, *args = self.match(str(url.path))
    if not cb:
      r = 404
      d = self.page_error(r, 'Page Not Found')
    else:
      try:
        with container() as c:
          d = cb(url, self, *args)
        if not d:
          d = c
        self.domxify(d)
      except Exception as e:
        log.exception('Internal Server Error')
        r = 500
        d = self.page_error(r, 'Internal Server Error',
          tags.div(
            tags.h1(type(e).__name__ + ': ' + str(e)),
            tags.pre(traceback.format_exc())))

    if not xhr:
      if not isinstance(d, dominate.document):
        doc = self.template_cls(str(url))
        doc += d
        d = doc
      d.head += tags.script(util.include(static_root / 'domx' / 'domx.js'))
      d.head += tags.style( util.include(static_root / 'domx' / 'domx.css'))

    self.send_response(r)
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(d.render().encode('utf-8'))

  def match(self, path):
    for q, cb in self.routes:
      if type(q) is str:
        m = re.match(q + '$', str(path))
        if not m: continue
        return cb, m
    return (None,)


  def page_error(self, code, msg='', body=None):
    d = self.template_cls(f'{code} {msg}')
    d += body or msg
    return d


  def domxify(self, node):
    for i in node.children:
      if not isinstance(i, tags.dom_tag):
        continue
      if isinstance(i, dx):
        if 'get' in i.attributes:
          method = 'get'
          path = i['get']
        elif 'post' in i.attributes:
          method = 'post'
          path = i['post']
        else:
          raise ValueError('no domx method specified')
        outer =  int(bool(i.attributes.get('outer')))
        target = i.attributes.get('target', 'this')
        event = i.attributes.get('event', 'onclick')
        before = i.attributes.get('before')
        after = i.attributes.get('after')

        before = f"(function(){{{before}}})" if before else 'null'
        after = f"(function(){{{after}}})" if after else 'null'

        # todo onsubmit, etc for different types
        node[event] = (
          f"return dx.replace("
          f"this, '{target}', "
          f"'/domx{path}', "
          f"'{method}', {outer}, {before}, {after}"
          ");"
        )
        node.children.remove(i)
      self.domxify(i)

