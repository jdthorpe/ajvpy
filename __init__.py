# INITIALIZE THE CONTEXT
import pkg_resources 
import PyV8 

ajv_js = pkg_resources.resource_string( __name__, '/'.join(('js', "ajv.js")))
ctx = PyV8.JSContext() 
ctx.enter() 
ctx.eval(ajv_js)

# ------------------------------
# HELPER FUNCTIONS BORROWED FROM: 
# http://stackoverflow.com/a/28652754/1519199
# ------------------------------

def _access_with_js(ctx, route):
    if len(route) == 0:
        raise Exception("route must have at least one element")
    accessor_string = route[0]
    for elem in route[1:]:
        if type(elem) in [str, unicode]:
            accessor_string += "['" + elem + "']"
        elif type(elem) == int:
            accessor_string += "[" + str(elem) + "]"
        else:
            raise Exception("invalid element in route, must be text or number")
    return ctx.eval(accessor_string)

def _get_py_obj(ctx, obj, route=[]):
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
            _ = str(_access_with_js(ctx, route)) #working around a problem with PyV8 r429
        num_elements = len(obj)
        for index in range(num_elements):
            elem = obj[index]
            cloned.append(_get_py_obj(ctx, elem, route + [index]))
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
    elif type(obj) == str:
        cloned = obj.decode('utf-8')
    else:
        cloned = obj
    return cloned


def load(filepath):
    with open(filepath) as fh:
        return ctx.eval("(function(){module = {exports:{}};exports = module.exports;%s;return module.exports;})()"
                        % fh.read())

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
            js_obj[key] = _get_js_obj(ctx,obj[key])
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
    # Plugin
    # --------------------------------------------------

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
        return self.inst.validate(_get_js_obj(ctx,schema),_get_js_obj(ctx,data))

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
        return self.inst(_get_js_obj(ctx,data));
    def __getattribute__(self, name):
        if name == "errors":
            return _get_py_obj(ctx,self.inst.errors)
        else:
            return object.__getattribute__(self, name)

