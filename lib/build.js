#!/usr/bin/env node

var fs = require('fs');
var csv = require('fast-csv')

var outData = []
fs.createReadStream("../data/inspect.csv")
    .pipe(csv({headers : true}))
    .on("data", function(data){
        outData.push(data)
    })
    .on("end", function(){
    	outData = {"data":outData}
        fs.writeFile("../data/domainData.json",JSON.stringify(outData));
    });