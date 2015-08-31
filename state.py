# Generic state

Registered_Sates = {}
ActiveState = None
class State(object):
    def __init__(s, name):
        s.name = name
        stateInit(name)
    def moveTo(s, name, **kwargs):
        stateMove(s.name, name, **kwargs)
    def leaving(s):
        print "Leaving state %s." % s.name
    def entered(s, **kwargs):
        print "Entered %s." % s.name
    def event(s, name, **kwargs):
        print "event fired: %s" % name

def stateMove(src, dest, **kwargs):
    if dest in Registered_Sates and src in Registered_Sates:
        Registered_Sates[src].leaving()
        ActiveState = Registered_Sates[dest]
        Registered_Sates[dest].entered(name, **kwargs)
    else:
        print "Cannot find state: %s -> %s." % (src, dest)

def stateInit(name, obj):
    if name in Registered_Sates:
        print "State %s already registered." % name
    else:
        Registered_Sates[name] = obj
        if not ActiveState:
            ActiveState = obj
            ActiveState.entered()

def event(name, **kwargs):
    ActiveState.event(name, **kwargs)
