"""Allow ``python -m touchstone_llm ...``.

Useful on Windows when pip's Scripts folder is not on PATH and the
``touchstone`` command is therefore "not recognized".
"""

from touchstone_llm.cli import app

app(prog_name="touchstone")
