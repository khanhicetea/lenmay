const { resolve } = require('path')
const { format } = require('util')
const { writeFileSync } = require('fs')
const { program } = require('commander')
const { execSync } = require("child_process")
const nunjucks = require('nunjucks')
const prompt = require('prompt-sync')();
const execa = require('execa');

nunjucks.configure({ autoescape: true })

const askYesNo = (msg, defaultValue) => {
    return prompt(format("%s [%s] ", msg, defaultValue ? "Y/n" : "y/N"), defaultValue ? 'y' : 'n').toLowerCase() == 'y'
}

const runScriptTemplate = (template, ctx, onDone, onError = null) => {
    const content = nunjucks.render(template, ctx)
    const filePath = format("/tmp/lenmay-%s.sh", Math.ceil(Math.random() * 10E10))

    writeFileSync(filePath, content)

    onError = onError ? onError : (err) => {
        console.log(err.message || 'Error')
    }

    execa('/usr/bin/sh', [filePath], {
        stdin: process.stdin,
        stdout: process.stdout,
        stderr: process.stderr
    })
    .on('close', (code, signal) => {
        if (code === 0) {
            onDone(code, signal)    
        } else {
            onError(new Error(format("Error ! Exit Code %d , Signal %s", code, signal)))
        }
    })
    .on('error', (err) => { onError(err) })
}

program.version("1.0.0");

program
    .command("init")
    .description("Init lenmay")
    .option("-d, --default", "Default settings, LEMP stack")
    .action((options) => {
        let settings = {
            timezone: "Asia/Ho_Chi_Minh",
            nginx: true,
            mysql: true,
            redis: true,
            nodejs: true,
            php: true,
        }

        if (!options.default) {
            settings.timezone = prompt("Default timezone ? ", settings.timezone)
            settings.nginx = askYesNo("NginX ?", settings.nginx)
            settings.mysql = askYesNo("Mysql ?", settings.mysql)
            settings.redis = askYesNo("Redis ?", settings.redis)
            settings.nodejs = askYesNo("Nodejs ?", settings.nodejs)
            settings.php = askYesNo("PHP ?", settings.php)
        }

        console.log(settings)

        // runScriptTemplate('templates/init.sh.twig', settings)
        runScriptTemplate("templates/test.sh.twig", settings, () => {
            console.log("Done!")
        })
    })

program.parse(process.argv);
