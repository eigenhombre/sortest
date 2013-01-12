import collections
import inspect
import itertools
import nose.importer
import nose.util
import operator
import os
import os.path
import re
import sys
import time
import traceback
import unittest


def find_python_files(rootdir, excluded_dirs):
    for root, subdirs, files in os.walk(rootdir):
        for baddir in excluded_dirs:
            if baddir in subdirs:
                subdirs.remove(baddir)
        for f in files:
            if f.endswith('.py'):
                yield root, f


def find_python_update_times(rootdir, excluded_dirs, pyfiles):
    for d, f in pyfiles:
        try:
            yield {"dir": d,
                   "file": f,
                   "path": os.path.join(d, f),
                   "saved": os.path.getmtime(os.path.join(d, f))}
        except OSError:
            pass  # Skip deleted file


def wanted_files(excluded_files, excluded_dirs, filesgen):
    for d in filesgen:
        if (d["file"] not in excluded_files
            and
            d["dir"] not in excluded_dirs):
            yield d


def find_modules(rootdir, dictgen):
    importer = nose.importer.Importer()
    for d in dictgen:
        modname = os.path.splitext(d["path"].replace(
            rootdir, "", 1).lstrip("/"))[0].replace("/", ".")
        modname = re.sub(r"\.__init__$", "", modname)
        # Account for possibility that __init__.py is our source file,
        # which we don't want for Nose's importer....:
        module = importer.importFromPath(d["path"], modname)
        reload(module)
        d["modname"] = modname
        d["module"] = module
        d["tests"] = []
        yield d


def is_a_test_function(func):
    return inspect.isfunction(func) and func.__name__.startswith("test_")


def get_test_functions_for_modules(dictgen):
    for d in dictgen:
        module = d["module"]
        for itemname in dir(module):
            item = getattr(module, itemname, None)
            if is_a_test_function(item):
                d["tests"].append({"function": item,
                                   "testtype": "function",
                                   "funname": ":".join((d["modname"], itemname))})
        yield d


class ExceptionCatchingResult(unittest.TestResult):
    """
    Needed to collect result from unittest.TestCases
    """
    def addError(self, t, q):
        print "\n\naddError", t, type(t), q, type(q)
        raise q[0]

    def addFailure(self, t, q):
        print "\n\naddFailure", t, type(t), q, type(q)
        raise q[0]


def get_unittest_functions(mods):
    tl = unittest.TestLoader()
    for module in mods:
        for itemname in dir(module["module"]):
            item = getattr(module["module"], itemname, None)
            if (item and
                nose.util.isclass(item) and
                issubclass(item, unittest.TestCase)):
                for t in tl.loadTestsFromTestCase(item):
                    funname = "%s:%s.%s" % (module["modname"],
                                            itemname,
                                            t._testMethodName)
                    module["tests"].append({"function": t,
                                            "testtype": "unittest",
                                            "funname": funname})
        yield module


def duration_and_success_status(frec):
    test_result = ExceptionCatchingResult()
    t = time.time()
    try:
        if frec["testtype"] == "unittest":
            frec["function"](test_result)
        else:
            assert frec["testtype"] == "function"
            frec["function"]()
    except Exception, e:
        traceback.print_exc()
        return time.time() - t, False
    else:
        return time.time() - t, True


def unroll_into_functions(modules_gen):
    for m in modules_gen:
        for f in m["tests"]:
            f["modname"] = m["modname"]
            f["module"] = m["module"]
            f["dir"] = m["dir"]
            f["file"] = m["file"]
            f["saved"] = m["saved"]
            yield f


def get_all_wanted_files(rootdir, excluded_files, excluded_dirs):
    pyfiles = find_python_files(rootdir, excluded_dirs)
    py_updated = find_python_update_times(rootdir, excluded_dirs, pyfiles)
    return wanted_files(excluded_files, excluded_dirs, py_updated)


def get_functions_from_files(rootdir, files):
    with_modules = find_modules(rootdir, files)
    unittest_funs = get_unittest_functions(with_modules)
    with_testfuns = get_test_functions_for_modules(unittest_funs)
    return unroll_into_functions(with_testfuns)


def pr(x):
    print x,
    sys.stdout.flush()
    

import pprint;
def pp(*args):
    pprint.PrettyPrinter().pprint(args)


# STATES
START = "S"
RUN = "R"
WAIT = "w"


def any_files_have_changed(filedict, last_check):
    for f in filedict:
        if f["saved"] > last_check:
            return True


def run(frec, verbose_level):
    if verbose_level > 1:
        print frec["funname"],
        sys.stdout.flush()
    duration, succeeded = duration_and_success_status(frec)
    if verbose_level == 1:
        os.write(sys.stdout.fileno(), ".")
        sys.stdout.flush()
    elif verbose_level > 1:
        print "%.4f" % duration
    return duration, succeeded


def continuously_test(rootdir, excluded_files, excluded_dirs,
                      verbose_level=1):
    file_t = time.time()
    last_timeout = time.time()
    state = START
    funcs = []
    constant_factory = lambda(value): itertools.repeat(value).next
    durations = collections.defaultdict(constant_factory(1E10))
    succeeded = collections.defaultdict(bool)
    while True:
    #for _ in range(100):   # For development with conttest
        if state == START:
            files = list(get_all_wanted_files(rootdir, excluded_files, excluded_dirs))
            try:
                funcs = sorted(list(get_functions_from_files(rootdir, files)),
                               key=lambda f: durations[f["funname"]])
            except (IndentationError, SyntaxError):
                traceback.print_exc()
                state = WAIT
                continue
            state = RUN

        if state == RUN:
            if not funcs:
                print "\nOK"
                state = WAIT
                continue
            f = funcs.pop(0)
            testtime, result = run(f, verbose_level)
            durations[f["funname"]] = testtime
            succeeded[f["funname"]] = result
            if result == False:
                state = WAIT
                continue
            t = time.time()
            if t - last_timeout > 0.5:
                last_timeout = t
                files = list(get_all_wanted_files(rootdir, excluded_files, excluded_dirs))
                if any_files_have_changed(files, file_t):
                    file_t = time.time()
                    state = START
                    continue

        if state == WAIT:
            files = list(get_all_wanted_files(rootdir, excluded_files, excluded_dirs))
            if any_files_have_changed(files, file_t):
                file_t = time.time()
                state = START
            else:
                time.sleep(0.05)
    # print "XXXXX"    # For development with conttest

"""
def find_files_and_updates(rootdir, excluded_dirs):
    tcheck = None
    while True:
        meta = {}
        for d, f in list(find_python_files(rootdir, excluded_dirs)):
            meta[(d, f)] = {"filename": f}
            # See if file was removed by actually reading it:
            try:
                with file(os.path.join(d, f)) as _f:
                    _f.readline()
            except IOError:  # File deleted
                del meta[(d, f)]
                continue
            t = os.path.getmtime(os.path.join(d, f))
            meta[(d, f)]["t"] = t
            if not tcheck or t > tcheck:
                tcheck = t
                meta[(d, f)]["updated"] = True
            else:
                meta[(d, f)]["updated"] = False
        yield meta


class SimpleTestResult(unittest.TestResult):
    def addError(self, x, exception_tuple):
        raise exception_tuple[1]


def run_testcase_as_function(f):
    f.run(SimpleTestResult())



def add_tests_for_path(funcdict, rootdir, fullpath, importer):
    modname = os.path.splitext(fullpath.replace(
        rootdir, "", 1).lstrip("/"))[0].replace("/", ".")

    # Account for possibility that __init__.py is our source file,
    # which we don't want for Nose's importer....:
    module = importer.importFromPath(fullpath,
                                     re.sub(r"\.__init__$", "", modname))
    reload(module)
    items = [(i, getattr(module, i, None))
             for i in dir(module)]
    functests = [(i, f)
             for (i, f) in items
             if is_a_test_function(f)]
    for item, func in functests:
        funcdict["%s:%s" % (module.__name__, item)] = func

    test_classes = [(i, f)
                    for (i, f) in items
                    if nose.util.isclass(f) and
                    issubclass(f, unittest.TestCase)]
    
    tl = unittest.TestLoader()
    testfuncs = [tl.loadTestsFromTestCase(cls[1])
                 for cls in test_classes]
    for f in testfuncs:
        for t in f._tests:
            funcdict["%s:%s" % (module.__name__, t)] = lambda: \
                                                  run_testcase_as_function(t)


def check_for_change_to_self(this_file):
    found_already = [False]  # Apologies for ugly hack for
                             # locally-scoped variable...
    def checker(path):
        if path == this_file:
            if found_already[0]:
                print "This file changed, quitting."
                raise SystemExit
            found_already[0] = True
            
    return checker


def file_was_updated(filedata):
    return len([1 for f in
                filedata.keys()
                if filedata[f]["updated"]]) > 0


def run_found_tests(last_search, test_functions_to_run,
                    failprev, lasttime, verbose_level, triggered_files_gen):
    testkeys = sorted(test_functions_to_run.keys(),
                      key=lambda i: (not failprev[i],
                                     lasttime[i]))
    for testfun in testkeys:
        if verbose_level > 1:
            print testfun,
            sys.stdout.flush()
        t = time.time()
        try:
            test_functions_to_run[testfun]()
        except Exception, e:
            elapsed = time.time() - t
            lasttime[testfun] = elapsed
            failprev[testfun] = True
            if verbose_level > 0:
                print
            traceback.print_exc()
            return last_search, False
        else:
            if verbose_level == 1:
                os.write(sys.stdout.fileno(), ".")
                sys.stdout.flush()
            elapsed = time.time() - t
            lasttime[testfun] = elapsed
            failprev[testfun] = False
            if verbose_level > 1:
                print "%.4f" % elapsed
        finally:
            if time.time() - last_search > 1:
                filedata = triggered_files_gen.next()
                triggered_again = file_was_updated(filedata)
                last_search = time.time()
                if triggered_again:
                    return last_search, True
    return last_search, False


def continuously_test_old(rootdir, excluded_files, excluded_dirs,
                      verbose_level=1):
    import pdb
    pdb.set_trace()
    importer = nose.importer.Importer()
    lasttime = collections.defaultdict(float)
    failprev = collections.defaultdict(bool)
    last_search = time.time()
    start_time = last_search
    # Loop over generator does not terminate:
    triggered_files_gen = find_files_and_updates(rootdir, excluded_dirs)
    retriggered = False
    filedata = None
    have_errors = False
    while True:
        if not retriggered:
            filedata = triggered_files_gen.next()
            triggered = file_was_updated(filedata)
        last_search = time.time()
        if triggered or retriggered:
            allfiles = list(filedata.iteritems())
            wanted = [(k, v)
                      for k, v in allfiles
                      if (k[1] not in excluded_files
                          and k[0] not in excluded_dirs)]
            test_functions_to_run = {}
            for k, v in wanted:
                fullpath = os.path.join(*k)
                try:
                    add_tests_for_path(test_functions_to_run, rootdir,
                                       fullpath, importer)
                    last_search, retriggered = run_found_tests(last_search,
                                                               test_functions_to_run,
                                                               failprev, lasttime,
                                                               verbose_level,
                                                               triggered_files_gen)
                except SyntaxError:
                    traceback.print_exc()
                    have_errors = True
                    continue
            if retriggered:
                if verbose_level == 1:
                    print
                elif verbose_level > 1:
                    print "Restart triggered."
            elif verbose_level > 0 and not have_errors:
                print "\nOK"
        else:
            test_functions_to_run = {}
            have_errors = False
            time.sleep(0.1)
"""
