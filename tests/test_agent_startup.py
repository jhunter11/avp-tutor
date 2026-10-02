import json
import socket
from unittest.mock import patch

import pytest
from starlette.testclient import TestClient

import demo


def test_background_process_options_cover_windows_macos_and_linux():
    windows = demo.background_options("Windows")
    assert windows["creationflags"] & 0x08000000  # CREATE_NO_WINDOW
    assert windows["creationflags"] & 0x00000200  # independent process group
    for system in ["Darwin", "Linux"]:
        assert demo.background_options(system) == {"start_new_session": True}


def test_local_environment_file_does_not_replace_inherited_key(tmp_path, monkeypatch):
    path = tmp_path / "team .env"
    path.write_text('LLM_PROVIDER=gemini\nGEMINI_MODEL="future-model"\nOPENROUTER_API_KEY="file-key"\n')
    monkeypatch.setenv("OPENROUTER_API_KEY", "inherited-key")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    env = demo.effective_environment(path)
    assert env["OPENROUTER_API_KEY"] == "inherited-key"
    assert env["GEMINI_MODEL"] == "future-model"
    assert env["AVP_DEMO_ENV"] == str(path)
    with pytest.raises(demo.StartupError, match="does not exist"):
        demo.effective_environment(tmp_path / "absent")


def test_identity_route_is_not_shadowed_by_static_mount(monkeypatch):
    monkeypatch.setenv("AVP_STARTUP_INSTANCE", "test-owned-instance")
    from agent_runtime import app
    with TestClient(app) as client:
        identity = client.get("/__agent/status")
        assert identity.status_code == 200
        assert identity.json()["application"] == "avp-tutor"
        assert identity.json()["instance"] == "test-owned-instance"
        assert client.get("/").status_code == 200


def test_stop_refuses_a_stale_or_foreign_process_record(monkeypatch):
    monkeypatch.setattr(demo, "saved_state", lambda: {"port": 8771, "pid": 999, "instance": "old"})
    monkeypatch.setattr(demo, "read_json_url", lambda _url: {"application": "avp-tutor", "pid": 999, "instance": "other", "root": str(demo.ROOT)})
    with patch("demo.os.kill") as kill:
        with pytest.raises(demo.StartupError, match="identity"):
            demo.stop()
        kill.assert_not_called()


def test_start_does_not_displace_an_occupied_port(monkeypatch):
    monkeypatch.setattr(demo, "saved_state", lambda: None)
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", 0))
        port = occupied.getsockname()[1]
        with patch("demo.subprocess.Popen") as process:
            with pytest.raises(demo.StartupError, match="occupied"):
                demo.start(demo.effective_environment(), port)
            process.assert_not_called()


def test_repeated_start_reuses_only_the_matching_configuration(monkeypatch):
    env = demo.effective_environment()
    state = {"port": 8771, "pid": 123, "instance": "owned", "url": "http://127.0.0.1:8771/"}
    live = {"app": "demo_v1.app:app", "provider": demo.public_status(env), "runtime_version": demo.runtime_version()}
    monkeypatch.setattr(demo, "saved_state", lambda: state)
    monkeypatch.setattr(demo, "owned_identity", lambda _state: live)
    with patch("demo.subprocess.Popen") as process, patch("demo.webbrowser.open") as browser:
        result = demo.start(env, 8771, open_browser=True)
        assert result["reused"] and result["url"].endswith("8771/")
        process.assert_not_called()
        browser.assert_called_once_with(result["url"])
        with pytest.raises(demo.StartupError, match="another configuration"):
            demo.start(env, 8772)
        live["runtime_version"] = "older-code"
        with pytest.raises(demo.StartupError, match="older code"):
            demo.start(env, 8771)


def test_doctor_reports_missing_key_without_disclosing_any_secret(monkeypatch):
    env = {"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "future-model", "OPENROUTER_API_KEY": "unrelated-private-marker"}
    status = demo.doctor(env)
    assert not status["provider"]["configured"]
    assert status["model_reachability"] == "not checked"
    assert "unrelated-private-marker" not in json.dumps(status)


def test_machine_readable_error_for_missing_env_file(tmp_path, capsys):
    assert demo.main(["doctor", "--env-file", str(tmp_path / "missing"), "--json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False and "does not exist" in result["error"]
