import logging

try:
    from whirl.tornado_server import *
except ImportError:
    server = None

if __name__ == '__main__' and server:
    logging.basicConfig(level=logging.DEBUG)

    # Example usage
    @get('^/$')
    def index(request):
        return 'Hello World'

    @get('^/u/([a-z0-9]+)$')
    def user(request, name):
        return 'Hi, %s' % name

    server.run()

