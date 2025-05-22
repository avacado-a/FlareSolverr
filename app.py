from flask import Flask, request, Response, render_template_string, redirect, url_for
import requests
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)

# HTML template for the GUI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Proxy Browser</title>
    <script>
        // Inject JavaScript to prevent links from opening in a new tab
        document.addEventListener('DOMContentLoaded', () => {
            document.body.addEventListener('click', (e) => {
                if (e.target.tagName === 'A') {
                    e.preventDefault();
                    window.location.href = '/proxy?url=' + encodeURIComponent(e.target.href);
                }
            });
        });

        // Register the service worker
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/service-worker.js').then(() => {
                console.log('Service Worker registered.');
            });
        }
    </script>
</head>
<body>
    <form method="GET" action="/proxy">
        <input type="text" name="url" placeholder="Enter URL" required>
        <button type="submit">Go</button>
    </form>
    <button onclick="history.back()">Back</button>
    <button onclick="history.forward()">Forward</button>
    <div id="content">
        {{ content|safe }}
    </div>
</body>
</html>
"""

# Service worker script
SERVICE_WORKER_SCRIPT = """
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    if (url.origin === location.origin && url.pathname.startsWith('/proxy-resource')) {
        // Redirect proxy resource requests to the actual target
        const targetUrl = url.searchParams.get('url');
        event.respondWith(fetch(targetUrl, { method: event.request.method, headers: event.request.headers }));
    } else {
        event.respondWith(fetch(event.request));
    }
});
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, content="")

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return redirect(url_for('index'))

    try:
        # Fetch the content from the target URL
        resp = requests.get(url, headers=request.headers, allow_redirects=True)
        print(resp.status_code, resp.url)  # Debugging line to check the response status and URL
        base_url = "{0.scheme}://{0.netloc}".format(urlparse(url))
        content = resp.text

        # Inject a <base> tag to set the base URL for all relative links and resources
        content = content.replace(
            '<head>',
            f'<head><base href="{base_url}/">'
        )

        # Rewrite relative URLs for static resources and links
        def rewrite_all_requests(match):
            original_url = match.group(1)
            absolute_url = urljoin(base_url, original_url)
            return match.group(0).replace(original_url, f'/proxy-resource?url={absolute_url}')
            absolute_url = urljoin(base_url, original_url)
            return match.group(0).replace(original_url, absolute_url)

        content = re.sub(r'src=["\'](.*?)["\']', rewrite_relative_urls, content)
        content = re.sub(r'href=["\'](.*?)["\']', rewrite_relative_urls, content)

        # Inject JavaScript to prevent links from opening in a new tab
        content = content.replace(
            '</body>',
            '<script>'
            'document.querySelectorAll("a").forEach(a => a.target = "");'
            '</script></body>'
        )

        return render_template_string(HTML_TEMPLATE, content=content)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/proxy-resource')
def proxy_resource():
    url = request.args.get('url')
    if not url:
        return "Missing URL", 400

    try:
        # Fetch the resource from the target URL
        resp = requests.get(url, headers=request.headers, stream=True)
        return Response(resp.iter_content(chunk_size=10 * 1024), content_type=resp.headers.get('Content-Type'))
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/service-worker.js')
def service_worker():
    return Response(SERVICE_WORKER_SCRIPT, content_type='application/javascript')

if __name__ == '__main__':
    app.run(debug=True)