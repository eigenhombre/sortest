import collections
import inspect
import nose.importer
import os
import os.path
import re
import sys
import time
import traceback


def python_files(rootdir, excluded_dirs):
    for root, subdirs, files in os.walk(rootdir):
        for baddir in excluded_dirs:
            if baddir in subdirs:
                subdirs.remove(baddir)
        for f in files:
            if f.endswith('.py'):
                yield root, f


def find_files_and_updates(rootdir, excluded_dirs):
    tcheck = None
    while True:
        trigger = False
        pf = list(python_files(rootdir, excluded_dirs))
        meta = {}
        for d, f in pf:
            if (d, f) not in meta:
                meta[(d, f)] = {}
            meta[(d, f)] = {"filename": f}
            try:
                with file(os.path.join(d, f)) as _f:
                    meta[(d, f)]["contents"] = _f.read()
            except IOError:  # File deleted
                del meta[(d, f)]
                continue
            t = os.path.getmtime(os.path.join(d, f))
            meta[(d, f)]["t"] = t
            if not tcheck or t > tcheck:
                tcheck = t
                meta[(d, f)]["updated"] = True
                trigger = True
        yield trigger, meta


def add_tests_for_path(funcdict, rootdir, fullpath, importer):
    modname = os.path.splitext(fullpath.replace(
        rootdir, "").lstrip("/"))[0].replace("/", ".")
    module = importer.importFromPath(fullpath, modname)
    reload(module)
    items = [(i, getattr(module, i, None))
             for i in dir(module)]
    tests = [(i, f)
             for (i, f) in items
             if is_a_test_function(f)]
    for item, func in tests:
        funcdict[(module, fullpath, item)] = func


def is_a_test_function(func):
    return inspect.isfunction(func) and func.__name__.startswith("test_")


def continuously_test(rootdir, excluded_files, excluded_dirs,
                      verbose_level=1):
    self_updated = False
    importer = nose.importer.Importer()
    lasttime = collections.defaultdict(float)
    failprev = collections.defaultdict(bool)
    last_search = time.time()
    # Loop over generator does not terminate:
    triggered_files_gen = find_files_and_updates(rootdir, excluded_dirs)
    retriggered = False
    while True:
        for triggered, filedata in triggered_files_gen:
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
                    if (re.sub("\.pyc$", ".py", fullpath) == __file__
                        and v.get("updated", False)):
                        if self_updated:
                            print ("Found change in test code itself, "
                                   "aborting!!!\n\n")
                            raise SystemExit
                        else:
                            self_updated = True

                    add_tests_for_path(test_functions_to_run, rootdir,
                                       fullpath, importer)

                def run_found_tests(last_search, test_functions_to_run):
                    testkeys = sorted(test_functions_to_run.keys(),
                                      key=lambda i: (not failprev[i],
                                                     lasttime[i]))
                    for it in testkeys:
                        if verbose_level > 1:
                            print "%s:%s" % (it[0].__name__, it[2]),
                            sys.stdout.flush()
                        t = time.time()
                        try:
                            test_functions_to_run[it]()
                        except Exception, e:
                            elapsed = time.time() - t
                            lasttime[it] = elapsed
                            failprev[it] = True
                            if verbose_level > 0:
                                print
                            traceback.print_exc()
                            return last_search, False
                        else:
                            if verbose_level == 1:
                                os.write(sys.stdout.fileno(), ".")
                                sys.stdout.flush()
                            elapsed = time.time() - t
                            lasttime[it] = elapsed
                            failprev[it] = False
                            if verbose_level > 1:
                                print "%.4f" % elapsed
                        finally:
                            if time.time() - last_search > 1:
                                triggered_again, _ = triggered_files_gen.next()
                                last_search = time.time()
                                if triggered_again:
                                    return last_search, True
                    return last_search, False
                last_search, retriggered = run_found_tests(last_search,
                    test_functions_to_run)
                if retriggered:
                    if verbose_level == 1:
                        print
                    elif verbose_level > 1:
                        print "Restart triggered."
                elif verbose_level > 0:
                    print "\nOK"
            else:
                time.sleep(0.1)
