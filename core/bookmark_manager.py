# core/bookmark_manager.py
# Bookmark management system for FTP servers

import json
import os
import logging

logger = logging.getLogger(__name__)

class BookmarkManager:
    """Manages server bookmarks and categories for quick navigation."""
    
    def __init__(self, servers_file="servers.json"):
        self.servers_file = servers_file
        self.servers = {}
        self.load_bookmarks()
    
    def load_bookmarks(self):
        """Load bookmarks from the servers.json file."""
        try:
            if os.path.exists(self.servers_file):
                with open(self.servers_file, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
            else:
                logger.warning(f"Servers file {self.servers_file} not found. Using empty bookmarks.")
                self.servers = {"CircleFTP": {}, "Dhakaflix": {}}
        except Exception as e:
            logger.error(f"Error loading bookmarks: {e}")
            self.servers = {"CircleFTP": {}, "Dhakaflix": {}}
    
    def get_servers(self):
        """Get list of available servers."""
        return list(self.servers.keys())
    
    def get_categories(self, server_name):
        """Get categories for a specific server."""
        return list(self.servers.get(server_name, {}).keys())
    
    def get_url(self, server_name, category_name):
        """Get URL for a specific server and category."""
        return self.servers.get(server_name, {}).get(category_name, "")
    
    def add_bookmark(self, server_name, category_name, url):
        """Add a new bookmark."""
        if server_name not in self.servers:
            self.servers[server_name] = {}
        self.servers[server_name][category_name] = url
        self.save_bookmarks()
    
    def remove_bookmark(self, server_name, category_name):
        """Remove a bookmark."""
        if server_name in self.servers and category_name in self.servers[server_name]:
            del self.servers[server_name][category_name]
            self.save_bookmarks()
    
    def save_bookmarks(self):
        """Save bookmarks to the servers.json file."""
        try:
            with open(self.servers_file, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving bookmarks: {e}")
    
    def generate_bookmarks_html(self):
        """Generate HTML content for the bookmark homepage."""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>FTP Server Bookmarks</title>
            <meta charset="UTF-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: linear-gradient(135deg, #232946, #393E6B);
                    color: #E0E0E0;
                }
                h1 { 
                    color: #2196F3; 
                    text-align: center;
                    margin-bottom: 30px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
                .server-section { 
                    margin-bottom: 30px; 
                    background: rgba(57, 62, 107, 0.7);
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
                }
                .server-name { 
                    color: #FF9800; 
                    border-bottom: 2px solid #2196F3; 
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }
                .category-list { 
                    list-style-type: none; 
                    padding-left: 20px; 
                }
                .category-item { 
                    margin: 8px 0; 
                }
                .category-link { 
                    text-decoration: none; 
                    color: #4CAF50; 
                    padding: 8px 15px;
                    border-radius: 6px;
                    display: inline-block;
                    transition: all 0.3s ease;
                    border: 1px solid transparent;
                }
                .category-link:hover { 
                    background: linear-gradient(45deg, #2196F3, #FF9800);
                    color: white;
                    text-decoration: none;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.4);
                }
                .stats {
                    text-align: center;
                    margin-top: 20px;
                    color: #888;
                    font-style: italic;
                }
            </style>
        </head>
        <body>
            <h1>🚀 FTP Server Bookmarks</h1>
        """
        
        total_categories = 0
        for server in self.get_servers():
            categories = self.get_categories(server)
            total_categories += len(categories)
            
            html += f'<div class="server-section">'
            html += f'<h2 class="server-name">📁 {server}</h2>'
            html += '<ul class="category-list">'
            
            for category in categories:
                url = self.get_url(server, category)
                html += f'<li class="category-item">'
                html += f'<a href="{url}" class="category-link">📂 {category}</a>'
                html += f'</li>'
            
            html += '</ul></div>'
        
        html += f"""
            <div class="stats">
                Total Servers: {len(self.get_servers())} | Total Categories: {total_categories}
            </div>
        </body>
        </html>
        """
        return html
