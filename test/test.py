import contextlib
import os
import os.path
import re
from sortest import *


def eq(a, b):
    assert a == b, "%s != %s" % (a, b)


@contextlib.contextmanager
def tmp_file_context(path, contents=""):
    d = os.path.dirname(path)
    if not os.path.exists(d):
        os.makedirs(d)
    with file(path, "w") as f:
        print >> f, contents,
    yield
    os.unlink(path)


def test_tmp_file_context(contents=""):
    f = "/tmp/foo/bar/ssglarch.py"
    with tmp_file_context(f, contents=contents):
        assert os.path.exists(f)
        eq(contents, file(f).read())
    assert not os.path.exists(f)


def test_nonempty_tmp_file_context():
    test_tmp_file_context("""\
import os.path
a = 1
""")


## Learning tests for nose.util.getpackage:

def test_module_path_1():
    path = "/tmp/test_project/test_module/__init__.py"
    with tmp_file_context(path):
        eq("test_module", nose.util.getpackage(path))


def test_module_path_2():
    with tmp_file_context("/tmp/test_project/test_module/__init__.py"):
        path = "/tmp/test_project/test_module/foo.py"
        with tmp_file_context(path):
            eq("test_module.foo", nose.util.getpackage(path))
