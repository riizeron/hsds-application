import h5pyd
import json
import os
from datetime import datetime
import logging

from h5pyd._apps.hsinfo import getUpTime, getHomeFolder


class Session:
    def __init__(self):
        self.server_endpoint = None
        self.username = None
        self.password = None
        self.api_key = ""
        self.home_dir = None
 
    def pingServer(self):
        message = None
        if self.server_endpoint is None:
            print("empty endpoint")
            message = "empty endpoint!"
            return False, message
        if not self.server_endpoint.startswith("http"):
            print("endpoint must start with 'http...'")
            message = "endpoint must start with 'http...'"
            return False, message

        try:
            info = h5pyd.getServerInfo(username=self.username, password=self.password, endpoint=self.server_endpoint,
                                       api_key=self.api_key)
            if 'state' not in info:
                print("unexpected response from server")
                message = "unexpected response from server"
                return False, message
            state = info["state"]
            if state != "READY":
                print("Server is not ready, please try later")
                message = "Server is not ready, please try later"
                return False, message
        except IOError as ioe:
            if ioe.errno == 401:
                print("Unauthorized (username/password or api key not valid)")
                message = "Unauthorized (username/password or api key not valid)"
                return False, message
            elif ioe.errno == 403:
                print("forbidden (account not setup?)")
                message = "forbidden (account not setup?)"
                return False, message
            elif ioe.errno:
                print("Unexpected error: {}".format(ioe.errno))
                message = "Unexpected error: {}".format(ioe.errno)
                return False, message
            else:
                print("Couldn't connect to server")
                message = "Couldn't connect to server"
                return False, message
        except json.decoder.JSONDecodeError:
            print("Unexpected response from server")
            message = "Unexpected response from server"
            return False, message
        message = ""
        return True, message

    def getServerInfo(self):
        """ get server state and print """
        message = ""
        try:
            print(f'username:{self.username},password:{self.password},endpoint:{self.server_endpoint}')
            info = h5pyd.getServerInfo(username=self.username, password=self.password, endpoint=self.server_endpoint)
            print("server name: {}".format(info["name"]))
            message += "server name: {}".format(info["name"]) + os.linesep
            if "state" in info:
                print("server state: {}".format(info['state']))
                message += "server state: {}".format(info['state']) + os.linesep
            print("endpoint: {}".format(self.server_endpoint))
            message += "endpoint: {}".format(self.server_endpoint) + os.linesep
            if "isadmin" in info and info["isadmin"]:
                admin_tag = "(admin)"
            else:
                admin_tag = ""
            print("username: {} {}".format(info["username"], admin_tag))

            self.username = info["username"]
            self.password = info["password"]
            
            message += "username: {} {}".format(info["username"], admin_tag) + os.linesep
            print("password: {}".format(info["password"]))
            message += "password: {}".format(info["password"]) + os.linesep
            if info['state'] == "READY":
                try:
                    home_folder = self.getHomeFolder()
                    if home_folder:
                        print("home: {}".format(home_folder))
                        message += "home: {}".format(home_folder) + os.linesep
                        self.home_dir = home_folder
                except IOError:
                    print("home: NO ACCESS", )
                    message += "home: NO ACCESS" + os.linesep + os.linesep

            if "hsds_version" in info:
                print("server version: {}".format(info["hsds_version"]))
                message += "server version: {}".format(info["hsds_version"]) + os.linesep
            if "node_count" in info:
                print("node count: {}".format(info["node_count"]))
                message += "node count: {}".format(info["node_count"]) + os.linesep
            elif "h5serv_version" in info:
                print("server version: {}".format(info["h5serv_version"]))
                message += "server version: {}".format(info["h5serv_version"]) + os.linesep
            if "start_time" in info:
                uptime = getUpTime(info["start_time"])
                print("up: {}".format(uptime))
                message += "up: {}".format(uptime) + os.linesep
            print("h5pyd version: {}".format(h5pyd.version.version))
            message += "h5pyd version: {}".format(h5pyd.version.version) + os.linesep

        except IOError as ioe:
            if ioe.errno == 401:
                if self.username and self.password:
                    print("username/password not valid for username: {}".format(self.username))
                    message += "username/password not valid for username: {}".format(self.username) + os.linesep
                else:
                    # authentication error with openid or app token
                    print("authentication failure")
                    message += "authentication failure" + os.linesep
            else:
                print("Error: {}".format(ioe))
                message += "Error: {}".format(ioe) + os.linesep

        return message

    def getDomain(self, domain = None):
        if domain is None:
            domain = self.home_dir
            try:
                home_folder = self.getFolder(domain)
                return True, home_folder
            except Exception:
                return False, None

        try:
            folder = self.getFolder(domain + '/')
            if folder.is_folder:
                return True, folder
            else:
                file = self.getFile(domain)
                return True, file
        except Exception:
            return False, None


    def getHomeFolder(self):    
        dir = self.getFolder('/home/')  # get folder object for root
        
        homefolder = '/'
        for name in dir:
        # we should come across the given domain
            if self.username.startswith(name):
                # check any folders where the name matches at least part of the username
                # e.g. folder: "/home/bob/" for username "bob@acme.com"
                path = '/home/' + name + '/'
                try:
                    f = h5pyd.Folder(path, username=self.username, password=self.password, endpoint=self.server_endpoint)
                except IOError as ioe:
                    logging.info("find home folder - got ioe: {}".format(ioe))
                    continue
                except Exception as e:
                    logging.warn("find home folder - got exception: {}".format(e))
                    continue
                if f.owner == self.username:
                    homefolder = path
                f.close()
                if homefolder:
                    break

        dir.close()
        return homefolder

    def getFolder(self, domain):
        username = self.username # cfg["hs_username"]
        password = self.password # cfg["hs_password"]
        endpoint = self.server_endpoint # cfg["hs_endpoint"]
        # bucket   = cfg["hs_bucket"]
        # pattern = cfg["pattern"]
        # query = cfg["query"]
        # if cfg["verbose"]:
        #     verbose = True
        # else:
        #     verbose = False
        batch_size = 100  # use smaller batchsize for interactively listing of large collections
        d = h5pyd.Folder(domain, endpoint=endpoint, username=username, #verbose=verbose,
                        password=password)#, bucket=bucket, pattern=pattern, query=query, batch_size=batch_size)
        return d
    
    def getFile(self, domain):
        username = self.username # cfg["hs_username"]
        password = self.password # cfg["hs_password"]
        endpoint = self.server_endpoint # cfg["hs_endpoint"]
        # username = cfg["hs_username"]
        # password = cfg["hs_password"]
        # endpoint = cfg["hs_endpoint"]
        # bucket = cfg["hs_bucket"]
        fh = h5pyd.File(domain, mode='r', endpoint=endpoint, username=username,
                    password=password, use_cache=True)#, bucket=buket)
        return fh

