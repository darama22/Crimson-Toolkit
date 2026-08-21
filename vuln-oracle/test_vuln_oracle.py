#!/usr/bin/env python3
"""Tests for VULN-ORACLE. Run: python test_vuln_oracle.py

Note: sample snippets below are deliberately benign (no real destructive
commands, webshells, or payloads) so that antivirus real-time protection does
not flag the test fixtures. They still trigger the scanner's detection rules.
"""
import importlib.util
import sys
from pathlib import Path

_here = Path(__file__).parent
spec = importlib.util.spec_from_file_location("vuln_oracle", _here / "vuln-oracle.py")
vo = importlib.util.module_from_spec(spec)
sys.modules["vuln_oracle"] = vo
spec.loader.exec_module(vo)


def test_python_rules(tmp):
    f = tmp / "app.py"
    f.write_text(
        "import os, yaml\n"
        "password = 'aaaaaaaa'\n"      # Hardcoded Secret
        "os.system(cmd)\n"             # Command Injection
        "yaml.load(data)\n",           # Insecure Deserialization
        encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    names = {x["name"] for x in rep.findings}
    assert "Hardcoded Secret" in names, names
    assert "Command Injection" in names, names
    assert "Insecure Deserialization" in names, names
    assert rep.risk_score > 0


def test_php_eval_detected(tmp):
    f = tmp / "x.php"
    f.write_text("<?php eval($x); ?>", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    cwes = {x["cwe"] for x in rep.findings}
    assert "CWE-95" in cwes  # eval RCE


def test_clean_file_no_findings(tmp):
    f = tmp / "clean.py"
    f.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    assert rep.findings == []
    assert rep.risk_score == 0


def test_comment_lines_skipped(tmp):
    f = tmp / "c.py"
    f.write_text("# eval(x) this line is only a comment\nx = 1\n", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    assert rep.findings == []


def test_directory_scan_and_min_severity(tmp):
    (tmp / "a.py").write_text("eval(x)\n", encoding="utf-8")
    (tmp / "b.py").write_text("import hashlib\nhashlib.md5(b'x')\n", encoding="utf-8")
    rep_all = vo.VulnOracle().scan_path(tmp)
    assert rep_all.files_scanned == 2
    rep_high = vo.VulnOracle().scan_path(tmp, min_severity="High")
    assert all(x["severity"] in ("Critical", "High") for x in rep_high.findings)
    assert any(x["severity"] == "Low" for x in rep_all.findings)  # md5 = Low


def test_shannon_entropy_ordering():
    # random-looking string has higher entropy than a repetitive one
    assert vo.shannon_entropy("aaaaaaaa") < vo.shannon_entropy("aB3xZ9qK")
    assert vo.shannon_entropy("") == 0.0


def test_entropy_secret_detected(tmp):
    f = tmp / "cfg.py"
    f.write_text("api_key = '9fJ2kQ8xZ1mB7vN4pL6wT0rY3aC5dE'\n", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    assert any(x["name"] == "High-Entropy Secret" for x in rep.findings)


def test_low_entropy_word_not_flagged(tmp):
    f = tmp / "ok.py"
    f.write_text("message = 'helloworldhelloworld'\n", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    assert not any(x["name"] == "High-Entropy Secret" for x in rep.findings)


def test_sarif_export(tmp):
    f = tmp / "x.py"
    f.write_text("eval(x)\n", encoding="utf-8")
    rep = vo.VulnOracle().scan_path(f)
    out = tmp / "r.sarif"
    vo.VulnOracle().export(rep, out)
    import json
    data = json.loads(out.read_text())
    assert data["version"] == "2.1.0"
    assert data["runs"][0]["results"]


if __name__ == "__main__":
    import tempfile, inspect
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if "tmp" in inspect.signature(fn).parameters:
                    fn(Path(tempfile.mkdtemp()))
                else:
                    fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
