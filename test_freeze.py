import freeze


def test_static_template_is_loaded_as_utf8():
    response = freeze.static_app.test_client().get("/")

    assert response.status_code == 200
    assert "📋 Timesheet Helper" in response.get_data(as_text=True)
    assert "•&#9;Monday" in response.get_data(as_text=True)
