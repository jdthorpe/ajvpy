"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var child_process_1 = require("child_process");
var path_1 = require("path");
var fs_1 = require("fs");
var validate_package_name = require("validate-npm-package-name");
var modules = process.argv, _module, package_json, outfile, outpath, main, command, child;
for (var i = 2; i < modules.length; i++) {
    // build the command
    _module = modules[i];
    console.log("hi");
    if (!validate_package_name(_module)) {
        console.log("Error: \"" + _module + "\" is not a valid package name.");
        continue;
    }
    package_json = JSON.parse(fs_1.readFileSync("./node_modules/" + _module + "/package.json", "utf8"));
    main = path_1.resolve(path_1.join("./node_modules/" + _module, package_json.main));
    outfile = _module + ".js";
    outpath = "../..//plugin/"; // relative to "./node_modules/.bin/"
    command = "webpack " + main + " --output-filename " + outfile + " --output-path " + outpath + " --output-library-target umd";
    // run webpack
    console.log("Bundling module \"" + _module + "\" via:\n> ", command);
    try {
        child = child_process_1.execSync(command, {
            cwd: path_1.resolve("./node_modules/.bin/"),
        });
    }
    catch (err) {
        console.log("webpack failed with err:", err);
    }
}
