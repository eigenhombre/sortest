# sortest

**Continuous testing in Python** with test sorting by execution speed,
  and with auto-restart from the beginning when files change.

For about nine months I have been using a [continuous testing
tool](https://github.com/eigenhombre/continuous-testing-helper/) I
wrote called `conttest`), in conjunction with
[Nose](https://nose.readthedocs.org/en/latest/), for continuous
testing of Python code.  Depending on what I'm working on, 
`conttest` automagically runs one, some or all of my automated tests,
whenever I save a file in my source tree.

The problem with this approach is that I either have to specify what
test I want it to run (very fast, but requires detailed work at the
command line), or let it run all my tests, which at the moment clock
upwards of ten minutes.  Since I favor a full-on TDD approach, this is
an unhappy choice to have to make.  As a result of my experiences with
this approach, I want:

1. To have a program discover all the tests I have to run;
1. To stop at the first failure;
1. To always run the last failed test first;
1. If there is no previous test failure, **run the fastest tests first**;
1. Even if the tests aren't done yet, **restart the testing from the beginning** if I change any source files.

The first three, I can get Nose to do no problem.  I tried to write a
plugin for Nose to do Items 4 and 5, to no avail -- I suspect only
the God of Noses can do such a thing.

My answer is `sortest`, which meets these requirements.  `sortest`
borrows a module-loading utility from Nose (and therefore has `nose`
as a requirement) but otherwise stands alone.

The first time through, tests are run in discovery order, but `sortest`
remembers the test speeds for subsequent passes, and runs the fastest
ones first after that (assuming no tests fail).

## Installation

    pip install sortest  # Or easy_install sortest

## Example Usage

At the bash prompt:

    cd /path/to/my/great/source/code
    sortest

In your Python test program:

    import sortest

    rootdir = os.path.join(*(["/"] +
                  os.path.dirname(__file__).split('/')[:-1]))
    # Or some other working directory...

    excluded_files = ["__init__.py", "fabfile.py", "setup.py"]
    excluded_dirs = ['.svn', '.git', 'man', 'migrations']
    sortest.continuously_test(rootdir, excluded_files,
                              excluded_dirs, verbose_level=1)

## Requirements

Tested only on Python 2.6 so far.  Depends on the Nose package.

## To Do

Many, many things, including:

1. Allow command line options for verbosity, files/directories to
exclude, and source code path.
1. Right now it only runs functions called `test_...` in your source
tree.  Need to support `unittest.TestCase` classes & methods.
1. Options are limited compared to Nose.
1. Code could stand some more comments and refactoring.

## Caveat

This is VERY VERY alpha software.  DON'T USE IT YET.  I cannot be held
liable for any missiles launched or life support systems crashed
because you used this completely unsupported and brand-new software.

## License

Copyright © 2012 John Jacobsen

Distributed under the Eclipse Public License.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF THIRD PARTY RIGHTS. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
