from whirl import url

def test():
    print url()
    print url('/moo')
    print url('http://moo')
    print url('http:///moo')
    print url('http://moo.com')
    print url('http://moo.com/')
    print url('http://moo.com/foo')
    print url('http://moo.com/foo/bar/')
    print url('http://moo.com/foo/bar?')
    print url('http://moo.com/foo/bar/?var=1')
    print url('http://moo.com/foo/bar/?var=1&baz=dog')
    print url('http://moo.com/foo/bar/?var=1&baz=dog&var=3')
    print url('http://moo.com/foo/bar/?var=1&baz=dog&var=3#here')
    assert url('?moo=1')['moo'] == '1'
    print url(url('?moo=1'))
    print url(url('?moo=1')).update_args(bar=2)
