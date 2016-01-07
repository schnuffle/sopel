#!/usr/bin/env python
"""
flood_detection.py - mutes nicks when flood is detected
Copyright 2016 Marc Schaefer (gposse.de)
Licensed under GPLv3
This module was developped looking how the jenni module banned_words.py does it's job
There're three  parts for this module:

1. flood_detection
Flood_detection module based on the flood detection module of cinnabot
The difference is that cinnabot uses the python irc module which offers a irc.execute_delayed method 
used to unmute a user

2. unmute_loop
Creates a loop triggered every loop_rate seconds to check for users that needs to be unmuted

3. additional debug and management commands

More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
 * Sopel: http://sopel.org/sopel/
"""

import time, threading, os, json
from sopel.tools import Identifier, SopelMemory, iterkeys
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

    for channel in bot.config.core.channels:
        bot.memory['muted_users'].setdefault(channel, SopelMemory())

    fn = bot.nick + '-' + '.muted_users.json'
    bot.muted_users_filename = os.path.join(bot.config.core.homedir, fn)
    if not os.path.exists(bot.muted_users_filename):
        try:
            f = open(bot.muted_users_filename, 'w')
        except OSError:
            pass
        else:
            f.write('')
            f.close()
    bot.memory['muted_users_lock'] = threading.Lock()
    #bot.memory['muted_users'] = loadMutedUsers(bot.muted_users_filename,bot.memory['muted_users_lock'])

def shutdown(bot=None):
    dumpMutedUsers(bot.muted_users_filename, bot.memory['muted_users'], bot.memory['muted_users_lock'])

def mute_user(bot,trigger):
    mute_host = trigger.hostmask.split("@")[1]
    mute_mask = "*!*@%s" % mute_host
    channel= trigger.sender
    nick = trigger.nick

    if bot.memory['muted_users'][channel].contains(nick):
        bot.memory['muted_users'][channel][nick] = [mute_mask, time.time(), bot.config.flood.quiet_time]   
        bot.write(['MODE',channel, '+b ', mute_mask])
        if bot.config.flood.debug_mode:
            bot.say('%s, you\'ll be muted for %s seconds' % (trigger.nick,bot.config.flood.quiet_time), channel)

def unmute_user(bot, channel, nick):
    if bot.memory['muted_users'][channel].contains(nick):
        if len(bot.memory['muted_users'][channel][nick]) == 3:
            mute_mask = bot.memory['muted_users'][channel][nick][0]
            bot.write(['MODE',channel, '-b ', mute_mask])
            bot.memory['muted_users'][channel][nick] = []
            #del(bot.memory['muted_users'][channel][nick])              

def loadMutedUsers(fn, lock):
    lock.acquire()
    try:
        with open(fn, 'r') as fp:
            result = json.load(fp)
    except:
        result = {}
    finally:
        lock.release()
    return result

def dumpMutedUsers(fn, data, lock):
    lock.acquire()
    try:
        with open(fn, 'w') as f: f.write(json.dumps(data))
    except IOError:
        pass
    finally:
        lock.release()
    return True

@sopel.module.interval(5)
def unban_loop(bot):
    debug_mode = bot.config.flood.debug_mode
    unmutelist = []
    for channel in bot.config.core.channels:
        if bot.memory['muted_users'].contains(channel):   
            if len(bot.memory['muted_users'][channel]) > 0:
                for nick,values in bot.memory['muted_users'][channel].items():
                    if len(values) == 3:
                        ban_time = values[1]
                        quiet_time = values[2]
                        if (time.time()-ban_time > quiet_time):
                            mute_mask = values[0]
                            if debug_mode:
                                bot.say('DEBUG: Unbanloop Unmuting nick %s with hostmask %s' % (nick,mute_mask), channel)            
                            unmutelist.append([channel,nick])
    for channel,nick in unmutelist:
        if bot.memory['muted_users'][channel].contains(nick):
            #bot.say('DEBUG: deleting table entry [%s],[%s] with muted_users array %s' % (nick,channel,bot.memory['muted_users']), channel)
            unmute_user(bot, channel, nick)

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
    
    # We only want to execute in a channel
    if not trigger.sender.startswith("#") :
        return

    # We don't want to warn or kickban admins
    if trigger.admin:
        #bot.reply('We don\'t mute admins')
        return

    channel = trigger.sender
    source = trigger.nick
    
    chan_ops = []
    chan_hops = []
    chan_voices = []
    if channel in bot.ops:
        chan_ops = bot.ops[channel]

    # First ensure bot is an op
    #
    #if bot.nick not in chan_ops:
    #    bot.reply('I don\'t have chanops %s' % bot.ops)
    #    return

    # Next ensure the sender isn't op, half-op, or voice
    if source in chan_ops or source in chan_hops or source in chan_voices:
        bot.reply('We don\'t mute halfops')
        return

    # when user posts more then <nb_messages< in <interval> seconds, flooding is triggered
    nb_messages =  bot.config.flood.nb_messages
    nb_messages2 =  bot.config.flood.nb_messages2
    interval =  bot.config.flood.flood_interval
    interval2 =  bot.config.flood.flood_interval2
    quiet_time = bot.config.flood.quiet_time
    quiet_time2 = bot.config.flood.quiet_time2
    debug_mode = bot.config.flood.debug_mode

    # put a timestamp for user and channel
    bot.memory['messages_by_source'].setdefault(channel, {}).setdefault(source, []).append(time.time())
    bot.memory['messages_by_source2'].setdefault(channel, {}).setdefault(source, []).append(time.time())
    
    
    bot.memory['muted_users'].setdefault(channel, SopelMemory()).setdefault(source, [])
    
    # keep nb_messages posts to be able to check for flooding
    bot.memory['messages_by_source'][channel][source] = bot.memory['messages_by_source'][channel][source][-int(nb_messages):]
    bot.memory['messages_by_source2'][channel][source] = bot.memory['messages_by_source2'][channel][source][-int(nb_messages2):]
    
    
    # check if source hits the flooding limits
    if (len(bot.memory['messages_by_source'][channel][source]) == int(nb_messages) and time.time() - min(bot.memory['messages_by_source'][channel][source]) < int(interval)) or (len(bot.memory['messages_by_source2'][channel][source]) == int(nb_messages2) and time.time() - min(bot.memory['messages_by_source2'][channel][source]) < int(interval2)): 
        #flooding detected
        #bot.reply('flooding detected')
        if bot.memory['muted_users'][channel].contains(source):
            #bot.reply('Key exists')
            if len(bot.memory['muted_users'][channel][source])==0:
                mute_user(bot,trigger)
            else:
                pass
        else:
            pass       
    return

@sopel.module.commands('floodlistmuted','flm')
def floodlistmuted(bot,trigger):
    """".floodlistmuted/.flm - list muted users """
    bot.reply('[ %s ]' % str(bot.memory['muted_users']))

@sopel.module.commands('floodload','fl')
def floodload(bot,trigger):
    """".floodload/.fl - list muted users """
    bot.memory['muted_users'] = loadMutedUsers(bot.muted_users_filename, bot.memory['muted_users_lock'])
    bot.reply('Loaded muted users!')

@sopel.module.commands('floodsave','fs')
def floodsave(bot,trigger):
    """".floodsave/.fs - list muted users """
    dumpMutedUsers(bot.muted_users_filename, bot.memory['muted_users'], bot.memory['muted_users_lock'])
    bot.reply('Muted users saved!')

@sopel.module.commands('floodprintconfig','fpc')
def floodprintconfig(bot,trigger):
    """.floodprintconfig - print the config paramters of the module."""
    bot.reply('[ nb_messages 1/2 = %s/%s, interval1/2 = %s/%s, quiet_time = %s ]' % (bot.config.flood.nb_messages,bot.config.flood.nb_messages2,bot.config.flood.flood_interval,bot.config.flood.flood_interval2,bot.config.flood.quiet_time))    

@sopel.module.commands('floodunmute','funm')
def floodunmute(bot,trigger):
    """".floodunmute/.funm <nick> - unmuted nick """
    channel = trigger.sender
    nick = Identifier(trigger.group(2))
    mute_mask = '%s!*@*' % nick
    bot.write(['MODE',channel, '-b ', mute_mask])
    
@sopel.module.commands('floodreset','fr')
def floodreset(bot,trigger):
    """".floodreset/.fr - reset quiet_time """
    channel = trigger.sender
    for nick,values in bot.memory[trigger.sender].items():
        values[4] = 0
        bot.memory['muted_users'][trigger.sender][nick] = values
