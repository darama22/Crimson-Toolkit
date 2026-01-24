#!/usr/bin/env python3
"""
GitHub Module for TARGET-SCOUT
Searches GitHub for repositories, code, and users related to target company
"""

import requests
import time
from typing import Dict, List

class GitHubScanner:
    """GitHub API scanner for OSINT"""
    
    def __init__(self, company_name: str, github_token: str = None):
        self.company_name = company_name
        self.api_base = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
    
    def search_repositories(self) -> List[Dict]:
        """Search for repositories related to company"""
        repos = []
        try:
            # Search for repos with company name
            url = f"{self.api_base}/search/repositories"
            params = {
                "q": self.company_name,
                "per_page": 10,
                "sort": "stars"
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    repos.append({
                        "name": item.get("full_name"),
                        "description": item.get("description", ""),
                        "stars": item.get("stargazers_count", 0),
                        "language": item.get("language", "Unknown"),
                        "url": item.get("html_url")
                    })
            elif response.status_code == 403:
                return {"error": "Rate limited. Consider using a GitHub token."}
            
            time.sleep(1)  # Rate limiting
        except Exception as e:
            return {"error": str(e)}
        
        return repos
    
    def search_users(self) -> List[Dict]:
        """Search for GitHub users with company in profile"""
        users = []
        try:
            url = f"{self.api_base}/search/users"
            params = {
                "q": f"{self.company_name} in:bio,company",
                "per_page": 10
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    users.append({
                        "username": item.get("login"),
                        "profile_url": item.get("html_url"),
                        "avatar": item.get("avatar_url")
                    })
            
            time.sleep(1)
        except Exception as e:
            return {"error": str(e)}
        
        return users
    
    def detect_tech_stack(self, repos: List[Dict]) -> Dict:
        """Analyze repositories to detect technology stack"""
        languages = {}
        
        for repo in repos:
            if isinstance(repo, dict) and "language" in repo:
                lang = repo["language"]
                if lang and lang != "Unknown":
                    languages[lang] = languages.get(lang, 0) + 1
        
        # Sort by frequency
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "primary_languages": dict(sorted_langs[:5]),
            "total_repos_analyzed": len(repos)
        }
    
    def scan(self) -> Dict:
        """Execute full GitHub scan"""
        repos = self.search_repositories()
        users = self.search_users()
        
        tech_stack = {}
        if isinstance(repos, list):
            tech_stack = self.detect_tech_stack(repos)
        
        return {
            "repositories": repos,
            "users": users,
            "tech_stack": tech_stack,
            "scan_status": "completed"
        }
