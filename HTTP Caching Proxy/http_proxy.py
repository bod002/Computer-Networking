from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.parse
import redis

class ProxyHandler(BaseHTTPRequestHandler):
    #class attribute, applies to all instances
    URLlist = []

    #init function getting stuff from BaseHTTPRequestHandler Class
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)

    def do_GET(self):
        # Extract the target URL from the request
        DestUrl = self.path[1:]  # Remove leading slash, this is what would b actually used when hooked up to a browser
        DestUrl='http://localhost:8080'
        if DestUrl not in self.URLlist:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            request_body = self.rfile.read(content_length)

            # Forward the GET request to the target URL
            response = self.forward_request(DestUrl, request_body)
            print(f"response: {response}")

            # Send the response status code and headers
            self.send_response(response.status)
            for header, value in response.getheaders():
                self.send_header(header, value)
            self.end_headers()

            # Send the response body
            self.wfile.write(response.read())

            #add to url list
            self.URLlist.append(DestUrl)
            print(f"Cache list: {self.URLlist}\n")
        else:
            request_body = b'1234567890'
            print('\n')
            print("Cached Request")
            content_length = int(self.headers['Content-Length'])
            request_body = self.rfile.read(content_length)
            # Forward the GET request to the target URL
            #response = self.forward_request(DestUrl, request_body)
            #print(f"response: {response}")
            #response.status = 100

            # Send the response status code and headers
            self.send_response(100)
            #for header, value in response.getheaders():
            #for header, value in headers:
            #    self.send_header(header, value)
            #self.end_headers()

            # Send the response body
            self.wfile.write(b'Cached')

    def forward_request(self, url, data):
        # Prepare the new request to be forwarded
        req = urllib.request.Request(url, data=data, headers=self.headers, method='GET')

        # Forward the request and get the response
        response = urllib.request.urlopen(req)
        return response

def run_proxy_server():
    host = 'localhost'
    port = 8000

    # Start the proxy server
    server = HTTPServer((host, port), ProxyHandler)
    print(f'Starting proxy server at {host}:{port}...')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # Handle keyboard interrupt (Ctrl+C) to gracefully shut down the server
        print('\nStopping server...')
        server.shutdown()
        server.server_close()
        print('Server stopped.')

if __name__ == '__main__':
    run_proxy_server()