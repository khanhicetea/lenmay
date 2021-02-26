const { resolve } = require('path')
const { format } = require('util')
const { writeFileSync } = require('fs')
const { program } = require('commander')
const { execSync } = require("child_process")
const { randomBytes } = require('crypto')
const nunjucks = require('nunjucks')
const prompt = require('prompt-sync')()
const execa = require('execa')

let dryRun = false

nunjucks.configure({ autoescape: true })

const askYesNo = (msg, defaultValue) => {
    return prompt(format("%s [%s] ", msg, defaultValue ? "Y/n" : "y/N"), defaultValue ? 'y' : 'n').toLowerCase() == 'y'
}

const randomString = (len, charSet) => {
    charSet = charSet || 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let random = '';
    for (var i = 0; i < len; i++) {
        const randomPoz = Math.floor(Math.random() * charSet.length);
        random += charSet.substring(randomPoz,randomPoz+1);
    }
    return random
}

const runScript = (content, onDone, onError = null) => {
    const filePath = format("/tmp/lenmay-%s.sh", Math.ceil(Math.random() * 10E10))

    writeFileSync(filePath, content)

    onError = onError ? onError : (err) => {
        console.log(err.message || 'Error')
    }

    if (dryRun) {
        return console.log("Dry run : " + filePath)
    }

    execa('/usr/bin/bash', [filePath], {
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

const runScriptTemplate = (template, ctx, onDone, onError = null) => {
    const content = nunjucks.render(template, ctx)
    runScript(content, onDone, onError)
}

program.version("1.0.0");

program
    .command("init")
    .description("Init lenmay")
    .option("-d, --default", "Default settings, LEMP stack")
    .option("--dry", "Dry Run")
    .action((options) => {
        let settings = {
            timezone: "Asia/Ho_Chi_Minh",
            nginx: true,
            mysql: true,
            redis: true,
            nodejs: true,
            php: true,
        }

        dryRun = options.dry

        if (!options.default) {
            settings.timezone = prompt("Default timezone ? ", settings.timezone)
            settings.nginx = askYesNo("NginX ?", settings.nginx)
            settings.mysql = askYesNo("Mysql ?", settings.mysql)
            settings.redis = askYesNo("Redis ?", settings.redis)
            settings.nodejs = askYesNo("Nodejs ?", settings.nodejs)
            settings.php = askYesNo("PHP ?", settings.php)
        }
        
        // Write down settings
        console.log(settings)

        settings.mysql_root_password = randomString(12)

        runScriptTemplate('templates/init.sh.twig', settings, () => {
            console.log("Done!")
        })
    })

program.parse(process.argv);
