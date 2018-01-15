#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import MySQLdb
import os
import sleekxmpp
import sys
import time

os.environ['TZ'] = "America/New_York"
time.tzset()

if sys.version_info < (3, 0):
	reload(sys)
	sys.setdefaultencoding('utf8')
else:
	raw_input = input

c2user_list = []
class c2user:
        User = ""
        CachedSchedule = ""
        Zone = 0
        SentIndex = -1
        SentPosture = ""
        SentLunch = -1

def LunchMessage(User):
        u = 0
        for i in range(len(c2user_list)):
                if (c2user_list[i].User == User):
                        u = i; break;

        Lunch = 0
        try:
                Lunch = c2user_list[u].CachedSchedule.index("L")
        except:
                pass

        hour = (Lunch / 2) if (Lunch % 2 == 0) else ((Lunch - 1) / 2)
        hour = (hour + 7) if (c2user_list[u].Zone == 0) else (hour + 5)
        am_pm = " am" if (hour < 12) else " pm"
        hour = (hour - 12) if (hour > 12) else hour
        minute = ":00" if (Lunch % 2 == 0) else ":30"
        time_zone = " EST" if (c2user_list[u].Zone == 0) else " MST"

        str_response = "Your **LUNCH** is at " + str(hour) + minute + am_pm + time_zone
        return str_response

class C2Bot(sleekxmpp.ClientXMPP):
	def __init__(me, jid, password):
		sleekxmpp.ClientXMPP.__init__(me, jid, password)
		me.add_event_handler("session_start", me.start)
		me.add_event_handler("message", me.OnMessage)

	def start(me, event):
		me.send_presence()
		me.get_roster()

	def SendMessage(me, To, Message):
		me.send_message(mto=To + "@example.com",
			mbody=Message, mtype='chat')

	def OnMessage(me, Message):
		if (Message['type'] in ('normal', 'chat')):
			sender = str(Message['from'])
			n = sender.index("@")
			sender_user = sender[0:n]
			command = Message['body'].lower()

			if ("c2bot help" in command):
				Message.reply("\nClarity2 Bot Command List\n"
				+ "Usage: c2bot <command>\n"
				+ "help -  Display the list of c2bot commands\n"
				+ "lunch - Find out when your lunch is scheduled").send()
			elif ("c2bot lunch" in command):
				Message.reply(LunchMessage(sender_user)).send()

def CacheUser(User, Zone, Schedule):
	for i in range(len(c2user_list)):
		if (c2user_list[i].User == User):
			c2user_list[i].CachedSchedule = Schedule
			c2user_list[i].Zone = Zone
			return

	u = c2user()
	u.User = User
	u.CachedSchedule = Schedule
	u.Zone = Zone
	u.SentIndex = -1
	u.SentPosture = ""
	u.SentLunch = -1
        c2user_list.append(u)

def c2sent(User, Index, Posture):
	for i in range(len(c2user_list)):
		if (c2user_list[i].User == User and c2user_list[i].SentIndex == Index):
			if (c2user_list[i].SentPosture == Posture):
				return True
			else:
				c2user_list[i].SentPosture = Posture
				return False
		elif (c2user_list[i].User == User):
			c2user_list[i].SentIndex = Index
			c2user_list[i].SentPosture = Posture
			return False

	u = c2user()
	u.User = User
        u.CachedSchedule = Schedule
        u.Zone = Zone
	u.SentIndex = Index
	u.SentPosture = Posture
	u.SentLunch = -1
	c2user_list.append(u)

	return False

def c2sentLunch(User, Lunch):
	for i in range(len(c2user_list)):
		if (c2user_list[i].User == User and c2user_list[i].SentLunch == Lunch):
			return True
		elif (c2user_list[i].User == User):
			c2user_list[i].SentLunch = Lunch
			return False

	u = c2user()
	u.User = User
        u.CachedSchedule = Schedule
        u.Zone = Zone
	u.SentIndex = -1
	u.SentPosture = ""
	u.SentLunch = Lunch
	c2user_list.append(u)

	return False

def c2chat(c2, User, Schedule):
	hour = int(time.strftime('%H'))
	hour = (hour + 24) if (hour >= 0 and hour < 7) else hour
	hour -= 7

	minute = int(time.strftime('%M'))
	n = 1 if (minute >= 30) else 0
	
	index = ((hour * 2) + n);

	p = Schedule[index : (index + 1)]
	prev_p = Schedule[(index - 1) : index]

	if (p != prev_p and c2sent(User, index, p) == False):
		if (p == "." and prev_p != "."): p = prev_p;

		ext = "posture";
		if (p == "P"): ext = "posture1"
                elif (p == "C"): ext = "posture2"

		c2.SendMessage(User, "Hello, "+User+". I am a bot. <Your posture has "
			+ "been updated or has changed> Your new posture is: "+ext
			+ ". Type >> c2bot help << for a list of my commands.")

	Lunch = -1
	try:
		Lunch = Schedule.index("L")
	except:
		pass

	if (index == (Lunch - 1) and c2sentLunch(User, Lunch) == False):
		c2.SendMessage(User, "Hello, "+User+". I am a bot. "
			+ LunchMessage(User)
			+ ". If you are in a live contact posture, you "
			+ "should message the floor lead 15 minutes before "
			+ "then to let them know.")

if __name__ == '__main__':
	db_conn = MySQLdb.connect(host='localhost', user='db_user',
        	passwd='db_password', db='database')
	cur = db_conn.cursor()

	c2 = C2Bot("example@example.com", "password")
	c2.register_plugin('xep_0030')
	c2.register_plugin('xep_0199')
	c2.connect()
	c2.process(block=False)

	while 1:
		n = int(time.strftime('%H'))
		n = (n + 24) if (n >= 0 and n < 7) else n
	
		sheet = ""
		if (n >= 24):
			d = datetime.date.fromordinal(datetime.date.
				today().toordinal() - 1)
			sheet += str(d.month) + "." + str(d.day) + "." + str(d.year)
		else:
			d = datetime.date.today()
			sheet += str(d.month) + "." + str(d.day) + "." + str(d.year)
		
		cur.execute("DELETE FROM schedules WHERE ID<>'"+sheet+"' OR ID IS NULL")
		cur.execute("SELECT * FROM schedules WHERE ID='"+sheet+"'")

		for ID, User, Zone, Schedule in cur.fetchall():
			CacheUser(User, Zone, Schedule)
			c2chat(c2, User, Schedule)
			time.sleep(2)

	db_conn.close()
