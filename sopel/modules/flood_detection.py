#!/usr/bin/env python
"""
flood_detection.py - mutes nicks when flood is detected
Copyright 2016 Marc Schaefer (gposse.de)
Licensed under GPLv3

This module was developped looking how the jenni module banned_words.py does it's job
There're two parts for this module:

1. flood_detection
Flood_detection module based on the flood detection module of cinnabot
The difference is that cinnabot uses the python irc module which offers a irc.execute_delayed method 
used to unmute a user

2. unmute_loop
Creates a loop triggered every loop_rate seconds to check for users that needs to be unmuted


More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
 * Sopel: http://sopel.org/sopel/
"""
from sopel.module import rule, priority, interval, commands, nickname_commands, example 
import imp, os, re, time, threading
from sopel.db import SopelDB

current_warnings = {}
messages_by_source  = {}
last_sent_warning  = {}
quiet_times  = {}
muted_users = {}

def setup(self):
    fn = self.nick + '-' + self.config.core.host + '.flood.db'
    self.flood_filename = os.path.join(self.config.core.homedir, fn)
    if not os.path.exists(self.flood_filename):
        try:
            f = open(self.flood_filename, 'w')
        except OSError:
            pass
        else:
            f.write('')
            f.close()
    #self.memory['tell_lock'] = threading.Lock()
    #self.memory['reminders'] = loadReminders(self.tell_filename, self.memory['tell_lock'])

def mute_user(bot,trigger):
    global muted_users
    
    mute_host = trigger.hostmask.split("@")[1]
    mute_mask = "*!*@%s" % mute_host
    channel= trigger.sender
    nick = trigger.nick
    muted_users[nick] = [channel, nick, mute_mask, time.time(), 30]
    bot.say('Muting %s' % mute_mask)
    bot.write(['MODE',channel, '+b m:%s' % mute_mask])

def unmute_user(bot, mute_mask):
    channel= muted_users[mute_mask][0]
    #bot.say('Unmuting %s' % mute_mask,channel)
    bot.write(['MODE',channel, '-b m:%s' % mute_mask])

@interval(10)
@priority('high')
def unban_loop(bot):
    global muted_users
    unmuted_list = []
    # check if any nicks quiet_time is finished and unmute
    for nick,values in muted_users.items():
        bantime = values[3]
        quiet_time = values[4]
        if (time.time()-bantime > quiet_time):
            mute_mask = values[2]
            channel = values[0]
            bot.say('Unbanloop Unmuting nick %s with hostmask %s' % (nick,mute_mask), channel)            
            unmute_user(bot, mute_mask)
            unmuted_list.append(mute_mask)
    for mask in unmuted_list:
        del(muted_users[mask])
    return

@rule(r'(.*)')
@priority('high')
def flood_detection(bot, trigger):
    """
    Listens to a channel for channel flooding. If one is found it first
    warns a user and mutes him for mute_time seconds, then after  repeat_warnings_limit kickbans them, where
    repeat_warnings defaults to 0, meaning instant ban.

    User warnings are stored only in memory, and as a result
    restarting jenni will eliminate any warnings.

    Currently bad words must be added to the config, as a future
    addition bad words will be editable by admins using a command.
    """
    global current_warnings
    global messages_by_source
    global last_sent_warning
    global quiet_times
    
    nb_messages =  3
    interval =  5
    quiet_time = 30
    debug_mode = True
    
    #bot.reply('Config is %s, %s, %s, %s' % (nb_messages,interval,quiet_time,debug_mode)) 

    # We only want to execute in a channel for which we have a wordlist
#    if not trigger.sender.startswith("#") :
#        return

    # We don't want to warn or kickban admins
    #if trigger.admin:
    #    bot.reply('We don\'t mute admins')
    #    return

    channel = trigger.sender
    source = trigger.nick
    
    chan_ops = []
    chan_hops = []
    chan_voices = []
    if channel in bot.ops:
        chan_ops = bot.ops[channel]

    # First ensure jenni is an op
    #if bot.nick not in chan_ops:
    #    bot.reply('We don\'t mute chanops')
    #    return

    # Next ensure the sender isn't op, half-op, or voice
    bad_nick = trigger.nick
    if bad_nick in chan_ops or bad_nick in chan_hops or bad_nick in chan_voices:
        bot.reply('We don\'t mute halfops')
        return


    # put a timestamp for user and channel
    messages_by_source.setdefault(channel, {}).setdefault(source, []).append(time.time())
    # keep nb_messages posts to be able to check for flooding
    messages_by_source[channel][source] = messages_by_source[channel][source][-int(nb_messages):]
    
    # check if source hits the flooding limits
    if (len(messages_by_source[channel][source]) == int(nb_messages)) and (time.time() - min(messages_by_source[channel][source]) < int(interval)):
        #flooding detected
        if time.time() - last_sent_warning.setdefault(source, 0) > 600:
            # send privmsg to stop behaviour if debug_mode is on
            if debug_mode:
                #jenni.say(bad_word_warning(bad_nick, bad_word_limit, current_warnings[bad_nick]))
                bot.say('Please stop db.set_nick_valueflooding')
        if not source in quiet_times:
            quiet_times[source] = int(quiet_time)
            if debug_mode:
                bot.say('You\'ll be muted')
            #bot.db.set_nick_value(trigger.nick,'startbantime', time.time())
            mute_user(bot,trigger)
        else:
            quiet_times[source] = 2 * quiet_times[source]
            bot.say('quiet time is doubled to %s' % (quiet_times[source]))
            mute_user(bot,trigger)
    return


