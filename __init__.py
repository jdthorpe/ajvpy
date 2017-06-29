# INITIALIZE THE CONTEXT
import pkg_resources 
import PyV8 

ajv_js = pkg_resources.resource_string( __name__, '/'.join(('js', "ajv.js")))
ctx = PyV8.JSContext() 
ctx.enter() 
ctx.eval(ajv_js)

def _eval(x):
    return ctx.eval("(%s)"%x)

# ------------------------------
# HELPER FUNCTIONS BORROWED FROM: 
# http://stackoverflow.com/a/28652754/1519199
# ------------------------------

def _build_accessor_string(ctx, route):
    if len(route) == 0:
        raise Exception("route must have at least one element")
    accessor_string = ""
    for elem in route:
        if type(elem) in [str, unicode]:
            accessor_string += "['" + elem + "']"
        elif type(elem) == int:
            accessor_string += "[" + str(elem) + "]"
        else:
            raise Exception("invalid element in route, must be text or number")
    return accessor_string


def _get_py_obj(ctx, obj, route=[]):
    # for handling of objects returned by Mongodb or MongoEngine
    def dict_is_empty(dict):
        for key in dict:
            return False
        return True
    def access(obj, key):
        if key in obj:
            return obj[key]
        return None
    cloned = None
    if isinstance(obj, list) or isinstance(obj, PyV8.JSArray):
        cloned = []
        if len(route):
            _ = str(_build_accessor_string(ctx, route)) #working around a problem with PyV8 r429
        for i in range(len(obj)):
            elem = obj[i]
            cloned.append(_get_py_obj(ctx, elem, route + [i]))
    elif isinstance(obj, dict) or isinstance(obj, PyV8.JSObject):
        cloned = {}
        for key in obj.keys():
            cloned_val = None
            if type(key) == int:
                #workaround for a problem with PyV8 where it won't let me access
                #objects with integer accessors
                val = None
                try:
                    val = access(obj, str(key))
                except KeyError:
                    pass
                if val == None:
                    val = access(obj, key)
                cloned_val = _get_py_obj(ctx, val, route + [key])
            else:
                cloned_val = _get_py_obj(ctx, access(obj, key), route + [key])
            cloned[key] = cloned_val
    elif isinstance(obj,basestring):
        cloned = obj.decode('utf-8')
    else:
        cloned = obj
    return cloned


def __validate_npm_package_name(x):
    return False

def load(filepath):
    if __validate_npm_package_name(filepath):
        filepath = _os.path.join(__dir,"plugin",filepath + ".js")
    assert _os.path.exists(filepath), ("No such file: " + filepath)
    with open(filepath) as fh:
        return ctx.eval("(function(){module = {exports:{}};exports = module.exports;%s;return module.exports;})()"
                        % fh.read())

import os as _os
__dir = _os.path.dirname(_os.path.realpath(__file__))
__validator_path = _os.path.join(__dir, 'js/validate-npm-package-name.js')
__is_valid_npm_package_name = load(__validator_path)
def __validate_npm_package_name(x):
    assert isinstance(x, basestring)
    return _get_py_obj(ctx,__is_valid_npm_package_name(x))["validForOldPackages"]

def _get_js_obj(ctx,obj):
    #workaround for a problem with PyV8 where it will implicitely convert python lists to js objects
    #-> we need to explicitely do the conversion. see also the wrapper classes for JSContext above.
    if isinstance(obj, list):
        js_list = []
        for entry in obj:
            js_list.append(_get_js_obj(ctx,entry))
        return PyV8.JSArray(js_list)
    elif isinstance(obj, dict):
        js_obj = ctx.eval("new Object();")
        for key in obj.keys():
            try:
                js_obj[key] = _get_js_obj(ctx,obj[key])
            except Exception, e:
                # unicode keys raise a Boost.python.aubment Exception which
                # can't be caught directly:
                # https://mail.python.org/pipermail/cplusplus-sig/2010-April/015470.html
                if (not str(e).startswith("Python argument types in")):
                    raise
                import unicodedata
                js_obj[unicodedata.normalize('NFKD', key).encode('ascii','ignore')] = _get_js_obj(ctx,obj[key])
        return js_obj
    else:
        return obj

# THE MAIN EXPORT
class Ajv(object):

    def __init__(self,options=None):
	# create the AJV instance in V8
        if options is None:
            self.inst = ctx.eval("new Ajv()")
        else:
            ctx.locals["_options"] = _get_js_obj(ctx,options)
            self.inst = ctx.eval("new Ajv(_options)")
            del ctx.locals["_options"]

    # --------------------------------------------------
    # NON-NATIVE METHODS AND ATTRIBUTES
    # --------------------------------------------------

    # --------------------
    # Plugin
    # --------------------
    def plugin(self,x,options=None):
        """ the Ajv.validate method

            The equivalent of calling \code{var ajv = new Ajv(); ajv.validate(...)} in javascript.

            @param schema The Schema with which to validate the \code{data}.
            @param data The data to be validated.  may be any of the above foremats. 

            @return boolean
        """
        if isinstance(x, basestring):
            x = load(x)
        assert x.__class__.__name__ == 'JSFunction', "x must be a string (file path) or loaded JS module"
        if options is not None:
            x(self.inst,_get_js_obj(ctx,options))
        else:
            x(self.inst)

    # --------------------
    # LAST
    # --------------------
    @property
    def last(self):
        """ returns the last object validated, for compatibility with modifying keywords
        """
        try:
            return _get_py_obj(ctx,self.__last)
        except AttributeError:
            raise AttributeError("'Ajv' has no attribute `last`; the property is only available after validating an object")


    # --------------------------------------------------
    # METHODS THAT RETURN A BOOLEAN
    # --------------------------------------------------

    def validate(self,schema,data):
        """ the Ajv.validate method

            The equivalent of calling \code{var ajv = new Ajv(); ajv.validate(...)} in javascript.

            @param schema The Schema with which to validate the \code{data}.
            @param data The data to be validated.  may be any of the above foremats. 

            @return boolean
        """
        self.__last = _get_js_obj(ctx,data)
        return self.inst.validate(_get_js_obj(ctx,schema),self.__last)

    def validateSchema(self,schema):
        """ the Ajv.validateSchema method

            The validate a json schema

            @param schema The Schema to be validated. 

            @return boolean
        """
        return self.inst.validateSchema(_get_js_obj(ctx,schema))

    # --------------------------------------------------
    # METHODS THAT RETURN an Object
    # --------------------------------------------------
    def compile(self,schema):
        """ The Ajv.compile method

            @return a callable ajv validator object
        """
        return validator(self.inst.compile(_get_js_obj(ctx,schema)))

    def getSchema(self,key):
        """ The Ajv.getSchema method

            @return a callable ajv validator object
        """
        return validator(self.inst.getSchema(_get_js_obj(ctx,key)))

    def errorsText(self):
        """ The Ajv.errorsText method

            Extracts the errors obj from the instance

            @return object containing the error message (if any)
        """
        return _get_py_obj(ctx,self.inst.errorsText())

    # --------------------------------------------------
    # METHODS THAT RETURN None
    # --------------------------------------------------
    def addSchema(self,key,schema):
        """ the Ajv.addSchema method

            The add a schema to an Ajv instance

            @param schema The schema to be added.
            @param key String; the name with which to store the schema

            @return None
        """
        self.inst.addSchema(_get_js_obj(ctx,key),_get_js_obj(ctx,schema))

    def removeSchema(self,key):
        """ the Ajv.removeSchema method

            The remove a schema from an Ajv instance

            @param key String; the name with schema to remove

            @return None
        """
        self.inst.removeSchema(_get_js_obj(ctx,key))

    def addFormat(self,key,format):
        """ the Ajv.addFormat method

            Add a string format to an Ajv instance.

            @param key String; the name with format to add.
            @param format the format to be added. 

            @return None
        """
        self.inst.addFormat(_get_js_obj(ctx,key))

    def keyword(self,key,obj):
        """ the Ajv.addFormat method

            Add a string format to an Ajv instance.

            @param key String; the name with keyword to add.
            @param obj the format to be added.  

            @return None
        """
        self.inst.keyword(_get_js_obj(ctx,key),_get_js_obj(ctx,obj))

    def addKeyword(self,name,definition):
        """ the Ajv.addKeyword method

            The add a schema to an Ajv instance

            @param name The name of the keyword to be added.
            @param definition A string encoding of a javascript obj to be used as to define the keyword.

            @return None
        """
        self.inst.addKeyword(_get_js_obj(ctx,name),_get_js_obj(ctx,definition))

    def __getattribute__(self, name):
        if name == "errors":
            return _get_py_obj(ctx,self.inst.errors)
        else:
            return object.__getattribute__(self, name)

class validator(object):
    def __init__(self,inst):
        self.inst = inst
    def __call__(self,data):
        self.__last = _get_js_obj(ctx,data)
        return self.inst(self.__last);
    def __getattribute__(self, name):
        if name == "errors":
            return _get_py_obj(ctx,self.inst.errors)
        else:
            return object.__getattribute__(self, name)
    # --------------------------------------------------
    # NON-NATIVE METHODS AND ATTRIBUTES
    # --------------------------------------------------
    @property
    def last(self):
        """ returns the last object validated, for compatibility with modifying keywords
        """
        try:
            return _get_py_obj(ctx,self.__last)
        except AttributeError:
            raise AttributeError("'Validator' has no attribute `last`; the property is only available after validating an object")

# a decorator for the clean method of MongoEngine.Document class
_ajv = None
def ajv_clean(schema,ajv=None):
    global _ajv
    from mongoengine import ValidationError
    if ajv is None:
        if _ajv is None:
            _ajv = Ajv()
        ajv = _ajv
    validator = ajv.compile(schema)
    def decorator(f):
        def wrapper(self):
            # execute ajv validator
            if not validator(dict(self.to_mongo())):
                msg = ", and ".join(["'%s' %s" %(e["schemaPath"],e["message"]) for e in validator.errors ])
                msg = ", and ".join(["'%s' %s" %(e["schemaPath"],e["message"]) for e in validator.errors ])
                err = ValidationError("AJV validation failed with message(s): "+msg)
                err.ajv_errors = validator.errors
                raise err
            # execute the normal Document.clean code
            f(self,validator.last)
        return wrapper
    return decorator

