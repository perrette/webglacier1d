""" helper functions
"""
import hashlib

def keepincache(fun):
    """ decorator to prevent a function from being called twice with the 
    same arguments.
    """
    DATA = {}
    def get_id_for_dict(dict_):
        " create a unique id for any dict"
        unique_str = ''.join(["'%s':'%s';"%(key, val) for (key, val) in sorted(dict_.items())])
        return hashlib.sha1(unique_str).hexdigest()

    def fun2(*args, **kwargs):
        loc = locals()
        id_ = get_id_for_dict(loc)
        if id_ not in DATA:
            res = fun(*args, **kwargs)
            DATA[id_] = res
            # print "result:",res
        return DATA[id_]

    fun2.DATA = DATA # access it from outside

    return fun2

