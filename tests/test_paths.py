from brasileirao import paths


def test_root_is_repo_root():
    assert (paths.ROOT / "pyproject.toml").exists()
