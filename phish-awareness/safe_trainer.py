#!/usr/bin/env python3
"""
SAFE-TRAINER - Anti-Phishing Awareness Simulator (Educational)
==============================================================
Generates a self-contained HTML training page that LOOKS like a login prompt
but captures NOTHING. When the learner submits, it reveals the phishing
red flags they should have noticed and scores their awareness.

This is the ethical inverse of a phishing kit:
  - No credentials are stored, transmitted, or logged. Ever.
  - Input never leaves the page (no network calls, no backend).
  - The goal is to TRAIN people to recognize phishing, not to deceive them.

Usage:
    python safe_trainer.py --brand "Acme Corp" -o training.html
    # open training.html in a browser and try to "log in"
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

RED_FLAGS = [
    ("URL / domain", "The address bar did not show the real company domain — "
     "phishing pages live on look-alike or unrelated URLs."),
    ("No password should be typed", "You entered a password into a page you "
     "reached from a link. Always navigate to the site yourself instead."),
    ("Urgency & fear", "Wording like 'account suspended' or 'verify now' is "
     "engineered to make you act before you think."),
    ("Where the form sends data", "A real login posts to the brand's own secure "
     "domain; kits post to a stranger's server or write your input to a file."),
    ("Certificate & padlock", "Check for HTTPS and a valid certificate matching "
     "the exact brand domain — not a subdomain trick like brand.secure-login.co."),
    ("Unexpected context", "You did not initiate this login. Unsolicited login "
     "prompts arriving by email/DM are the number-one phishing delivery method."),
]

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{brand} — Sign in</title>
<style>
  :root {{ --bg:#f0f2f5; --card:#fff; --accent:#1877f2; --danger:#c0392b;
           --ok:#2e7d32; --text:#1c1e21; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:system-ui,Segoe UI,Roboto,Arial,sans-serif;
          background:var(--bg); color:var(--text);
          display:flex; align-items:center; justify-content:center;
          min-height:100vh; padding:16px; }}
  .card {{ background:var(--card); width:100%; max-width:400px; border-radius:12px;
           box-shadow:0 2px 16px rgba(0,0,0,.12); padding:28px; }}
  .brand {{ text-align:center; font-size:28px; font-weight:800;
            color:var(--accent); margin-bottom:6px; }}
  .warn {{ font-size:12px; text-align:center; color:#666; margin-bottom:18px; }}
  input {{ width:100%; padding:14px; margin:8px 0; border:1px solid #ccd0d5;
           border-radius:8px; font-size:15px; }}
  button {{ width:100%; padding:14px; margin-top:8px; border:0; border-radius:8px;
            background:var(--accent); color:#fff; font-size:17px; font-weight:700;
            cursor:pointer; }}
  .reveal {{ display:none; margin-top:20px; }}
  .reveal.show {{ display:block; }}
  .banner {{ background:#fdecea; border:1px solid var(--danger); color:var(--danger);
             padding:14px; border-radius:8px; font-weight:700; text-align:center; }}
  .flags {{ list-style:none; padding:0; margin:16px 0 0; }}
  .flags li {{ background:#fff8e1; border-left:4px solid #f39c12; margin:8px 0;
               padding:10px 12px; border-radius:6px; font-size:14px; }}
  .flags b {{ display:block; color:#7a5c00; margin-bottom:2px; }}
  .score {{ text-align:center; font-size:18px; font-weight:800; margin-top:16px;
            color:var(--ok); }}
  .again {{ background:#42b72a; }}
  footer {{ text-align:center; font-size:11px; color:#8a8d91; margin-top:18px; }}
</style>
</head>
<body>
  <div class="card">
    <div class="brand">{brand}</div>
    <div class="warn">⚠️ Anti-phishing TRAINING simulator — nothing you type is saved or sent.</div>

    <form id="loginForm" autocomplete="off">
      <input type="text" id="user" placeholder="Email or phone" aria-label="user">
      <input type="password" id="pass" placeholder="Password" aria-label="password">
      <button type="submit">Log in</button>
    </form>

    <div class="reveal" id="reveal">
      <div class="banner">🎣 This was a phishing simulation. In a real attack, your
        credentials would now be in an attacker's hands.</div>
      <p style="font-size:14px">Here are the red flags this page contained:</p>
      <ul class="flags">{flags}</ul>
      <div class="score" id="score"></div>
      <button class="again" onclick="location.reload()">Try again / reset</button>
    </div>

    <footer>Educational tool · No data collection · Crimson Toolkit — phish-awareness</footer>
  </div>

<script>
(function () {{
  // SECURITY NOTE: this handler intentionally does NOTHING with the input.
  // The credentials are read only to prove to the learner they were exposed,
  // then immediately discarded. No storage, no network, no logging.
  var form = document.getElementById('loginForm');
  form.addEventListener('submit', function (e) {{
    e.preventDefault();
    var typedPassword = document.getElementById('pass').value.length > 0;
    // Discard input immediately.
    document.getElementById('user').value = '';
    document.getElementById('pass').value = '';
    form.style.display = 'none';
    var reveal = document.getElementById('reveal');
    reveal.classList.add('show');
    var msg = typedPassword
      ? "You typed a password into an unverified page. Awareness score: 0/1 — but now you know."
      : "Good instinct — you hesitated on the password. Awareness score: 1/1.";
    document.getElementById('score').textContent = msg;
  }});
}})();
</script>
</body>
</html>
"""


def build_page(brand: str) -> str:
    flag_items = "".join(
        f"<li><b>{html.escape(title)}</b>{html.escape(desc)}</li>"
        for title, desc in RED_FLAGS)
    return TEMPLATE.format(brand=html.escape(brand), flags=flag_items)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate a safe anti-phishing awareness training page.")
    ap.add_argument("--brand", default="Acme Corp",
                    help="Brand name to display on the mock login")
    ap.add_argument("-o", "--output", default="training.html",
                    help="Output HTML file (default training.html)")
    args = ap.parse_args()

    out = Path(args.output)
    out.write_text(build_page(args.brand), encoding="utf-8")
    print(f"[+] Safe training page written to {out.resolve()}")
    print("[i] Open it in a browser. Nothing typed into it is stored or sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
