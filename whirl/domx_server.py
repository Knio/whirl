
import http.server
import logging
import socketserver
import pathlib
# import sys

import dominate
from dominate import tags, util
import whirl

log = logging.getLogger(__name__)
root = pathlib.Path(whirl.__path__[0])

class Page:
  def __init__(self, document):
    self.document = document

  def __call__(self, *args, **kwargs):
    return self.index(*args, **kwargs)

class x(tags.dom_tag): pass

def make_page(app, uri):
  doc = dominate.document()
  inline = False
  doc.head += tags.script(util.include(root / 'domx' / 'domx.js'))
  doc.head += tags.style( util.include(root / 'domx' / 'domx.css'))
  page = app(doc)
  try:
    # router
    for p in uri.path.split('/'):
      if p == '':
        continue
      if p == '_domx':
        inline = True
        continue
      page = getattr(page, p)
  except AttributeError:
    raise ValueError(404)
  # render page
  tags.pre(repr(page))
  with doc:
    page()

  # dxify
  def walk(node):
    for i in node.children:
      if not isinstance(i, tags.dom_tag):
        continue
      if not isinstance(i, x):
        walk(i)
        continue
      # it's a x() marker
      # todo onsubmit, etc for different types
      node['onclick'] = "dx.replace('{}', '{}');".format(
        i['target'],
        '/_domx' + i['get'],
      )
      node.children.remove(i)

  walk(doc.body)
  if inline:
    return doc.body.children[0]
  else:
    return doc


@dominate.document('Internal Server Error')
def page_error():
  import traceback
  tags.pre(traceback.format_exc())


class DomxRequestHandler(socketserver.ThreadingMixIn, http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    host = self.headers.get('Host', '')
    uri = whirl.url(self.path)
    r = 200
    try:
      d = make_page(self.app, uri)
    except:
      d = page_error()
      r = 500

    self.send_response(r)
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(d.render().encode('utf-8'))

def run(app_, addr=('', 8888)):
  class RH(DomxRequestHandler):
    app = app_
  httpd = socketserver.TCPServer(addr, RH, bind_and_activate=False)
  httpd.allow_reuse_address = True
  httpd.daemon_threads = True
  httpd.server_bind()
  httpd.server_activate()
  log.info('Serving at {}'.format(addr))
  try:
    httpd.serve_forever()
  except KeyboardInterrupt:
    log.info('Stopping server')
  finally:
    httpd.server_close()


def main():
  logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s:%(levelname)s:%(filename)s:%(funcName)s:%(lineno)s] %(message)s')
  parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawTextHelpFormatter)
  parser.add_argument('--port', default=8888, type=int)
  parser.add_argument('--ip', default='', type=str)
  args = parser.parse_args()
  run((args.ip, args.port))

if __name__ == '__main__':
  main()
