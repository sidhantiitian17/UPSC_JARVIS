import jarvis


def test_package_imports_and_has_version():
    assert jarvis.__version__ == "0.1.0"
