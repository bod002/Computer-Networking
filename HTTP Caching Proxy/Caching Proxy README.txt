This program is a proxy that will receive an http GET message from a server and then will forward the http GET message to
the client if the message URL is not already in the proxy's cache. The http_recv is a client and http_send is a server.
Since the http_recv is only set up on one location sending the same thing it can only be contacted by a http GET once before
the http proxy blocks the connection. If the http_server was receiving http messages from different URLs on a browser it could
continuously pull new data without wasting time on already retrieved http messages. The requests and http.server api were
used in http_proxy.py as well as in the sender and receiver programs. These programs were co-authored by chatGPT.

Limitations:
- does not operate with POST messages
- does not Handle cache invalidation
- no Error handling for network failures, invalid requests, or server errors