#!/usr/bin/env python3
"""Tests for LOOKALIKE-CHECK. Run: python test_lookalike.py"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "lookalike_check", Path(__file__).with_name("lookalike_check.py"))
lc = importlib.util.module_from_spec(spec)
sys.modules["lookalike_check"] = lc
spec.loader.exec_module(lc)


def test_levenshtein_basics():
    assert lc.levenshtein("kitten", "sitting") == 3
    assert lc.levenshtein("abc", "abc") == 0
    assert lc.levenshtein("", "abc") == 3


def test_skeleton_normalises_homoglyphs():
    assert lc.skeleton("paypa1") == "paypal"
    assert lc.skeleton("g00gle") == "google"
    assert lc.skeleton("rnicrosoft") == "microsoft"  # rn -> m


def test_homoglyph_domain_flagged():
    r = lc.analyze("http://paypa1.com/login")
    assert r["verdict"] == "LIKELY PHISHING"
    assert any("paypal.com" in f for f in r["flags"])


def test_cyrillic_lookalike():
    # 'а' here is Cyrillic U+0430
    r = lc.analyze("http://аpple.com")
    assert r["registrable"] != "apple.com"
    assert r["skeleton"] == "apple.com"
    assert r["verdict"] == "LIKELY PHISHING"


def test_brand_in_unrelated_subdomain():
    r = lc.analyze("login.microsoft.account-verify.ru")
    assert r["verdict"] == "LIKELY PHISHING"
    assert any("classic phishing structure" in f for f in r["flags"])


def test_typosquat_edit_distance():
    r = lc.analyze("http://gogle.com")
    assert r["closest_brand"] == "google.com"
    assert r["verdict"] in ("LIKELY PHISHING", "SUSPICIOUS")


def test_legit_domain_clean():
    r = lc.analyze("https://google.com/search")
    assert r["verdict"].startswith("LEGITIMATE")
    assert r["flags"] == []


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as exc:
                failures += 1
                print(f"FAIL {name}: {exc}")
    sys.exit(1 if failures else 0)
