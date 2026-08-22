from app.main import app


def test_exposes_exactly_two_business_paths() -> None:
    assert set(app.openapi()["paths"]) == {"/pagamentos", "/pagamentos/{payment_id}"}
