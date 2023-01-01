from asterisk.agi import *
agi = AGI()


def x():
    agi.verbose('exiting %s' %agi.appexec("asterisk -rx 'hangup request channelname'"))
        # y= agi.appexec("asterisk -rx 'hangup request channelname'")
        
