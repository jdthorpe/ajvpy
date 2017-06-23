A very thin wrapper around the awesome
[AJV](http://epoberezkin.github.io/ajv/) JSON validation library for
JavaScript.  Depends on the [PyV8](https://pypi.python.org/pypi/PyV8/)
package.  Just use `import Ajv from ajvpy`, and away you go.

# Getting started

Note that the only real change is that you need to drop the JavaScript's
`new` and `var` operators.  See the official [AJV
Readme](https://github.com/epoberezkin/ajv) for API documentation. 

The fastest validation call:

```python
from ajvpy import Ajv 
ajv = Ajv() # options can be passed, e.g. {"allErrors": True}
validate = ajv.compile(schema)
valid = validate(data)
if not valid: print(validate.errors)
```
or with less code

```python
# ...
valid = ajv.validate(schema, data)
if not valid: print(ajv.errors)
# ...
```

or

```python
# ...
ajv.addSchema(schema, 'mySchema')
valid = ajv.validate('mySchema', data)
if not valid: print(ajv.errorsText())
# ...
```

See [API](https://github.com/epoberezkin/ajv#api) and
[Options](https://github.com/epoberezkin/ajv#options) for more details.

### Object Modification with AJV

When using custom keywords which modify an object, the modified object may
be accessed via the `last` attribute of an `Ajv` or `validator ` instance
(after making the round-trip from python to JavaScript and back, of course):

```Python
import ajvpy
ajv = ajvpy.Ajv()
ajv.addKeyword('add-value', {
        "modifying": True,
        "type": "number",
		# note that ajvpy._eval(...) is not encouraged, see below
        "compile": ajvpy._eval("""(function (schema) {
            return (function (data, path, parent, key) {
                try {
                    parent[key] += schema;
                    return true;
                }
                catch (err) {
                    return false;
                }
            });
        })"""),
		"metaschema":{"type":"number"},
		})

x = {"value":1}

ajv.validate({
	"type":"object",
	"properties":{
		"value":{
			"type":"number",
			"add-value":3
			}
		},
	},x)

x
#> {'value': 1}
ajv.last
#> {'value': 4}
```
<sup>** note that `ajvpy._eval(...)` evaluates JS code in the global scope and
is not encouraged.  Loading external UMD or CommonJS modules via
`ajvpy.load()` is preferred.</sup>

# Plugin Modules

CommonJS and UMD modules containing custom
[keywords](https://github.com/epoberezkin/ajv#defining-custom-keywords) and
[formats](https://github.com/epoberezkin/ajv#api-addformat) which would be
loaded in NodeJS via:

```JavaScript
// Create an Ajv instance
var Ajv = requrire("ajv");
var ajv = new Ajv();

// Import the plugin module
var my_plugin = require("some-plugin-module");

// Add the keywords and/or formats to the instance
my_plugin(ajv) 
// or 
my_plugin(ajv,{"My":"options"}) 

```

and which are bundled into a stand alone bundle (see `Creating Plugin
Bundles`, below) can be loaded onto an `ajvpy` instance like so:

```Python
# Create an Ajv instance
from ajvpy import Ajv 
ajv = Ajv()

# Import and add the keywords and/or formats to the instance
ajv.plugin("path/to/my/bundle.js")
# or 
ajv.plugin("path/to/my/bundle.js",{"My":"options"})
```

Or to re-use the plugin module, use:

```Python
from ajvpy import load

my_module = load("path/to/my/bundle.js")

ajv.plugin(my_module)
# or 
ajv.plugin(my_module,{"My":"options"})
```

# Creating Plugin Bundles

Plugin bundles can be created from node modules using one of the many
JavaScript bundlers, such as [webpack](https://webpack.js.org/) or
[Browserify](http://browserify.org/). The simplest way to bundle a NPM
module containing an AJV plugin is to call:

```
cd path/to/ajvpy
npm install my-favorite-ajv-plugin
npm run bundle -- my-favorite-ajv-plugin
```

which will cause `webpack` to create a bundle of your plugin here at 
`ajvpy/plugins/my-favorite-ajv-plugin.js` that can be used like so:

```Python
from ajvpy import Ajv 
ajv = Ajv()

# Import and add the keywords and/or formats to the instance
ajv.plugin("my-favorite-ajv-plugin")
# or 
ajv.plugin("my-favorite-ajv-plugin",{"My":"options"})
```


# AJV Version

The currently bundled version of `AJV` is 5.2.0.  To update the version of
`AJV` used by `ajvpy`, you'll need to have [NodeJS](https://nodejs.org/)
installed on you machine, and then run: 

```
cd path/to/ajvpy
npm install
npm install ajv@latest
npm run webpack
```
