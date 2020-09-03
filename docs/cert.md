# Renew certificate

1. Stop the server

2. Start a temporal simple http server

    $ sudo python -m http.server 80

3. Execute the command:

    $ certbot renew

4. Stop the temporal simple http server

5. Restart the server

    $ sudo python index.py -s -p 443
