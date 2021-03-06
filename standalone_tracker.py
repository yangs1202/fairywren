import eventlet
eventlet.monkey_patch()
import eventlet.backdoor
from eventlet import wsgi
from tracker import Tracker
from auth import *
from peers import *

import swarm
import vanilla
import psycopg2
import sys
import json
import logging.config
DEFAULT_LISTEN_IP ='127.0.0.1'
DEFAULT_LISTEN_PORT = 8080
DEFAULT_PATH_DEPTH = 1

if __name__ == '__main__':
	with open(sys.argv[1],'r') as fin:
		conf = json.load(fin)
	
	if 'logging' in conf['tracker']:	
		logging.config.dictConfig(conf['tracker']['logging'])
	
	authmgr = Auth(conf['salt'])
	connPool = vanilla.buildConnectionPool(psycopg2,**conf['tracker']['postgresql'])
	authmgr.setConnectionPool(connPool)
	
	httpListenIp = conf['tracker'].get('ip',DEFAULT_LISTEN_IP)
	httpListenPort = conf['tracker'].get('port',DEFAULT_LISTEN_PORT)
	httpPathDepth = conf.get('pathDepth',DEFAULT_PATH_DEPTH)
	
	#Use a six hour period for flushing expired peers
	redisConnPool = vanilla.buildRedisConnectionPool(**conf['redis'])
	peerList = Peers(redisConnPool,60*60*6)
	tracker = Tracker(authmgr,peerList,httpPathDepth)
	
	swarmConnPool = vanilla.buildConnectionPool(psycopg2,**conf['tracker']['postgresql'])
	swarm = swarm.Swarm()
	swarm.setConnectionPool(swarmConnPool)
	eventlet.spawn_n(swarm)
	
	tracker.addAfterAnnounce(swarm.pushPeer)
	
	eventlet.spawn_n(peerList)
	wsgi.server(eventlet.listen((httpListenIp, httpListenPort)), tracker)
