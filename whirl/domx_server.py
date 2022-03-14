
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
  pass


@dominate.document
def make_page(app, path):
  tags.h1('Hellp')
  tags.pre(repr(path))


@dominate.document('Internal Server Error')
def page_error():
  import traceback
  tags.pre(traceback.format_exc())


class Server(socketserver.ThreadingMixIn, http.server.BaseHTTPRequestHandler):
  def do_GET(self):
    host = self.headers.get('Host', '')
    path = whirl.url(self.path)
    r = 200
    try:
      d = make_page(self.app, path)
    except:
      d = page_error()
      r = 500

    d.head += tags.script(util.include(root / 'domx' / 'domx.js'))
    d.head += tags.style( util.include(root / 'domx' / 'domx.css'))

    self.send_response(r)
    self.send_header('Content-Type', 'text/html; charset=utf-8')
    self.end_headers()
    self.wfile.write(d.render().encode('utf-8'))

  @classmethod
  def run(cls, app, addr=('', 8888)):
    httpd = socketserver.TCPServer(addr, cls, bind_and_activate=False)
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

  Server.run((args.ip, args.port))

run = Server.run

if __name__ == '__main__':
  main()
