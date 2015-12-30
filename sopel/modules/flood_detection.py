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

import imp, os, re, time, threading
from sopel.tools import Identifier, SopelMemory
from sopel.config.types import (
    StaticSection, ValidatedAttribute
)
import sopel.module


class FloodSection(StaticSection):
    """ the number of message needed for the flood detection to kick in"""
    nb_messages = ValidatedAttribute('nb_messages', int, default=10)
    """ the number of message needed for the flood detection to kick in"""
    nb_messages2 = ValidatedAttribute('nb_messages2', int, default=10)
    """ the maximal time interval in seconds in which nb_messages can be posted
        before the flodd detection triggers """
    flood_interval = ValidatedAttribute('flood_interval', int, default=10)
    """ the maximal time interval in seconds in which nb_messages can be posted
        before the flodd detection triggers """
    flood_interval2 = ValidatedAttribute('flood_interval2', int, default=10)
    """ the time in seconds a user will be muted """
    quiet_time   = ValidatedAttribute('quiet_time', int, default=20)
    """ the time in seconds a user will be muted """
    quiet_time2   = ValidatedAttribute('quiet_time2', int, default=20)
    """ debug_moed adds some exrta output for debuggin purposes """
    debug_mode   = ValidatedAttribute('debug_mode', bool, default=True)    

def configure(config):
    """ Declare a [flood] section in the config to store module
        specific configuration values """
    config.define_section('flood', FloodSection)
    """ declare nb_messages parameter in seconds """
    config.flood.configure_setting(
        'nb_messages', "Number of posts after flood trigger is active."
    )
    config.flood.configure_setting(
        'nb_messages2', "Number of posts after flood trigger is active."
    )
    config.flood.configure_setting(
        'flood_interval', "Time span in witch nb_messages posts trigger flood detection."
    )
    config.flood.configure_setting(
        'flood_interval2', "Time span in witch nb_messages posts trigger flood detection."
    )
    config.flood.configure_setting(
        'quiet_time', "Time a user is muted."
    )
    config.flood.configure_setting(
        'quiet_time2', "Time a user is muted."
    )
    config.flood.configure_setting(
        'debug_mode', "Turn on some extra infos"
    )

def setup(bot=None):
   # TODO figure out why this is needed, and get rid of it, because really?
    if not bot:
        return
    bot.config.define_section('flood', FloodSection)
    bot.memory['messages_by_source'] = SopelMemory()
    bot.memory['messages_by_source2'] = SopelMemory()    
    bot.memory['muted_users'] = SopelMemory()
    bot.memory['last_sent_warning'] = SopelMemory()




def mute_user(bot,trigger):
    
    mute_host = trigger.hostmask.split("@")[1]
    mute_mask = "*!*@%s" % mute_host
    channel= trigger.sender
    nick = trigger.nick
    bot.memory['muted_users'][nick] = [channel, nick, mute_mask, time.time(), bot.config.flood.quiet_time] 
    bot.write(['MODE',channel, '+b m:%s' % mute_mask])

def unmute_user(bot, nick):
    channel= bot.memory['muted_users'][nick][0]
    mute_mask = bot.memory['muted_users'][nick][2]
    #bot.say('Unmuting %s' % mute_mask,channel)
    bot.write(['MODE',channel, '-b m:%s' % mute_mask])

@sopel.module.interval(5)
def unban_loop(bot):
    unmuted_list = []
    debug_mode = bot.config.flood.debug_mode
    # check if any nicks quiet_time is finished and unmute
    for nick,values in bot.memory['muted_users'].items():
        bantime = values[3]
        quiet_time = values[4]
        if (time.time()-bantime > quiet_time):
            mute_mask = values[2]
            channel = values[0]
            if debug_mode and "#test" in bot.channels:
                bot.say('DEBUG: Unbanloop Unmuting nick %s with hostmask %s' % (nick,mute_mask), channel)            
            unmute_user(bot, nick)
            unmuted_list.append(nick)
    for delnick in unmuted_list:
        del(bot.memory['muted_users'][nick])
    return

@sopel.module.rule(r'(.*)')
@sopel.module.priority('high')
def flood_detection(bot, trigger):
    """
    Listens to a channel for channel flooding. If one is found it first
    warns a user and mutes him for mute_time seconds, then after  repeat_warnings_limit kickbans them, where
    repeat_warnings defaults to 0, meaning instant ban.

    User warnings are stored only in memory, and as a result
    restarting jenni will eliminate any warnings.

    """
    
    # when user posts more then <nb_messages< in <interval> seconds, flooding is triggered
    nb_messages =  bot.config.flood.nb_messages
    nb_messages2 =  bot.config.flood.nb_messages2
    interval =  bot.config.flood.flood_interval
    interval2 =  bot.config.flood.flood_interval2
    quiet_time = bot.config.flood.quiet_time
    quiet_time2 = bot.config.flood.quiet_time2
    debug_mode = bot.config.flood.debug_mode
    
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
    bot.memory['messages_by_source'].setdefault(channel, {}).setdefault(source, []).append(time.time())
    bot.memory['messages_by_source2'].setdefault(channel, {}).setdefault(source, []).append(time.time())

    # keep nb_messages posts to be able to check for flooding
    bot.memory['messages_by_source'][channel][source] = bot.memory['messages_by_source'][channel][source][-int(nb_messages):]
    bot.memory['messages_by_source2'][channel][source] = bot.memory['messages_by_source2'][channel][source][-int(nb_messages):]
    
    
    # check if source hits the flooding limits
    if (len(bot.memory['messages_by_source'][channel][source]) == int(nb_messages) and time.time() - min(bot.memory['messages_by_source'][channel][source]) < int(interval)) or (len(bot.memory['messages_by_source2'][channel][source]) == int(nb_messages2) and time.time() - min(bot.memory['messages_by_source2'][channel][source]) < int(interval2)): 
        #flooding detected
        if time.time() - bot.memory['last_sent_warning'].setdefault(source, 0) > 600:
            bot.msg(source, "%s, Please don't paste in here when there's more than 3 lines. Use http://dpaste.com/ instead. Thank you !" % trigger.hostmask)
            bot.memory['last_sent_warning'][source] = time.time()
        if not source in bot.memory['muted_users'].keys():
            if debug_mode:
                bot.say('%s, you\'ll be muted for %s seconds' % (trigger.nick,quiet_time), source)
            mute_user(bot,trigger)
        else:
            bot.memory['muted_users'][source][4] = 2 * bot.memory['muted_users'][source][4]
            if debug_mode:
                bot.say('quiet time is doubled to %s for %s ' % (bot.memory['muted_users'][source][4],source))
    return

@sopel.module.commands('listmuted','lm')
def list_muted(bot,trigger):
    bot.reply('[ %s ]' % str(bot.memory['muted_users']), trigger.nick)
    
@sopel.module.commands('printconfig','pc')
def print_config(bot,trigger):
    bot.reply('[ nb_messages 1/2 = %s/%s, interval1/2 = %s/%s, quiet_time = %s ]' % (bot.config.flood.nb_messages,bot.config.flood.nb_messages2,bot.config.flood.flood_interval,bot.config.flood.flood_interval2,bot.config.flood.quiet_time))    
