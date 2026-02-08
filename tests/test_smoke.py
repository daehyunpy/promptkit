"""Smoke test to verify package structure is importable."""


def test_package_imports():
    """Verify the package structure is importable."""
    import promptkit
    import promptkit.app
    import promptkit.domain
    import promptkit.infra

    assert promptkit.__version__ == "0.1.0"
