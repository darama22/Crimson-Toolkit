# TARGET-SCOUT - Example Usage

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic scan
python target-scout.py --company "Microsoft"

# Scan specific modules
python target-scout.py --company "OpenAI" --modules github,domains

# Verbose output
python target-scout.py --company "Google" --verbose

# Save report
python target-scout.py --company "Netflix" --output report.json
```

## Advanced Usage

### GitHub Scanning with Token

```bash
# Get better rate limits with GitHub token
python target-scout.py --company "Facebook" --github-token YOUR_GITHUB_TOKEN

# GitHub-only scan
python target-scout.py --company "Meta" --modules github --verbose
```

### Domain Enumeration

```bash
# Full domain scan
python target-scout.py --company "Amazon" --modules domains

# Specify exact domain
python target-scout.py --company "AWS" --domain aws.amazon.com
```

## Real-World Examples

### Example 1: Tech Company Recon

```bash
python target-scout.py --company "OpenAI" --verbose
```

**Output:**
```
Found 10 public GitHub repositories
  - Significant-Gravitas/AutoGPT (Python) ⭐ 181362
  - ollama/ollama (Go) ⭐ 160209
  - f/awesome-chatgpt-prompts (TypeScript) ⭐ 143223
Primary tech stack: Python
```

### Example 2: Domain Discovery

```bash
python target-scout.py --company "Google" --modules domains
```

**Output:**
```
Domain google.com resolves!
Found 7 active subdomains
  - www.google.com
  - mail.google.com
  - admin.google.com
  - vpn.google.com
  - api.google.com
```

## Module Details

### LinkedIn Scanner
- **Method:** Public Google search of LinkedIn pages
- **Limitations:** No employee enumeration without API
- **Output:** Company URLs, basic info

### GitHub Scanner
- **Method:** GitHub Search API
- **Features:** Repository search, user search, tech stack detection
- **Rate Limits:** 60 req/hour (no token), 5000 req/hour (with token)

### Domain Scanner
- **Method:** DNS enumeration + subdomain bruteforce
- **Features:** A/MX/TXT/NS records, common subdomain discovery
- **Coverage:** 12 common subdomain prefixes

## Tips

1. **Use GitHub Token:** Create a Personal Access Token at https://github.com/settings/tokens for increased rate limits.

2. **Verbose Mode:** Add `-v` to see detailed results in real-time.

3. **Combine Modules:** Use multiple modules together for comprehensive recon:
   ```bash
   python target-scout.py --company "Target" --output full-report.json -v
   ```

4. **Rate Limiting:** Scanner includes built-in delays to avoid API limits.
