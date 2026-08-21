#!/usr/bin/env python3
"""
LOOKALIKE-CHECK - Typosquatting & Homoglyph Domain Detector (Educational)
=========================================================================
Given a URL or domain, decide whether it is a look-alike of a well-known brand
using three techniques defenders rely on:

  1. Homoglyph normalisation  - maps Unicode look-alikes (Cyrillic а, digit 0,
     'rn' -> 'm', etc.) to their ASCII skeleton, catching аpple.com / paypa1.com.
  2. Edit-distance similarity  - Levenshtein distance to known brand domains.
  3. Structural red flags      - punycode (xn--), excessive subdomains, brand
     name buried in a subdomain of an unrelated domain (e.g. paypal.evil.com).

Purpose: teach users/defenders to spot phishing URLs. This never contacts the
domain; it is pure offline string analysis.

Usage:
    python lookalike_check.py http://paypa1.com/login
    python lookalike_check.py xn--pypal-4ve.com
    python lookalike_check.py login.microsoft.account-verify.ru
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

# Well-known brands people are commonly phished for.
KNOWN_BRANDS = [
    "google.com", "facebook.com", "instagram.com", "microsoft.com",
    "apple.com", "amazon.com", "paypal.com", "netflix.com", "linkedin.com",
    "discord.com", "github.com", "dropbox.com", "ebay.com", "steampowered.com",
    "whatsapp.com", "outlook.com", "office.com", "bankofamerica.com",
]

# Characters that visually resemble ASCII letters/digits -> skeleton mapping.
HOMOGLYPHS = {
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b",
    "$": "s", "@": "a", "|": "l", "!": "i",
    # common Cyrillic / Greek look-alikes
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
    "ѕ": "s", "і": "i", "ј": "j", "ԁ": "d", "ո": "n", "м": "m", "т": "t",
    "α": "a", "ο": "o", "ρ": "p", "ν": "v", "ι": "i",
}


def skeleton(text: str) -> str:
    """Reduce a string to its visual ASCII skeleton for homoglyph comparison."""
    text = text.lower()
    out = "".join(HOMOGLYPHS.get(ch, ch) for ch in text)
    return out.replace("rn", "m").replace("vv", "w")


def levenshtein(a: str, b: str) -> int:
    """Classic edit distance (iterative, O(len(a)*len(b)) time, O(len(b)) space)."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def registrable(domain: str) -> str:
    """Best-effort registrable domain (last two labels)."""
    parts = domain.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else domain


def extract_domain(target: str) -> str:
    if "://" not in target:
        target = "http://" + target
    host = urlparse(target).hostname or ""
    return host.lower().strip(".")


def analyze(target: str) -> dict:
    domain = extract_domain(target)
    reg = registrable(domain)
    reg_skel = skeleton(reg)
    flags: list[str] = []
    best = {"brand": None, "distance": 99, "kind": None}

    # 1. exact legit?
    if reg in KNOWN_BRANDS:
        # but a brand name inside an unrelated parent domain is still a red flag
        pass

    # 2. homoglyph / edit-distance against each brand
    for brand in KNOWN_BRANDS:
        brand_core = brand.split(".")[0]
        # skeleton match on registrable part
        if reg_skel == skeleton(brand):
            if reg != brand:
                flags.append(f"Homoglyph/skeleton match to {brand} "
                             f"('{reg}' looks identical to '{brand}')")
                best = {"brand": brand, "distance": 0, "kind": "homoglyph"}
        d = levenshtein(reg.split(".")[0], brand_core)
        if 0 < d <= 2 and d < best["distance"]:
            best = {"brand": brand, "distance": d, "kind": "typo"}

    if best["kind"] == "typo":
        flags.append(f"Very close to {best['brand']} "
                     f"(edit distance {best['distance']}) — likely typosquat")

    # 3. brand name buried in a subdomain of an unrelated site
    labels = domain.split(".")
    for brand in KNOWN_BRANDS:
        core = brand.split(".")[0]
        if core in labels[:-2] and reg != brand:
            flags.append(f"Brand '{core}' appears in a subdomain of unrelated "
                         f"domain '{reg}' — classic phishing structure")
            break

    # 4. structural red flags
    if domain.startswith("xn--") or ".xn--" in domain:
        flags.append("Punycode domain (xn--) — may hide non-ASCII look-alikes")
    if len(labels) >= 5:
        flags.append(f"Unusually deep subdomain chain ({len(labels)} labels)")
    if any(w in domain for w in ("secure", "verify", "account", "login", "update")) \
            and reg not in KNOWN_BRANDS:
        flags.append("Security/urgency keyword in a non-official domain")

    verdict = "LIKELY PHISHING" if any("Homoglyph" in f or "typosquat" in f
                                       or "phishing structure" in f for f in flags) \
        else "SUSPICIOUS" if flags else \
        ("LEGITIMATE (known brand)" if reg in KNOWN_BRANDS else "NO KNOWN INDICATORS")

    return {"input": target, "domain": domain, "registrable": reg,
            "skeleton": reg_skel, "closest_brand": best["brand"],
            "flags": flags, "verdict": verdict}


def main() -> int:
    ap = argparse.ArgumentParser(description="Detect look-alike/typosquatting phishing domains.")
    ap.add_argument("target", help="URL or domain to check")
    ap.add_argument("--json", action="store_true", help="Output JSON")
    args = ap.parse_args()

    result = analyze(args.target)
    if args.json:
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"\nInput      : {result['input']}")
        print(f"Domain     : {result['domain']}")
        print(f"Registrable: {result['registrable']}  (skeleton: {result['skeleton']})")
        if result["closest_brand"]:
            print(f"Closest brand: {result['closest_brand']}")
        print(f"\nVerdict: {result['verdict']}")
        if result["flags"]:
            print("Red flags:")
            for f in result["flags"]:
                print(f"  - {f}")
        print()
    # exit code: non-zero if suspicious/phishing (useful for filters)
    return 0 if result["verdict"].startswith(("LEGITIMATE", "NO KNOWN")) else 1


if __name__ == "__main__":
    sys.exit(main())
