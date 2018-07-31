============  ASSIGNMENT 2 ==============

server/server.py has the main server running.
proxy.py has the proxy server running.

server needs to be run 10000 port
python2 server.py 10000

proxy server runs on 20000 port
python2 proxy.py 20000

NO_OCC_OF_CACHE is 2 which means that the cache
will store on 2nd request onwards, which means in
the 1st request, the proxy will respond without
caching.

Comments are provided above every function and
the parser function has been explained in
comments.

Open the browser and type localhost:20000/$i.(txt/data)
i ranges from 1 to 9.

Example:

-> localhost:20000/1.txt
    1.txt is responded without caching
-> localhost:20000/1.txt
    1.txt is responded with caching

    CACHE: 1.txt
-> localhost:20000/2.txt
    2.txt is responded without caching
-> localhost:20000/3.txt
    3.txt is responded without caching

    CACHE: 1.txt
-> localhost:20000/4.txt
    4.txt is responded without caching
-> localhost:20000/2.txt
    2.txt is responded with caching

    CACHE: 1.txt 2.txt
-> localhost:20000/4.txt
    4.txt is responded with caching

    CACHE: 1.txt 2.txt 4.txt
-> localhost:20000/1.txt
    1.txt is responded from cache
-> localhost:20000/3.txt
    3.txt is responded with caching

    CACHE: 1.txt 3.txt 4.txt

    2.txt being oldest referenced in the cache
    is deleted. Hence, every file is cached
    on its second(MAX_OCC_OF_CACHE) reference.


