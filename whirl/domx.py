import argparse
import http.server
import io
import json
import logging
import pathlib
import re
import socketserver
import traceback
import typing

import dominate
from dominate import tags, util

try:
  import rich.traceback
except ImportError:
  rich = None

from .url import url

log = logging.getLogger(__name__)
static_root = pathlib.Path(__file__).parent


# TODO move to dominate.utils
class container(dominate.dom_tag.dom_tag):
  def _render(self, sb, *a, **kw):
    self._render_children(sb, *a, **kw)
    return sb


class dx(tags.dom_tag):
  pass


class HTTPError(RuntimeError):
  @classmethod
  def fromcode(cls, x):
    return cls(http.HTTPStatus(x))


# this is exported as whirl.domx
class DomxServer(
    socketserver.ThreadingMixIn,
    http.server.BaseHTTPRequestHandler):
  dx = dx
  container = container
  httperror = HTTPError.fromcode

  template_cls = dominate.document
  routes = []

  class Path(typing.NamedTuple):
    q: str
    cb: typing.Callable
    type: str

  @classmethod
  def template(cls, t):
    cls.template_cls = t
    return t

  @classmethod
  def route(cls, route, *args, type=None, **kw):
    if args:
      # normal call
      cls.routes.append(DomxServer.Path(route, args[0], type, **kw))
    else:
      # decorator with args
      def add(cb):
        cls.routes.append(DomxServer.Path(route, cb, type, **kw))
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
    log.info(f'Serving at {addr}')
    try:
      while 1:
        try:
          # httpd.serve_forever() # poll_timeout doesnt work
          httpd.handle_request()
        except TimeoutError:
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
    u = url(self.path)

    # TODO get rid of this convention and clean up request type handling
    xhr = False
    parts = list(u.path.parts)
    if len(parts) > 1 and parts[1] == 'domx':
      del parts[1]
      parts[0] = ''
      u = url(u, path='/'.join(parts))
      xhr = True

    r = 200
    content_type = 'text/html'

    try:
      route, match = self.match(str(u.path))
      if not route:
        raise HTTPError.fromcode(404)

      if route.type == 'json':
        d = json.dumps(route.cb(u, self, *match.groups()), sort_keys=True, indent='  ')
        content_type = 'application/json'

      else:
        with container() as c:
          d = route.cb(u, self, *match.groups())
        if not d:
          d = c
        self.domxify(d)

        if not xhr: # wrap d in the page template
          if not isinstance(d, dominate.document):
            doc = self.template_cls(str(u))
            doc += d
            d = doc
          d.head += tags.script(util.include(static_root / 'domx' / 'domx.js'))
          d.head += tags.style( util.include(static_root / 'domx' / 'domx.css'))

    except Exception as e:
      r = 500
      if isinstance(e, HTTPError):
        e = e.args[0]
        phrase = e.phrase
        description = e.description
      else:
        r = 500
        phrase = type(e).__name__ + ': ' + str(e)
        description = ''

      with tags.div() as tb:
          tags.h1(phrase)
          tags.p(description)
          if rich:
            # rtb = rich.traceback.Traceback()
            out = io.StringIO()
            con = rich.console.Console(
              file=out,
              record=True,
              width=200,
            )
            con.print_exception(
                show_locals=True,
                width=200,
            )
            util.raw(con.export_svg(code_format='''
              <svg class="rich-terminal" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
                  <style>
                    @font-face {{
                        font-family: "Fira Code";
                        src: local("FiraCode-Regular"),
                                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Regular.woff2") format("woff2"),
                                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Regular.woff") format("woff");
                        font-style: normal;
                        font-weight: 400;
                    }}
                    @font-face {{
                        font-family: "Fira Code";
                        src: local("FiraCode-Bold"),
                                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff2/FiraCode-Bold.woff2") format("woff2"),
                                url("https://cdnjs.cloudflare.com/ajax/libs/firacode/6.2.0/woff/FiraCode-Bold.woff") format("woff");
                        font-style: bold;
                        font-weight: 700;
                    }}
                    .{unique_id}-matrix {{
                        font-family: Fira Code, monospace;
                        font-size: {char_height}px;
                        line-height: {line_height}px;
                        font-variant-east-asian: full-width;
                    }}
                    .{unique_id}-title {{
                        font-size: 18px;
                        font-weight: bold;
                        font-family: arial;
                    }}
                    {styles}
                  </style>

                  <defs>
                    <clipPath id="{unique_id}-clip-terminal">
                      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" />
                    </clipPath>
                    {lines}
                  </defs>

                  <g transform="translate({terminal_x}, {terminal_y})" clip-path="url(#{unique_id}-clip-terminal)">
                  {backgrounds}
                    <g class="{unique_id}-matrix">
                      {matrix}
                    </g>
                  </g>
              </svg>'''))
          else:
            tags.pre(traceback.format_exc())

      d = self.page_error(r, tb)


    self.send_response(r)
    self.send_header('Content-Type', f'{content_type}; charset=utf-8')
    self.end_headers()
    self.wfile.write(str(d).encode('utf-8'))

  def match(self, path):
    for route in self.routes:
      m = re.match(route.q + '$', str(path))
      if not m: continue
      return route, m
    return None, None


  def page_error(self, code, body=None):
    s = http.HTTPStatus(code)
    msg = f'{code} {s.phrase} {s.description}'
    d = self.template_cls(msg)
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
        outer   =  int(bool(i.attributes.get('outer')))
        target  = i.attributes.get('target', 'this')
        event   = i.attributes.get('event', 'onclick')
        before  = i.attributes.get('before')
        after   = i.attributes.get('after')

        before  = f"(function(){{{before}}})" if before else 'null'
        after   = f"(function(){{{after}}})" if after else 'null'

        # todo onsubmit, etc for different types
        node[event] = (
          f"return dx.replace(event, "
          f"this, '{target}', "
          f"'/domx{path}', "
          f"'{method}', {outer}, {before}, {after}"
          ");"
        )
        node.children.remove(i)
      self.domxify(i)
