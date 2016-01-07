#!/usr/bin/env python
"""
slap.py - slaps nick with a trout
Copyright 2016 Marc Schaefer (gposse.de)
Licensed under GPLv3


More info:
 * jenni: https://github.com/myano/jenni/
 * Phenny: http://inamidst.com/phenny/
 * Sopel: http://sopel.org/sopel/
"""

import time, threading, random
from sopel.tools import Identifier, SopelMemory
from sopel.config.types import (
    StaticSection, ValidatedAttribute
)
import sopel.module



@sopel.module.commands('slap')
def slap(bot,trigger):
    """".slap <nick> - slaps <nick> with a large trout or maybe some other fish"""
    #bot.reply('Slapper triggered!')
    slap_words = ['large trout', 'stinky tuna', 'bubbly wale','roten perch']
    if not trigger.sender.startswith('#'):
       bot.reply('Slapping is done in pulbic!')
    nick = trigger.group(2)
    if nick is None:
        bot.reply('You must tell me who  to slap!')
        return
    slap_text = '%s slaps %s with a %s' % (trigger.nick,nick,random.choice (slap_words))
    bot.notice(slap_text,trigger.sender)

