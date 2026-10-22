#!/usr/bin/env python3
"""
Lightweight Static Web Server for Social Media Downloader Landing Page
Zero external dependencies, minimal memory footprint (< 10 MB RAM).
"""

import http.server
import socketserver
import os
import sys
import argparse

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

class CustomHTTPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Cache control headers
        if self.path.endswith(('.css', '.js', '.png', '.ico', '.svg', '.woff2')):
            self.send_header('Cache-Control', 'public, max-age=86400')
        else:
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
        super().end_headers()

def run(port=8082, directory=None):
    if directory is None:
        directory = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(directory)
    
    handler = CustomHTTPHandler
    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        print(f"[SMD Web] Serving at http://0.0.0.0:{port} (Directory: {directory})")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SMD Landing Page Server")
    parser.add_argument("--port", type=int, default=8082, help="Port to listen on (default: 8082)")
    parser.add_argument("--dir", type=str, default=None, help="Directory to serve")
    args = parser.parse_args()
    
    run(port=args.port, directory=args.dir)
