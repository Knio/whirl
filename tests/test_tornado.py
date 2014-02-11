import logging

from whirl.tornado_server import *

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Example usage
    @get('^/$')
    def index(request):
        return 'Hello World'

    @get('^/u/([a-z0-9]+)$')
    def user(request, name):
        return 'Hi, %s' % name

    server.run()

