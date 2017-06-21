var path = require('path');
var fs = require('fs');

ajv_package = JSON.parse(fs.readFileSync("./node_modules/ajv/package.json","utf8"))


module.exports = {
  entry: path.resolve(path.join("./node_modules/ajv",ajv_package.main)),
  output: {
    filename: 'js/ajv.js',
    path: path.resolve(__dirname),
    library: 'Ajv',
    libraryTarget: 'var'
  }
};
