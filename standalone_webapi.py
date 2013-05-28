import eventlet
eventlet.monkey_patch()
import eventlet.backdoor
from eventlet import wsgi

from webapi import Webapi
from auth import *
from torrents import TorrentStore

import vanilla
import psycopg2
import sys
import json

if __name__ == '__main__':
	with open(sys.argv[1],'r') as fin:
		conf = json.load(fin)
		
		connPool = vanilla.buildConnectionPool(psycopg2,**conf['webapi']['postgresql'])
		
		authmgr = Auth(conf['salt'])
		authmgr.setConnectionPool(connPool)
		
		torrents = TorrentStore(conf['webapi']['torrentPath'],conf['trackerUrl'],conf['apiUrl'])
		torrents.setConnectionPool(connPool)
		
	webapi = Webapi(authmgr,torrents,conf['pathDepth'])
	wsgi.server(eventlet.listen(('127.0.0.1', 8081)), webapi)
