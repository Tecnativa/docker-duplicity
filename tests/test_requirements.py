import filecmp
import tempfile
from pathlib import Path

from plumbum.cmd import poetry


def test_requirements_file_up_to_date():
    cur_path = Path.cwd()
    # Generate new requirements.txt from lock file
    assert (cur_path / "poetry.lock").exists()
    with tempfile.NamedTemporaryFile(suffix=".txt", prefix="requirements") as f:
        new_file = f.name
        poetry("export", "-E", "duplicity", "-o", new_file)
        # Compare new file with old one
        assert filecmp.cmp(
            new_file, cur_path / "requirements.txt"
        ), "Requirements file not up-to-date!"
