import threading
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import tornadoredis
import tornado.gen
import redis
import json
import socket
import time
import datetime
import random
import uuid
from collections import OrderedDict 

#dem variables
# redis
c = tornadoredis.Client()
c.connect()

r = redis.StrictRedis()

strims = {}
clients = {}
ping_every = 15

def apiDump():
	counts = strimCounts()
	totalviewers = 0
	for strim in counts:
		totalviewers = totalviewers + counts[strim]
	sorted_counts = OrderedDict(sorted(counts.items(), key=lambda t: t[1]))
	return {"streams":sorted_counts, "totalviewers":totalviewers,"totalclients":numClients()}

def strimCounts():
	def num(s):
		try:
			return int(s)
		except ValueError:
			return float(s)
	strims = r.hgetall('strims') or []
	counts = {}
	for strim in strims:
		counts[strim] = num(strims[strim])
	return counts

def numClients():
	return r.hlen('clients')

#takes care of updating console
def printStatus():
	trd = threading.Timer(8, printStatus)
	trd.daemon = True # lets us use Ctrl+C to kill python's threads
	trd.start()
	print str(numClients()), 'clients connected right now'
	sweepClients()
	sweepStreams()
	strim_counts = strimCounts()
	# print len(strim_counts), "unique strims"
	for key, value in strim_counts.items():
		print key, value

def sweepClients():
	global ping_every
	clients = r.hgetall('clients')
	if isinstance(clients, int):
		print 'got', clients, 'instead of actual clients'
		return
	to_remove = []
	expire_time = (time.time()-(3*ping_every))
	for client_id in clients:
		# client = clients[client_id]
		lpt = r.hget('last_pong_time', client_id)
		# print lpt, expire_time
		if (((lpt == '') or (lpt == None)) or (float(lpt) < expire_time)):
			# if(("last_pong_time" in client) and (client["last_pong_time"] < (t_now-(5*ping_every)))):
			to_remove.append(client_id)
	for client_id in to_remove:
		print "removing", client_id
		# don't call remove_viewer because it's async and causes a race condition
		# with the sync code
		# decrement the appropriate stream, unless there isn't one
		if clients[client_id] != "" and clients[client_id] != None:
			# TODO: switch to hash len
			new_count = r.hincrby('strims', clients[client_id], -1)
			if new_count <= 0:
				r.hdel('strims', clients[client_id])
		print 'done removing', client_id
	if len(to_remove) > 0:
		lpts_removed = r.hdel('last_pong_time', *to_remove)
		clients_removed = r.hdel('clients', *to_remove)
		print 'done removing all', lpts_removed, 'out of', len(to_remove), 'last_pong_time entries', clients_removed, 'out of', len(to_remove), 'clients', to_remove

#remove the dict key if nobody is watching DaFeels
def sweepStreams():
	try:
		strims = r.hgetall('strims')
	except Exception, e:
		print 'ERROR: Failed to get all strims from redis in order to sweep'
		print e
		return
	if isinstance(strims, int):
		print 'got', strims, 'instead of actual strims'
		return
	to_remove = []
	for strim in strims:
		print strim, strims[strim]
		if(strims[strim] <= 0):
			print "queueing removal of", strim
			to_remove.append(strim)
	if(len(to_remove) > 0):
		print "going to remove these:", to_remove
		num_deleted = r.hdel('strims', to_remove)
		print "deleted this many strims:", str(num_deleted), "should have deleted this many: ", str(len(to_remove)) 

#ayy lmao
#if self.is_enlightened_by(self.intelligence):
#	self.is_euphoric = True

#Stat tracking websocket server
#Hiring PHP developers does not contribute to the quota of employees with disabilities.
class WSHandler(tornado.websocket.WebSocketHandler):

	def __init__(self, application, request, **kwargs):
		tornado.websocket.WebSocketHandler.__init__(self, application, request, **kwargs)
		self.client = tornadoredis.Client()
		self.client.connect()
		self.io_loop = tornado.ioloop.IOLoop.instance()

	def check_origin(self, origin):
		return True

	@tornado.gen.engine
	def open(self):
		global clients
		self.id = str(uuid.uuid4())
		print 'Opened Websocket connection: (' + self.request.remote_ip + ') ' + socket.getfqdn(self.request.remote_ip) + " id: " + self.id
		clients[self.id] = {'id': self.id}
		lpt_set_or_updated = yield tornado.gen.Task(self.client.hset, 'last_pong_time', self.id, time.time())
		if lpt_set_or_updated == 1:
			print "redis:", lpt_set_or_updated, "creating last_pong_time on open with:", self.id
		else:
			print "redis:", lpt_set_or_updated, "WARN: updating last_pong_time on open with:", self.id, lpt_set_or_updated
		client_set_or_updated = yield tornado.gen.Task(self.client.hset, 'clients', self.id, 'connecting')
		if client_set_or_updated == 1:
			print "redis:", client_set_or_updated, "creating new client id: ", self.id
		else:
			print "redis:", client_set_or_updated, "WARN: updating old client id: ", self.id
		len_clients = yield tornado.gen.Task(self.client.hlen, 'clients')
		print 'len_clients is', len_clients
		# Ping to make sure the agent is alive.
		self.io_loop.add_timeout(datetime.timedelta(seconds=(ping_every/3)), self.send_ping)
	
	@tornado.gen.engine
	def on_connection_timeout(self):
		print "-- Client timed out due to PINGs without PONGs"
		# this might be redundant and redundant
		# don't ping them pointlessly
		self.remove_viewer()
		self.close()

	@tornado.gen.engine
	def send_ping(self):
		in_clients = yield tornado.gen.Task(c.hexists, 'clients', self.id)
		if in_clients:
			print "<- [PING]", self.id
			try:
				self.ping(self.id)
				# global ping_every
				self.ping_timeout = self.io_loop.add_timeout(datetime.timedelta(seconds=ping_every), self.on_connection_timeout)
			except Exception as ex:
				print "-- ERROR: Failed to send ping!", "to: "+ self.id + " because of " + repr(ex)
				self.on_connection_timeout()
		
	@tornado.gen.engine
	def on_pong(self, data):
		# We received a pong, remove the timeout so that we don't
		# kill the connection.
		print "-> [PONG]", data

		if hasattr(self, "ping_timeout"):
			self.io_loop.remove_timeout(self.ping_timeout)

		in_clients = yield tornado.gen.Task(c.hexists, 'clients', self.id)
		if in_clients:
			created_or_updated = yield tornado.gen.Task(c.hset, 'last_pong_time', self.id, time.time())
			if created_or_updated != 0:
				# 0 means the field was updated
				print "redis:", created_or_updated, "creating last_pong_time on_pong is messed up with:", self.id
			# Wait some seconds before pinging again.
			global ping_every
			self.io_loop.add_timeout(datetime.timedelta(seconds=ping_every), self.send_ping)

	@tornado.gen.engine
	def on_message(self, message):
		global strims
		global numClients
		global clients
		fromClient = json.loads(message)
		action = fromClient[u'action']
		strim = fromClient[u'strim']

		if strim == "/destinychat?s=strims&stream=":
			strim = "/destinychat"

		#handle session counting - This is a fucking mess :^(
		if action == "join":
			created_or_updated_client = yield tornado.gen.Task(self.client.hset, 'clients', self.id, strim)
			if created_or_updated_client != 1:
				# 1 means the already existing key was updated, 0 means it was created
				print "joining strim is messed up with:", self.id, created_or_updated_client
			# TODO: switch to hash len count
			strim_count = yield tornado.gen.Task(self.client.hincrby, 'strims', strim, 1)
			self.write_message(str(strim_count) + " OverRustle.com Viewers")
			print 'User Connected: Watching %s' % (strim)

		elif action == "viewerCount":
			try:
				strim_count = yield tornado.gen.Task(self.client.hget, 'strims', strim)			
			except Exception, e:
				print "ERROR: (with " +strim+ ") failed to get the viewer count for this strim"
				print e
			else:
				self.write_message(str(strim_count) + " OverRustle.com Viewers")

		elif action == "api":
			self.write_message(json.dumps(apiDump()))

		else:
			print 'WTF: Client sent unknown command >:( %s' % (action)

	@tornado.gen.engine
	def on_close(self):
		print 'Closed Websocket connection: (' + self.request.remote_ip + ') ' + socket.getfqdn(self.request.remote_ip)+ " id: "+self.id
				# don't ping them pointlessly
		self.remove_viewer()

	@tornado.gen.engine
	def remove_viewer(self):
		if hasattr(self, "ping_timeout"):
			self.io_loop.remove_timeout(self.ping_timeout)
		global c
		v_id = self.id
		in_clients = yield tornado.gen.Task(c.hexists, 'clients', v_id)
		if in_clients:
			strim = yield tornado.gen.Task(c.hget, 'clients', v_id)
			#####
			# if strim lists get ugly and problematic, 
			# have this just send a message to the .sync client 
			# and queue a sweep
			if strim != '':
				# TODO: switch to hash with len
				new_count = yield tornado.gen.Task(c.hincrby, 'strims', strim, -1)
				if new_count <= 0:
					num_deleted = yield tornado.gen.Task(c.hdel, 'strims', strim)
					if num_deleted == 0:
						print "deleting this strim counter did not work : ", strim 
			else:
				print 'deleting a client that was not tied to a strim:', v_id
			#####
			clients_deleted = yield tornado.gen.Task(c.hdel, 'clients', v_id)
		pong_times_deleted = yield tornado.gen.Task(c.hdel, 'last_pong_time', v_id)
		if pong_times_deleted == 0:
			print "redis:", pong_times_deleted, v_id, "deleting this pong tracker was redundant"
		print str(numClients()) + " viewers remain connected"

#print console updates
printStatus()

#JSON api server
class APIHandler(tornado.web.RequestHandler):
		def get(self):
				self.write(json.dumps(apiDump()))

#GET address handlers
application = tornado.web.Application([
		(r'/ws', WSHandler),
		(r'/api', APIHandler)
])
 
#starts the server on port 9998
if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(9998)
	tornado.ioloop.IOLoop.instance().start()
