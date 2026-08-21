#!/usr/bin/env python3
"""Tests for DEFENSE-RADAR posture scanner. Run: python -m pytest -q (or plain)."""
import importlib.util
import socket
import sys
import threading
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "defense_radar", Path(__file__).with_name("defense-radar.py"))
dr = importlib.util.module_from_spec(spec)
sys.modules["defense_radar"] = dr  # required so dataclasses can resolve the module
spec.loader.exec_module(dr)


def test_parse_ports_ranges_and_lists():
    assert dr.parse_ports("22,80,443") == [22, 80, 443]
    assert dr.parse_ports("1-3") == [1, 2, 3]
    assert dr.parse_ports(None) == dr.DEFAULT_PORTS
    assert 70000 not in dr.parse_ports("70000")  # out of range dropped


def test_resolve_ip_and_hostname():
    assert dr.PostureRadar.resolve("127.0.0.1") == "127.0.0.1"
    assert dr.PostureRadar.resolve("localhost") in ("127.0.0.1", "::1")
    assert dr.PostureRadar.resolve("nonexistent.invalid.") is None


def test_grade_boundaries():
    r = dr.PostureRadar()
    assert r._grade(0, 0).startswith("A")
    assert r._grade(2.0, 1) == "A"
    assert r._grade(9.0, 3) == "F"


def test_scan_detects_open_port(tmp_path):
    # Spin up a throwaway listener on an ephemeral port
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]
    stop = threading.Event()

    def serve():
        srv.settimeout(0.5)
        while not stop.is_set():
            try:
                c, _ = srv.accept()
                c.close()
            except (socket.timeout, OSError):
                continue

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    try:
        radar = dr.PostureRadar(timeout=0.5, workers=10)
        report = radar.scan("127.0.0.1", [port])
        assert any(p.port == port and p.open for p in report.ports)
        # export round-trips to JSON
        out = tmp_path / "r.json"
        radar.export(report, out)
        assert out.exists() and '"target"' in out.read_text()
    finally:
        stop.set()
        srv.close()


def test_audit_http_headers_flags_missing():
    # a response missing all security headers -> every guidance returned
    missing = dr.PostureRadar.audit_http_headers({"Server": "nginx"})
    assert len(missing) == len(dr.SECURITY_HEADERS)


def test_audit_http_headers_all_present():
    full = {h: "x" for h in dr.SECURITY_HEADERS}
    full["Server"] = "nginx"
    assert dr.PostureRadar.audit_http_headers(full) == []


def test_audit_http_headers_case_insensitive():
    # header names are case-insensitive per RFC
    partial = {"Strict-Transport-Security": "max-age=63072000"}
    missing = dr.PostureRadar.audit_http_headers(partial)
    assert not any("HSTS" in m for m in missing)


def test_risk_score_zero_when_nothing_open():
    radar = dr.PostureRadar(timeout=0.2, workers=5)
    # Port 1 almost never listens on loopback
    report = radar.scan("127.0.0.1", [1])
    assert report.risk_score == 0.0
    assert report.grade.startswith("A")


if __name__ == "__main__":
    import sys
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                # provide tmp_path where needed
                import inspect
                if "tmp_path" in inspect.signature(fn).parameters:
                    import tempfile
                    fn(Path(tempfile.mkdtemp()))
                else:
                    fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
