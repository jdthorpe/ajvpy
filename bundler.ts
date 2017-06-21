import {execSync} from 'child_process';
import {resolve, join} from 'path';
import {readFileSync, mkdirSync, existsSync} from 'fs';
var validate_package_name = require("validate-npm-package-name");


var modules:string[] = process.argv,
    _module:string,
    package_json:any,
    outfile:string,
    outpath:string,
    main:string,
    command:string,
    child;

for(let i = 2; i < modules.length; i++){
    // build the command
    _module = modules[i];
console.log("hi")
    if(!validate_package_name(_module)){
        console.log(`Error: "${_module}" is not a valid package name.`);
        continue;
    }
    package_json = JSON.parse(readFileSync(`./node_modules/${_module}/package.json`,"utf8"));
    main = resolve(join(`./node_modules/${_module}`,package_json.main));
    outfile = `${_module}.js`;
    outpath = `../..//plugin/`; // relative to "./node_modules/.bin/"
    command = `webpack ${main} --output-filename ${outfile} --output-path ${outpath} --output-library-target umd`;

    // run webpack
    console.log(`Bundling module "${_module}" via:\n> `, command );
    try{
        child = execSync(command,{
            cwd:resolve("./node_modules/.bin/"),
        });
    }catch(err){
        console.log("webpack failed with err:", err);
    }
}
