import socket
import multiprocessing
import atexit
import os
import datetime
import subprocess

clist = []
addrlist = []
plist = []
response_codes = {
        "200": "HTTP/1.0 200 OK\nServer:kral4 http server\nConnection: close\nContent-Type: text/html\n\n",
        "400": "HTTP/1.0 400 Bad request\nCache-Control: no-cache\nServer:kral4 http server\nConnection: close\nContent-Type: text/html\n\n<html><body><h1>400 Bad request</h1>Your browser sent an invalid request.</body></html>",
        "404": "HTTP/1.0 404 Not Found\nCache-Control: no-cache\nServer:kral4 http server\nConnection: close\nContent-Type: text/html\n\n<html><body><h1>404 Not Found</h1>YThe requested file or directory is not exist</body></html>",
        "500": "HTTP/1.0 500 Internal Server Error\nCache-Control: no-cache\nServer:kral4 http server\nConnection: close\nContent-Type: text/html\n\n<html><body><h1>500 Internal Server Error</h1>Server ran into a problem :(</body></html>",
        "503": "HTTP/1.0 503 Service Unavailable\nCache-Control: no-cache\nServer:kral4 http server\nConnection: close\nContent-Type: text/html\n\n<html><body><h1>503 Service Unavailable</h1>There is a problem with server</body></html>"
    }

def getconfig():
    root_dir   = ""
    enable_php = ""
    php_path   = ""
    with open("config.cfg", "r") as f:
        lines = f.readlines()
    for line in lines:
        if "#" not in line:
            line = line.split(":")
            if line[0] == "root_dir":
                root_dir = line[1].strip()
            elif line[0] == "enable_php":
                enable_php = int(line[1].strip())
            elif line[0] == "php_path":
                php_path = line[1].strip()

    return root_dir, enable_php, php_path

def log(data2log):
    with open("logs.txt", "a") as f:
        f.write(str(datetime.datetime.now()) + ", " + str(data2log) + "\n")

def closesocket(sock):
    sock.shutdown(socket.SHUT_RDWR)
    sock.close()
    log("Socket Closed " + str(sock))

def callphp(filepath):
    last = b""
    config = getconfig()
    result = subprocess.Popen([config[2], "-f", filepath], stdout=subprocess.PIPE)
    out, err = result.communicate()
    return out.decode()

def killthreads():
    global plist
    for p in plist:
        p.terminate()
    log("Server Closed")

def preparefileandrespond(filepath, c):
    global response_codes
    root_dir, enable_php, php_path = getconfig()
    if filepath == "/":
        #if rootdir
        isindexhtml = os.path.isfile(root_dir + "index.html")
        isindexphp  = os.path.isfile(root_dir + "index.php")
        if isindexhtml == True:
            with open(root_dir + "index.html") as f:
                filecontent = f.read()
            finalresponse = response_codes["200"] + filecontent
            c.sendall(finalresponse.encode())
            closesocket(c)
        elif isindexphp == True:
            if enable_php != 1:
                print("enable_php off canceling request")
                c.sendal(response_codes["403"].encode())
                closesocket(c)
            else:
                filecontent = callphp(root_dir + "index.php")
                finalresponse = response_codes["200"] + filecontent
                c.sendall(finalresponse.encode())
                closesocket(c)
        else:
            filecontent = os.listdir(root_dir)
            response_head = "<html><head><title>list of /</title></head><body><h1>Kral4 HTTP Server</h1>"
            response_body = ""
            response_end = "</body></html>"
            for content in filecontent:
                response_body += f"<a href='{content}'>{content}</a>"
            filecontent = response_head + response_body + response_end
            finalresponse = response_codes["200"] + filecontent
            c.sendall(finalresponse.encode())
            closesocket(c)
    else:
        #if not rootdir
        isdir = os.path.isdir(root_dir + filepath)
        isfile = os.path.isfile(root_dir + filepath)
        if isdir == True:
            isindexhtml = os.path.isfile(root_dir + "index.html")
            isindexphp  = os.path.isfile(root_dir + "index.php")
            if isindexhtml == True:
                with open(root_dir + "index.html") as f:
                    filecontent = f.read()
                finalresponse = response_codes["200"] + filecontent
                c.sendall(finalresponse.encode())
                closesocket(c)
            elif isindexphp == True:
                if enable_php != 1:
                    print("enable_php off canceling request")
                    c.sendal(response_codes["403"].encode())
                    closesocket(c)
                else:
                    filecontent = callphp(root_dir + "index.php")
                    finalresponse = response_codes["200"] + filecontent
                    c.sendall(finalresponse.encode())
                    closesocket(c)
            else:
                filecontent = os.listdir(root_dir)
                response_head = "<html><head><title>list of /</title></head><body><h1>Kral4 HTTP Server</h1>"
                response_body = ""
                response_end = "</body></html>"
                for content in filecontent:
                    response_body += f"<a href='{content}'>{content}</a>"
                filecontent = response_head + response_body + response_end
                finalresponse = response_codes["200"] + filecontent
                c.sendall(finalresponse.encode())
                closesocket(c)
        elif isfile == True:
            if "." in filepath:
                fileext = filepath.split(".")
                if fileext[-1] == "php":
                    if enable_php != 1:
                        print("enable_php off canceling request")
                        c.sendall(response_codes["403"].encode())
                        closesocket(c)
                    else:
                        filecontent = callphp(root_dir + filepath)
                        finalresponse = response_codes["200"] + filecontent
                        c.sendall(finalresponse.encode())
                        closesocket(c)
                else:
                    with open(root_dir + filepath, "r") as f:
                        filecontent = f.read()
                    finalresponse = response_codes["200"] + filecontent
                    c.sendall(finalresponse.encode())
                    closesocket(c)
            else:
                with open(root_dir + filepath, "r") as f:
                    filecontent = f.read()
                finalresponse = response_codes["200"] + filecontent
                c.sendall(finalresponse.encode())
                closesocket(c)
        else:
            c.sendall(response_codes["404"].encode())
            closesocket(c)

def processandrespond(c, data):
    global response_codes
    request_method = ""
    request_path   = ""
    http_version   = ""
    user_agent     = ""
    for d in data:
        if b"HTTP" in d:
            httpline = d.decode().split(" ")
            request_method = httpline[0]
            request_path   = httpline[1]
            http_version   = httpline[2]
        elif b"User-Agent" in d:
            useragentline  = d.decode().split("User-Agent:")
            user_agent     = useragentline[1]
    if request_method and request_path and http_version and user_agent != "":
        print(request_method, request_path, http_version, user_agent)
        preparefileandrespond(request_path, c)
    else:
        c.sendall(response_codes['400'].encode())
        closesocket(c)
    log(request_method + " " + request_path + " " + http_version + " " + user_agent + " " + str(c))

def receivefromclient(c):
    global response_codes
    data = c.recv(4096)
    if b"\r\n" in data:
        data = data.split(b"\r\n")
        p = multiprocessing.Process(target=processandrespond, args=(c, data))
        p.start()
        plist.append(p)
    elif b"\r\n" in data:
        data = data.split(b"\n")
        p = multiprocessing.Process(target=processandrespond, args=(c, data))
        p.start()
        plist.append(p)
    else:
        c.sendall(response_codes["400"].encode())
        closesocket(c)

def accept(s):
    global clist
    global addrlist
    global plist
    while True:
        c, addr = s.accept()
        clist.append(c)
        addrlist.append(addr)
        p = multiprocessing.Process(target=receivefromclient, args=(c,))
        p.start()
        plist.append(p)
        log("Connection Accepted " + str(addr) + str(c))


def main():
    global plist
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", 8080))
    s.listen()
    print("listening")
    atexit.register(killthreads)
    p = multiprocessing.Process(target=accept, args=(s,))
    p.start()
    plist.append(p)
    log("Server Started")
    

if __name__ == "__main__":
    main()
    
