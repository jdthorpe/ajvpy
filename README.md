A very thin wrapper around the awesome
[AJV](http://epoberezkin.github.io/ajv/) JSON validation library for
JavaScript.  Depends on the [PyV8](https://pypi.python.org/pypi/PyV8/)
package.  Just use `import Ajv from ajvpy`, and away you go.

## Getting started

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

