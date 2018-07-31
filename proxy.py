import copy
import thread
import socket
import sys
import os
import datetime
import time
import json
import threading
import email.utils as eut

# global variables
max_connections = 10
BUFFER_SIZE = 4096
CACHE_DIR = "./cache"
MAX_CACHE_BUFFER = 3
NO_OF_OCC_FOR_CACHE = 2
logs = {}
locks = {}

# take command line argument
if len(sys.argv) != 2:
    print "Usage: python %s <PROXY_PORT>" % sys.argv[0]
    print "Example: python %s 20000" % sys.argv[0]
    raise SystemExit

try:
    proxy_port = int(sys.argv[1])
except:
    print "provide proper port number"
    raise SystemExit

if not os.path.isdir(CACHE_DIR):
    os.makedirs(CACHE_DIR)


for file in os.listdir(CACHE_DIR):
    os.remove(CACHE_DIR + "/" + file)


# lock fileurl
def lock_access(fileurl):
    if fileurl in locks:
        lock = locks[fileurl]
    else:
        lock = threading.Lock()
        locks[fileurl] = lock
    lock.acquire()

# unlock fileurl
def leave_lock(fileurl):
    if fileurl in locks:
        lock = locks[fileurl]
        lock.release()
    else:
        print "Lock problem"
        sys.exit()


# add fileurl entry to log
def add_log(fileurl, client_addr):
    fileurl = fileurl.replace("/", "__")
    if not fileurl in logs:
        logs[fileurl] = []
    dt = time.gmtime()
    logs[fileurl].append({
            "datetime" : dt,
            "client" : json.dumps(client_addr),
        })
#    print logs

# decide whether to cache or not
def do_cache_or_not(fileurl):
    try:
        log_arr = logs[fileurl.replace("/", "__")]
        if len(log_arr) < NO_OF_OCC_FOR_CACHE : return False
        last_third = log_arr[len(log_arr)-NO_OF_OCC_FOR_CACHE]["datetime"]
        #print "\n\n", datetime.datetime.fromtimestamp(time.mktime(last_third)) + datetime.timedelta(minutes=10), "\n\nfgfbf\n\n", datetime.datetime.utcnow(), "\n"
        
        # After 10 mins, the server will cache irrespective of modified or not
        if datetime.datetime.fromtimestamp(time.mktime(last_third)) + datetime.timedelta(minutes=10) >= datetime.datetime.utcnow():
            return True
        else:
            return False
    except Exception as e:
        print e
        return False

# check whether file is already cached or not
def get_current_cache_info(fileurl):

    if fileurl.startswith("/"):
        fileurl = fileurl.replace("/", "", 1)

    cache_path = CACHE_DIR + "/" + fileurl.replace("/", "__")

    if os.path.isfile(cache_path):
        last_mtime = time.gmtime(os.path.getmtime(cache_path))
        return cache_path, last_mtime
    else:
        return cache_path, None


# collect all cache info
def get_cache_details(client_addr, details):
    lock_access(details["total_url"])
    add_log(details["total_url"], client_addr)
    do_cache = do_cache_or_not(details["total_url"])
    cache_path, last_mtime = get_current_cache_info(details["total_url"])
    leave_lock(details["total_url"])
    details["do_cache"] = do_cache
    details["cache_path"] = cache_path
    details["last_mtime"] = last_mtime
    return details


# if cache is full then delete the least recently used cache item
def get_space_for_cache(fileurl):
    cache_files = os.listdir(CACHE_DIR)
    if len(cache_files) < MAX_CACHE_BUFFER:
        return

    for file in cache_files:
    	filepath = "/"+file
        lock_access(filepath)

    # for file in cache_files:
    # 	print logs["__"+file][-1]["datetime"]

    last_mtime = min(logs["__"+file][-1]["datetime"] for file in cache_files)
    #print "\n\n", last_mtime, " :tobedeleted\n\n"
    
    # the file which has been added least recently in the cache will be deleted
    file_to_del = [file for file in cache_files if logs["__"+file][-1]["datetime"] == last_mtime][0]

    os.remove(CACHE_DIR + "/" + file_to_del)
    for file in cache_files:
    	filepath = "/"+file
        leave_lock(filepath)
        


# returns a dictionary of details
# http://5.txt/
def parse_details(client_addr, client_data):
    try:
        # parse first line like below
        # http:://127.0.0.1:20020/1.data

        lines = client_data.splitlines()
        # divide the header into line

        while lines[len(lines)-1] == '':
            lines.remove('')
        # removes all the null lines from the end

        first_line_tokens = lines[0].split()
        # GET /1.data HTTP/1.1 => "GET", "/1.data", "HTTP/1.1"

        url = first_line_tokens[1]
        # url = "/1.data"

        # get starting index of IP
        url_pos = url.find("://")
        if url_pos != -1:   # for requests of type "http://server/1.data"
            protocol = url[:url_pos]
            url = url[(url_pos+3):]
        else:				# for requests of type "/1.data"
            protocol = "http"

        # get port if any
        # get url path
        port_pos = url.find(":")   # server:'portnum/1.data'
        path_pos = url.find("/")   # server:portnum/'1.data'
        if path_pos == -1:
            path_pos = len(url)


        # change request path accordingly
        if port_pos==-1 or path_pos < port_pos:
            server_port = 10000
            server_url = url[:path_pos] #server
        else:
            server_port = int(url[(port_pos+1):path_pos]) #portnum
            server_url = url[:port_pos] #server


        # build up request for server
        first_line_tokens[1] = url[path_pos:]
        #print "\n\nsfkknbkf\n\n", first_line_tokens, "\n\nfbdfb\n\n"
        lines[0] = ' '.join(first_line_tokens)
        #print lines, "\n\n"
        client_data = "\r\n".join(lines) + '\r\n\r\n'
        #print client_data, "\n\n"

        print "\n\n",server_url, url, "\n\n"

        return {
            "server_port" : server_port,
            "server_url" : server_url,
            "total_url" : url,
            "client_data" : client_data,
            "protocol" : protocol,
            "method" : first_line_tokens[0],
        }

    except Exception as e:
        print e
        print
        return None



# insert the header
def insert_if_modified(details):

    lines = details["client_data"].splitlines()
    while lines[len(lines)-1] == '':
        lines.remove('')

    #header = "If-Modified-Since: " + time.strptime("%a %b %d %H:%M:%S %Y", details["last_mtime"])
    header = time.strftime("%a %b %d %H:%M:%S %Y", details["last_mtime"])
    header = "If-Modified-Since: " + header
    lines.append(header)

    details["client_data"] = "\r\n".join(lines) + "\r\n\r\n"
    return details


# serve get request
def serve_get(client_socket, client_addr, details):
    try:
        client_data = details["client_data"]
        print "\n\nClient Data: \n\n", client_data, "\n\n"
        do_cache = details["do_cache"]
        cache_path = details["cache_path"]
        print "\n\nCache_path: ", cache_path, "\n\n"
        last_mtime = details["last_mtime"]

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.connect((details["server_url"], details["server_port"]))
        server_socket.send(details["client_data"])

        reply = server_socket.recv(BUFFER_SIZE)
        print "\n\nReply: ", reply, "\n\n"
        if last_mtime and "304 Not Modified" in reply:
            print "returning cached file %s to %s" % (cache_path, str(client_addr))
            # lock_access(details["total_url"])
            f = open(cache_path, 'rb')
            chunk = f.read(BUFFER_SIZE)
            while chunk:
                client_socket.send(chunk)
                chunk = f.read(BUFFER_SIZE)
            f.close()
            # leave_lock(details["total_url"])

        else:
            if do_cache:
                print "caching file while serving %s to %s" % (cache_path, str(client_addr))
                get_space_for_cache(details["total_url"])
                lock_access(details["total_url"])
                f = open(cache_path, "w+")
                # print len(reply), reply
                while len(reply):
                    client_socket.send(reply)
                    f.write(reply)
                    reply = server_socket.recv(BUFFER_SIZE)
                    #print len(reply), reply
                f.close()
                leave_lock(details["total_url"])
                client_socket.send("\r\n\r\n")
            else:
                print "without caching serving %s to %s" % (cache_path, str(client_addr))
                #print len(reply), reply
                while len(reply):
                    client_socket.send(reply)
                    reply = server_socket.recv(BUFFER_SIZE)
                    #print len(reply), reply
                client_socket.send("\r\n\r\n")

        server_socket.close()
        client_socket.close()
        return

    except Exception as e:
        server_socket.close()
        client_socket.close()
        #print e
        return



# A thread function to handle one request
def handle_one_request_(client_socket, client_addr, client_data):
 #   print client_addr, "\n\ndvsfvfb\n\n", client_data
    details = parse_details(client_addr, client_data)

    #print "\nsddff\n", details, "\nsdfgfg\n"
    if not details:
        print "no details"
        client_socket.close()
        return

    if details["method"] == "GET":
        details = get_cache_details(client_addr, details)
        if details["last_mtime"]:
            details = insert_if_modified(details)
        serve_get(client_socket, client_addr, details)

#    client_socket.close()
    print client_addr, "closed\n\n"




# This funciton initializes socket and starts listening.
# When connection request is made, a new thread is created to serve the request
def start_proxy_server():

    # Initialize socket
    try:
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy_socket.bind(('', proxy_port))
        proxy_socket.listen(max_connections)

        print "Serving proxy on %s port %s ..." % (
            str(proxy_socket.getsockname()[0]),
            str(proxy_socket.getsockname()[1])
            )

    except Exception as e:
        print "Error in starting proxy server ..."
        print e
        proxy_socket.close()
        raise SystemExit


    # Main server loop
    while True:
        try:
            client_socket, client_addr = proxy_socket.accept()
            client_data = client_socket.recv(BUFFER_SIZE)

            print
            print "%s - - [%s] \"%s\"" % (
                str(client_addr),
                str(datetime.datetime.utcnow()),
                client_data.splitlines()[0]
                )

            thread.start_new_thread(
                handle_one_request_,
                (
                    client_socket,
                    client_addr,
                    client_data
                )
            )

        except KeyboardInterrupt:
            client_socket.close()
            proxy_socket.close()
            print "\nProxy server shutting down ..."
            break



start_proxy_server()
