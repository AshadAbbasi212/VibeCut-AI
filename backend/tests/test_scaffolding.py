"""Basic scaffolding test."""


def test_environment_scaffolding():
    import backend
    import backend.pipeline
    import backend.api
    assert backend is not None
    assert backend.pipeline is not None
    assert backend.api is not None
