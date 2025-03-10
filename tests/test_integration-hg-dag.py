# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import imp
import os
import mock

from conftest import hg_out

mozphab = imp.load_source(
    "mozphab", os.path.join(os.path.dirname(__file__), os.path.pardir, "moz-phab")
)
mozphab.SHOW_SPINNER = False


_revision = 100


def _check_call_by_line_gen(*args, **kwargs):
    global _revision
    yield "Revision URI: http://example.test/D%s" % _revision
    _revision += 1


check_call_by_line = mock.Mock(side_effect=_check_call_by_line_gen)


def _init_repo(hg_repo_path):
    test_file = hg_repo_path / "X"
    test_file.write_text(u"R0")
    hg_out("commit", "--addremove", "--message", "R0")
    return dict(test_file=test_file, rev=0, rev_map={"R0": "0"})


def _add_commit(repo, parent, name):
    hg_out("update", repo["rev_map"][parent])
    repo["test_file"].write_text(name.decode("utf8"))
    hg_out("commit", "--message", name)
    repo["rev"] += 1
    repo["rev_map"][name] = str(repo["rev"])


def _submit(repo, start, end, expected):
    mozphab.main(
        ["submit", "--yes", "--bug", "1", repo["rev_map"][start], repo["rev_map"][end]]
    )
    log = hg_out("log", "--graph", "--template", r"{desc|firstline}\n")
    assert log.strip() == expected.strip()


def test_submit_single_1(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _add_commit(repo, "B1", "C1")
    _submit(
        repo,
        "A1",
        "A1",
        """
o  C1
|
o  B1
|
@  Bug 1 - A1
|
o  R0
""",
    )


def test_submit_single_2(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _add_commit(repo, "A1", "B2")
    _submit(
        repo,
        "A1",
        "A1",
        """
o  B2
|
| o  B1
|/
@  Bug 1 - A1
|
o  R0
""",
    )


def test_submit_single_3(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _add_commit(repo, "B1", "C1")
    _add_commit(repo, "B1", "C2")
    _submit(
        repo,
        "A1",
        "A1",
        """
o  C2
|
| o  C1
|/
o  B1
|
@  Bug 1 - A1
|
o  R0
""",
    )


def test_submit_stack_1(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _submit(
        repo,
        "A1",
        "B1",
        """
@  Bug 1 - B1
|
o  Bug 1 - A1
|
o  R0
""",
    )


def test_submit_stack_2(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _add_commit(repo, "A1", "B2")
    _submit(
        repo,
        "A1",
        "B1",
        """
@  Bug 1 - B1
|
| o  B2
|/
o  Bug 1 - A1
|
o  R0
""",
    )


def test_submit_stack_3(in_process, hg_repo_path):
    repo = _init_repo(hg_repo_path)

    _add_commit(repo, "R0", "A1")
    _add_commit(repo, "A1", "B1")
    _add_commit(repo, "A1", "B2")
    _add_commit(repo, "B1", "C1")
    _submit(
        repo,
        "A1",
        "B1",
        """
o  C1
|
@  Bug 1 - B1
|
| o  B2
|/
o  Bug 1 - A1
|
o  R0
""",
    )
