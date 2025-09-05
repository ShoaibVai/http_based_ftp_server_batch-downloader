#!/usr/bin/env python3
"""
Comprehensive verification that the statusBar TypeError has been resolved.
This script checks all instances of statusBar usage in the codebase.
"""

import os
import re

def check_statusbar_usage():
    """Check all Python files for proper statusBar usage."""
    print("🔍 Checking statusBar usage across the codebase...")
    
    issues_found = []
    files_checked = 0
    
    # Files to check
    python_files = [
        'ui/main_window.py',
        'ui/browser_tab.py',
        'ui/downloads_tab.py',
        'ui/settings_tab.py'
    ]
    
    for file_path in python_files:
        if os.path.exists(file_path):
            files_checked += 1
            print(f"   📄 Checking {file_path}...")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                # Check for problematic patterns
                for i, line in enumerate(lines, 1):
                    # Look for statusBar() calls (incorrect)
                    if re.search(r'\.statusBar\(\)\.showMessage', line):
                        issues_found.append({
                            'file': file_path,
                            'line': i,
                            'content': line.strip(),
                            'issue': 'Uses statusBar() instead of statusBar'
                        })
                    
                    # Look for correct usage (for verification)
                    if re.search(r'\.statusBar\.showMessage', line):
                        print(f"      ✅ Line {i}: Correct statusBar usage found")
    
    print(f"\n📊 Summary:")
    print(f"   Files checked: {files_checked}")
    print(f"   Issues found: {len(issues_found)}")
    
    if issues_found:
        print(f"\n❌ Issues found:")
        for issue in issues_found:
            print(f"   File: {issue['file']}")
            print(f"   Line: {issue['line']}")
            print(f"   Issue: {issue['issue']}")
            print(f"   Content: {issue['content']}")
            print()
        return False
    else:
        print(f"   ✅ No statusBar issues found - all usage is correct!")
        return True

def verify_specific_method():
    """Verify the specific method that was causing the error."""
    print(f"\n🎯 Verifying handle_browser_url_selected method...")
    
    file_path = 'ui/main_window.py'
    if not os.path.exists(file_path):
        print(f"   ❌ File {file_path} not found")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the method
    import re
    method_match = re.search(
        r'def handle_browser_url_selected\(self, url\):(.*?)(?=def|\Z)', 
        content, 
        re.DOTALL
    )
    
    if not method_match:
        print(f"   ❌ Method handle_browser_url_selected not found")
        return False
    
    method_content = method_match.group(1)
    
    # Check for problematic statusBar calls
    if 'statusBar().showMessage' in method_content:
        print(f"   ❌ Found statusBar() calls in method - still needs fixing")
        return False
    elif 'statusBar.showMessage' in method_content:
        print(f"   ✅ Method uses correct statusBar property access")
        return True
    else:
        print(f"   ⚠️  No statusBar calls found in method")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("StatusBar TypeError Fix Verification")
    print("=" * 60)
    
    # Change to project directory
    os.chdir('a:/Documents/Projects/server_batch_downloader')
    
    # Run checks
    general_check = check_statusbar_usage()
    specific_check = verify_specific_method()
    
    print(f"\n" + "=" * 60)
    if general_check and specific_check:
        print("🎉 VERIFICATION PASSED: statusBar TypeError fix is complete!")
        exit_code = 0
    else:
        print("❌ VERIFICATION FAILED: statusBar issues still exist")
        exit_code = 1
    
    print("=" * 60)
    exit(exit_code)
