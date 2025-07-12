#!/usr/bin/env python3
"""
LinkSync SQL to PocketBase Importer (Browser Auth Version)

This script reads links from a SQL file and imports them into a PocketBase collection
using the authentication token from the browser's localStorage.

Usage:
    1. First, log into your LinkSync app in the browser
    2. Run this script: python inseart_browser_auth.py [--sql-file SQL_FILE_PATH]

Example:
    python inseart_browser_auth.py --sql-file links.sql

Note: 
    - Make sure you're logged into the LinkSync app in your browser first
    - The script will read the authentication token from browser localStorage
    - You need to have a 'links' collection with the proper schema already set up in PocketBase
"""
import re
import json
from datetime import datetime
import sys
import os
import urllib.request
import urllib.error
import urllib.parse
import base64
import http.client
import time
import argparse
import ssl
import glob
from urllib.parse import urlparse
from http.client import HTTPSConnection, HTTPConnection
import socket
import sqlite3
from pathlib import Path

# Configuration - Global variables
POCKETBASE_URL = "http://localhost:8090"  # Update with your PocketBase URL
API_COLLECTION = "links"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_header(message):
    print(f"\n{Colors.BOLD}{message}{Colors.END}")
    print("-" * len(message))

# Function to extract favicon URL from a website (improved version matching Svelte app)
def fetch_favicon(url):
    """
    Fetch favicon URL using the same logic as the Svelte app's metadata service
    """
    try:
        # Parse the URL to get the domain
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed_url = urlparse(url)
        domain = parsed_url.hostname
        if not domain:
            print_error(f"Could not parse domain from URL: {url}")
            return ""
        
        base_url = f"{parsed_url.scheme}://{domain}"
        
        print_info(f"Fetching favicon for: {domain}")
        
        # First try to fetch the page's HTML to find favicon/logo links (like metascraper)
        try:
            context = ssl._create_unverified_context()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                if response.status != 200:
                    print_warning(f"Non-200 response {response.status} for {url}")
                else:
                    html = response.read().decode('utf-8', errors='ignore')
                    
                    # Look for various logo/icon patterns in HTML (similar to metascraper-logo)
                    logo_patterns = [
                        # Open Graph image (prioritized)
                        r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
                        r'<meta[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
                        # Apple touch icons (high quality)
                        r'<link[^>]*rel=["\'][^"\']*apple-touch-icon[^"\']*["\'][^>]*href=["\']([^"\']+)["\']',
                        r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\'][^"\']*apple-touch-icon[^"\']*["\']',
                        # Standard favicon links
                        r'<link[^>]*rel=["\']icon["\'][^>]*href=["\']([^"\']+)["\']',
                        r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']icon["\']',
                        r'<link[^>]*rel=["\']shortcut icon["\'][^>]*href=["\']([^"\']+)["\']',
                        r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']shortcut icon["\']',
                    ]
                    
                    for pattern in logo_patterns:
                        matches = re.findall(pattern, html, re.IGNORECASE)
                        if matches:
                            for favicon_url in matches:
                                # Clean up the URL
                                favicon_url = favicon_url.strip()
                                if not favicon_url:
                                    continue
                                
                                # Handle relative URLs
                                if favicon_url.startswith('//'):
                                    favicon_url = f"{parsed_url.scheme}:{favicon_url}"
                                elif favicon_url.startswith('/'):
                                    favicon_url = f"{base_url}{favicon_url}"
                                elif not favicon_url.startswith(('http://', 'https://')):
                                    favicon_url = f"{base_url}/{favicon_url}"
                                
                                # Validate the URL format
                                try:
                                    parsed_favicon = urlparse(favicon_url)
                                    if not parsed_favicon.netloc:
                                        continue
                                except:
                                    continue
                                
                                # Check if favicon exists and is accessible
                                try:
                                    favicon_req = urllib.request.Request(favicon_url, headers=headers)
                                    favicon_req.get_method = lambda: 'HEAD'
                                    with urllib.request.urlopen(favicon_req, timeout=5, context=context) as favicon_response:
                                        if favicon_response.status == 200:
                                            # Check content type to ensure it's an image
                                            content_type = favicon_response.headers.get('Content-Type', '')
                                            if any(img_type in content_type.lower() for img_type in ['image/', 'application/octet-stream']):
                                                print_success(f"Found valid favicon: {favicon_url}")
                                                return favicon_url
                                            else:
                                                print_warning(f"Favicon URL returned non-image content: {content_type}")
                                except Exception as e:
                                    print_warning(f"Favicon check failed for {favicon_url}: {e}")
                                    continue
        except Exception as e:
            print_warning(f"Error fetching HTML from {url}: {e}")
        
        # Try common favicon locations if no favicon found in HTML
        favicon_locations = [
            f"{base_url}/favicon.ico",
            f"{base_url}/favicon.png",
            f"{base_url}/apple-touch-icon.png",
            f"{base_url}/apple-touch-icon-precomposed.png",
            f"{base_url}/apple-touch-icon-120x120.png",
            f"{base_url}/apple-touch-icon-152x152.png",
            f"{base_url}/apple-touch-icon-180x180.png"
        ]
        
        print_info(f"Trying common favicon locations for {domain}...")
        for favicon_url in favicon_locations:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                req = urllib.request.Request(favicon_url, headers=headers)
                req.get_method = lambda: 'HEAD'
                with urllib.request.urlopen(req, timeout=5, context=ssl._create_unverified_context()) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if any(img_type in content_type.lower() for img_type in ['image/', 'application/octet-stream']):
                            print_success(f"Found favicon at common location: {favicon_url}")
                            return favicon_url
            except Exception as e:
                print_warning(f"Failed to check {favicon_url}: {e}")
                continue
        
        # Fallback to Google's favicon service (same as Svelte app)
        google_favicon = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        print_info(f"Using Google favicon service as fallback: {google_favicon}")
        
        # Verify Google's service responds
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            req = urllib.request.Request(google_favicon, headers=headers)
            req.get_method = lambda: 'HEAD'
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print_success(f"Google favicon service is accessible: {google_favicon}")
                    return google_favicon
        except Exception as e:
            print_warning(f"Google favicon service failed: {e}")
        
        print_warning(f"No favicon found for {domain}")
        return ""
    
    except Exception as e:
        print_error(f"Error fetching favicon for {url}: {e}")
        return ""

# Function to parse the SQL file
def parse_sql_file(file_path):
    print_info(f"Reading SQL file: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            sql_content = file.read()
    except FileNotFoundError:
        print_error(f"File not found: {file_path}")
        return []
    except Exception as e:
        print_error(f"Error reading file: {e}")
        return []
    
    # Extract INSERT statements
    insert_pattern = r"INSERT INTO `links` \(`id`, `url`, `name`, `description`, `tags`, `username`, `email`, `added_date`, `visibility`, `clicks`\) VALUES\s*([^;]+);"
    insert_match = re.search(insert_pattern, sql_content, re.DOTALL)
    
    if not insert_match:
        print_warning("No INSERT statements found in the SQL file.")
        return []
    
    values_content = insert_match.group(1)
    
    # Extract individual rows
    rows_pattern = r"\((\d+),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*([^,]*),\s*([^,]*),\s*'([^']*)',\s*'([^']*)',\s*(\d+)\)"
    rows = re.findall(rows_pattern, values_content)
    
    if not rows:
        print_warning("No link entries found in the SQL file.")
        return []
    
    links = []
    for row in rows:
        id_val, url, name, description, tags_str, username, email, added_date, visibility, clicks = row
        
        # Convert tags string to array
        tags = [tag.strip() for tag in tags_str.split(',')]
        
        links.append({
            'original_id': id_val,
            'url': url,
            'name': name,
            'description': description,
            'tags': tags,
            'username': None if username == 'NULL' else username.strip("'"),
            'email': None if email == 'NULL' else email.strip("'"),
            'added_date': added_date,
            'visibility': visibility,
            'clicks': int(clicks)
        })
    
    print_success(f"Successfully parsed {len(links)} links from SQL file")
    return links

# Function to get Chrome's localStorage data
def get_chrome_localStorage():
    """Get localStorage data from Chrome's Local Storage leveldb"""
    try:
        # Chrome's localStorage path on Windows
        chrome_user_data = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default')
        local_storage_path = os.path.join(chrome_user_data, 'Local Storage', 'leveldb')
        
        if not os.path.exists(local_storage_path):
            print_warning("Chrome localStorage path not found")
            return None
        
        print_info(f"Looking for localStorage data in: {local_storage_path}")
        
        # Try to find localStorage files
        import glob
        ldb_files = glob.glob(os.path.join(local_storage_path, '*.ldb'))
        
        if not ldb_files:
            print_warning("No .ldb files found in Chrome localStorage")
            return None
        
        # Search for our auth key in the files
        auth_key = "pocketbase_auth_v2"
        localhost_key = f"_http://localhost:8090\x00\x01{auth_key}"
        
        for ldb_file in ldb_files:
            try:
                with open(ldb_file, 'rb') as f:
                    content = f.read()
                    
                # Look for our key in the binary data
                if localhost_key.encode() in content:
                    # Found our key, now try to extract the JSON data
                    start_idx = content.find(localhost_key.encode())
                    if start_idx != -1:
                        # Look for JSON data after the key
                        json_start = content.find(b'{', start_idx)
                        if json_start != -1:
                            # Find the end of JSON (this is tricky with binary data)
                            brace_count = 0
                            json_end = json_start
                            for i in range(json_start, len(content)):
                                if content[i:i+1] == b'{':
                                    brace_count += 1
                                elif content[i:i+1] == b'}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i + 1
                                        break
                            
                            try:
                                json_data = content[json_start:json_end].decode('utf-8')
                                auth_data = json.loads(json_data)
                                print_success("Found authentication data in Chrome localStorage")
                                return auth_data
                            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                                print_warning(f"Failed to parse JSON from localStorage: {e}")
                                continue
            except Exception as e:
                print_warning(f"Error reading {ldb_file}: {e}")
                continue
        
        print_warning("Authentication data not found in Chrome localStorage")
        return None
        
    except Exception as e:
        print_error(f"Error accessing Chrome localStorage: {e}")
        return None

# Alternative method: Manual token input
def get_manual_token():
    """Ask user to manually provide the authentication token"""
    print_info("Please provide the authentication token manually:")
    print_info("1. Open your browser and go to the LinkSync app")
    print_info("2. Open Developer Tools (F12)")
    print_info("3. Go to Application/Storage tab")
    print_info("4. Find Local Storage -> http://localhost:8090")
    print_info("5. Look for 'pocketbase_auth_v2' key")
    print_info("6. Copy the entire JSON value OR just the token value")
    
    try:
        token_input = input("\nPaste the authentication data here: ").strip()
        if not token_input:
            return None
        
        # Check if it's a full JSON object or just a token
        if token_input.startswith('{'):
            # It's a JSON object
            try:
                auth_data = json.loads(token_input)
                
                # Validate structure
                if 'token' in auth_data and ('model' in auth_data or 'record' in auth_data):
                    print_success("Authentication data validated")
                    # Normalize the structure - some versions use 'record' instead of 'model'
                    if 'record' in auth_data and 'model' not in auth_data:
                        auth_data['model'] = auth_data['record']
                    return auth_data
                else:
                    print_error("Invalid authentication data structure")
                    return None
            except json.JSONDecodeError as e:
                print_error(f"Invalid JSON format: {e}")
                return None
        else:
            # It's just a token, we need to decode it to get user info
            try:
                # Decode the JWT token to get user info
                token_parts = token_input.split('.')
                if len(token_parts) != 3:
                    print_error("Invalid token format")
                    return None
                
                # Decode the payload (add padding if needed)
                payload_b64 = token_parts[1]
                # Add padding if needed
                padding = len(payload_b64) % 4
                if padding:
                    payload_b64 += '=' * (4 - padding)
                
                payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                user_id = payload.get('id')
                
                if not user_id:
                    print_error("Could not extract user ID from token")
                    return None
                
                # Create a mock auth_data structure
                auth_data = {
                    'token': token_input,
                    'model': {
                        'id': user_id,
                        'email': 'user@example.com'  # We don't have the email from token
                    }
                }
                
                print_success("Token validated and user ID extracted")
                return auth_data
                
            except Exception as e:
                print_error(f"Error decoding token: {e}")
                return None
            
    except KeyboardInterrupt:
        print_info("\nOperation cancelled")
        return None

# Function to get browser authentication
def get_browser_auth():
    """Get authentication token from browser localStorage"""
    print_info("Attempting to get authentication from browser...")
    
    # First try Chrome localStorage
    auth_data = get_chrome_localStorage()
    
    if not auth_data:
        print_warning("Could not automatically extract authentication from browser")
        print_info("Falling back to manual token entry...")
        auth_data = get_manual_token()
    
    if not auth_data:
        return None, None
    
    # Validate token structure
    if 'token' not in auth_data or ('model' not in auth_data and 'record' not in auth_data):
        print_error("Invalid authentication data structure")
        return None, None
    
    # Normalize the structure - some versions use 'record' instead of 'model'
    if 'record' in auth_data and 'model' not in auth_data:
        auth_data['model'] = auth_data['record']
    
    # Check if token is expired
    try:
        token = auth_data['token']
        if isinstance(token, str):
            token_parts = token.split('.')
            if len(token_parts) == 3:
                # Add padding if needed
                payload_b64 = token_parts[1]
                padding = len(payload_b64) % 4
                if padding:
                    payload_b64 += '=' * (4 - padding)
                
                payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                exp = payload.get('exp', 0)
                current_time = int(time.time())
                
                if exp < current_time:
                    print_error("Authentication token is expired. Please log in again in the browser.")
                    return None, None
        
        user_model = auth_data.get('model', {})
        if isinstance(user_model, dict):
            user_id = user_model.get('id')
            user_email = user_model.get('email', 'Unknown')
        else:
            print_error("Invalid user model structure")
            return None, None
        
        if not user_id:
            print_error("User ID not found in authentication data")
            return None, None
            
        print_success(f"Using authentication for user: {user_email} (ID: {user_id})")
        
        return token, user_id
        
    except Exception as e:
        print_error(f"Error validating token: {e}")
        return None, None

# Function to insert a link into PocketBase using browser auth
def insert_link(link_data, auth_token, user_id, skip_favicons=False):
    url = f"{POCKETBASE_URL}/api/collections/{API_COLLECTION}/records"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    # Fetch favicon for the link (matching Svelte app behavior)
    favicon = ""
    favicon_found = False
    if not skip_favicons:
        try:
            favicon = fetch_favicon(link_data['url'])
            if favicon and favicon.strip():
                favicon_found = True
                print_success(f"Favicon found for {link_data['name']}: {favicon}")
            else:
                print_warning(f"No valid favicon found for: {link_data['name']}")
                favicon = ""  # Ensure it's empty string, not None
        except Exception as e:
            print_warning(f"Failed to fetch favicon for {link_data['name']}: {e}")
            favicon = ""
    
    # Prepare data for PocketBase format (exactly matching Svelte app structure)
    pb_data = {
        "url": link_data['url'],
        "name": link_data['name'],
        "description": link_data['description'],
        "tags": link_data['tags'],
        "visibility": link_data['visibility'],
        "user": user_id,
        "favicon": favicon,  # This should match the 'favicon' field from the model
        "clicks": link_data.get('clicks', 0)  # Default to 0 if not provided
    }
    
    # Debug: Print the data being sent (truncate long URLs)
    favicon_display = favicon[:50] + '...' if len(favicon) > 50 else favicon
    print_info(f"Inserting: {pb_data['name']} | Favicon: {favicon_display if favicon else 'None'}")
    
    data = json.dumps(pb_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            if response.status in [200, 201]:
                response_data = json.loads(response.read().decode('utf-8'))
                # Verify favicon was actually saved
                saved_favicon = response_data.get('favicon', '')
                
                if saved_favicon and saved_favicon.strip():
                    favicon_display = saved_favicon[:50] + '...' if len(saved_favicon) > 50 else saved_favicon
                    print_success(f"✓ Link saved with favicon: {favicon_display}")
                    return (True, True)  # Success with favicon
                elif favicon and favicon.strip():
                    print_warning(f"✓ Link saved but favicon was not stored (sent: {favicon[:50]}...)")
                    return (True, False)  # Success but no favicon stored
                else:
                    print_info(f"✓ Link saved without favicon (none provided)")
                    return (True, False)  # Success, no favicon attempted
            else:
                print_warning(f"Unexpected status code: {response.status}")
                return (False, False)
    except urllib.error.HTTPError as e:
        try:
            error_msg = e.read().decode('utf-8')
            error_data = json.loads(error_msg)
            
            # Check for duplicate/unique constraint violations
            if (e.code == 400 and 
                ("not unique" in error_msg.lower() or 
                 "already exists" in error_msg.lower() or
                 any("unique" in str(v).lower() for v in error_data.get('data', {}).values()))):
                print_warning(f"Link already exists: {link_data['name']} ({link_data['url']})")
                return (True, favicon_found)  # Consider it successful since the link exists
            else:
                print_error(f"Failed to insert link '{link_data['name']}': {error_msg}")
                # Print detailed error for debugging
                if 'data' in error_data:
                    for field, error_info in error_data['data'].items():
                        if isinstance(error_info, dict) and 'message' in error_info:
                            print_error(f"  {field}: {error_info['message']}")
                        else:
                            print_error(f"  {field}: {error_info}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            error_msg = e.read().decode('utf-8', errors='ignore')
            print_error(f"Failed to insert link '{link_data['name']}': {error_msg}")
        return (False, False)
    except urllib.error.URLError as e:
        print_error(f"Failed to insert link '{link_data['name']}': {e.reason}")
        return (False, False)
    except ConnectionRefusedError:
        print_error("Connection refused - PocketBase server may be down")
        return (False, False)
    except Exception as e:
        print_error(f"Failed to insert link '{link_data['name']}': {e}")
        return (False, False)

# Function to show a progress bar
def progress_bar(current, total, width=50):
    progress = int(width * current / total)
    bar = "█" * progress + "░" * (width - progress)
    percent = int(100 * current / total)
    return f"[{bar}] {percent}%"

def main():
    global POCKETBASE_URL
    
    # Get configuration from command-line arguments
    parser = argparse.ArgumentParser(description='Import links from SQL file to PocketBase using browser authentication')
    parser.add_argument('--sql-file', default=os.path.join(os.path.dirname(__file__), "links.sql"), help='Path to SQL file')
    parser.add_argument('--skip-favicons', action='store_true', help='Skip favicon fetching (faster but links will have no icons)')
    parser.add_argument('--url', default=POCKETBASE_URL, help='PocketBase URL')
    args = parser.parse_args()
    
    POCKETBASE_URL = args.url
    
    print_header("LinkSync SQL to PocketBase Importer (Browser Auth)")
    print_info(f"PocketBase URL: {POCKETBASE_URL}")
    print_info(f"SQL File: {args.sql_file}")
    print_info(f"Favicon Fetching: {'Disabled' if args.skip_favicons else 'Enabled'}")
    
    # Parse SQL file
    print_header("Step 1: Parsing SQL File")
    links = parse_sql_file(args.sql_file)
    if not links:
        print_error("No links found in the SQL file. Exiting.")
        sys.exit(1)
    
    # Get browser authentication
    print_header("Step 2: Getting Browser Authentication")
    auth_token, user_id = get_browser_auth()
    if not auth_token or not user_id:
        print_error("Failed to get authentication from browser. Exiting.")
        sys.exit(1)
    
    # Insert links into PocketBase
    print_header("Step 3: Inserting Links into PocketBase")
    success_count = 0
    favicon_count = 0
    failed_count = 0
    
    print_info(f"Starting import of {len(links)} links...")
    
    for i, link in enumerate(links):
        progress = progress_bar(i, len(links))
        
        # Show more detailed progress
        status_icon = "⚙️"
        print(f"\r{progress} {status_icon} Processing: {link['name'][:40]}{'...' if len(link['name']) > 40 else ''}   ", end='', flush=True)
        
        result = insert_link(link, auth_token, user_id, args.skip_favicons)
        success, has_favicon = result
        
        if success:
            success_count += 1
            if has_favicon:
                favicon_count += 1
                status_icon = "✅"
            else:
                status_icon = "📝"
        else:
            failed_count += 1
            status_icon = "❌"
            # If we have too many consecutive failures, check if server is still running
            if failed_count > 5 and (failed_count % 5 == 0):
                print(f"\n⚠ Multiple failures detected. Checking server status...")
                try:
                    test_req = urllib.request.Request(f"{POCKETBASE_URL}/api/health")
                    with urllib.request.urlopen(test_req, timeout=5) as test_response:
                        if test_response.status == 200:
                            print_info("Server is still running, continuing...")
                        else:
                            print_warning(f"Server returned status {test_response.status}")
                except Exception as e:
                    print_error(f"Cannot reach server: {e}")
                    print_error("Stopping import due to server connectivity issues")
                    break
        
        # Update progress with status
        print(f"\r{progress} {status_icon} Processed: {link['name'][:40]}{'...' if len(link['name']) > 40 else ''}   ", end='', flush=True)
        
        # Small delay to prevent overwhelming the server
        time.sleep(0.2)  # Slightly longer delay to give favicon fetching time
    
    # Clear the progress bar line
    print("\r" + " " * 80 + "\r", end='')
    
    # Summary
    print_header("Import Summary")
    print_info(f"Total links processed: {len(links)}")
    print_success(f"Successfully imported: {success_count}")
    if not args.skip_favicons:
        print_info(f"Links with favicons: {favicon_count}")
    if success_count < len(links):
        print_warning(f"Failed to import: {len(links) - success_count}")
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}Import process completed!{Colors.END}")
    
    if success_count > 0:
        print_info(f"You can view your links at: {POCKETBASE_URL}/_/#/collections/links/records")

if __name__ == "__main__":
    main()
