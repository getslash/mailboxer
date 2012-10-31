import inspect

class Signature(object):
    def __init__(self, argtypes, optionals):
        super(Signature, self).__init__()
        self.argtypes = argtypes
        self.optionals = optionals

class SignatureException(Exception):
    pass

class MissingArgumentType(SignatureException):
    pass

class UnknownArgumentsException(SignatureException):
    pass

def get_function_signature(func, argtypes):
    argtypes = dict(argtypes)
    argspec = inspect.getargspec(func)
    untyped = set(argspec.args) - set(argtypes)
    if untyped:
        raise MissingArgumentType("The following arguments have no type: {}".format(", ".join(sorted(untyped))))
    unknown = set(argtypes) - set(argspec.args)
    if unknown:
        raise UnknownArgumentsException("The following arguments aren't real arguments")
    optionals = set(argspec.args[-len(argspec.defaults or ()):])
    return Signature(argtypes, optionals)
