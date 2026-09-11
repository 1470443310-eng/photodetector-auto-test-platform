from streamlit.testing.v1 import AppTest


def test_main_page_shows_guide_and_inline_chinese_report():
    app = AppTest.from_file("app.py", default_timeout=30).run()

    assert not app.exception
    assert len(app.get("popover")) == 1

    app.button[0].click().run()

    assert not app.exception
    assert len(app.tabs) == 4
    assert len(app.get("html")) == 1
    assert len(app.get("download_button")) == 1
    assert [metric.value for metric in app.metric[:4]] == ["20", "13", "6", "1"]


def test_realistic_mode_changes_seed_on_each_browser_run():
    app = AppTest.from_file("app.py", default_timeout=30).run()

    app.button[0].click().run()
    first_seed = app.session_state["outcome"]["effective_seed"]

    app.button[0].click().run()
    second_seed = app.session_state["outcome"]["effective_seed"]

    assert first_seed != second_seed
    assert app.session_state["outcome"]["previous_effective_seed"] == first_seed
    assert app.session_state["outcome"]["browser_run_count"] == 2
