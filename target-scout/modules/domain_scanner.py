#!/usr/bin/env python3
"""
Domain Module for TARGET-SCOUT
Enumerates subdomains and performs basic DNS/WHOIS reconnaissance
"""

import socket
import dns.resolver
from typing import Dict, List

class DomainScanner:
    """Domain and DNS reconnaissance"""
    
    def __init__(self, company_name: str):
        self.company_name = company_name
        self.tlds_tried = []
        self.domain = self._guess_domain(company_name)
    
    def _guess_domain(self, company: str) -> str:
        """
        Convert company name to likely domain by trying multiple TLDs
        Returns the first domain that resolves
        """
        # Clean company name
        clean = company.lower().replace(" ", "").replace("inc", "").replace("ltd", "").replace(".", "")
        
        # Common TLDs to try (in priority order)
        tlds = [".com", ".es", ".net", ".org", ".io", ".co", ".uk", ".de", ".fr"]
        
        for tld in tlds:
            test_domain = f"{clean}{tld}"
            self.tlds_tried.append(test_domain)
            
            try:
                socket.gethostbyname(test_domain)
                # Domain resolves! Use this one
                return test_domain
            except socket.gaierror:
                continue  # Try next TLD
        
        # If nothing resolves, default to .com
        return f"{clean}.com"
    
    def check_domain_exists(self) -> bool:
        """Check if guessed domain resolves"""
        try:
            socket.gethostbyname(self.domain)
            return True
        except socket.gaierror:
            return False
    
    def enumerate_subdomains(self) -> List[str]:
        """Try common subdomain prefixes"""
        common_subdomains = [
            "www", "mail", "ftp", "admin", "portal", "vpn",
            "api", "dev", "staging", "test", "blog", "shop"
        ]
        
        found_subdomains = []
        
        for sub in common_subdomains:
            subdomain = f"{sub}.{self.domain}"
            try:
                socket.gethostbyname(subdomain)
                found_subdomains.append(subdomain)
            except socket.gaierror:
                pass  # Subdomain doesn't exist
        
        return found_subdomains
    
    def get_dns_records(self) -> Dict:
        """Query DNS records (A, MX, TXT, NS)"""
        records = {
            "A": [],
            "MX": [],
            "TXT": [],
            "NS": []
        }
        
        try:
            resolver = dns.resolver.Resolver()
            
            # A records
            try:
                answers = resolver.resolve(self.domain, 'A')
                records["A"] = [str(rdata) for rdata in answers]
            except:
                pass
            
            # MX records
            try:
                answers = resolver.resolve(self.domain, 'MX')
                records["MX"] = [str(rdata.exchange) for rdata in answers]
            except:
                pass
            
            # TXT records
            try:
                answers = resolver.resolve(self.domain, 'TXT')
                records["TXT"] = [str(rdata) for rdata in answers]
            except:
                pass
            
            # NS records
            try:
                answers = resolver.resolve(self.domain, 'NS')
                records["NS"] = [str(rdata) for rdata in answers]
            except:
                pass
        
        except Exception as e:
            records["error"] = str(e)
        
        return records
    
    def scan(self) -> Dict:
        """Execute full domain scan"""
        domain_exists = self.check_domain_exists()
        
        result = {
            "guessed_domain": self.domain,
            "domain_exists": domain_exists,
            "tlds_tried": self.tlds_tried,
            "subdomains": [],
            "dns_records": {},
            "scan_status": "completed"
        }
        
        if domain_exists:
            result["subdomains"] = self.enumerate_subdomains()
            result["dns_records"] = self.get_dns_records()
        else:
            result["note"] = f"Domain {self.domain} does not resolve. Tried: {', '.join(self.tlds_tried[:3])}..."
        
        return result
