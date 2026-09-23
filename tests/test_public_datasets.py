import hashlib

import pytest

from scripts.fetch_teaching_data import install_file


def test_verified_file_is_saved(tmp_path):
    data = b'{"teaching": true}'
    entry = {"path": "source/example.json", "sha256": hashlib.sha256(data).hexdigest()}
    install_file(tmp_path, entry, data)
    assert (tmp_path / entry["path"]).read_bytes() == data


def test_bad_hash_cannot_replace_existing_file(tmp_path):
    path = tmp_path / "example.json"
    path.write_text("original")
    with pytest.raises(ValueError, match="checksum"):
        install_file(tmp_path, {"path": "example.json", "sha256": "wrong"}, b"changed")
    assert path.read_text() == "original"


def test_destination_cannot_escape_download_directory(tmp_path):
    with pytest.raises(ValueError, match="path"):
        install_file(tmp_path, {"path": "../escape", "sha256": ""}, b"")
