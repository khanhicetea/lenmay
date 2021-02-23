const { resolve } = require('path')
const { format } = require('util')
const { writeFileSync } = require('fs')
const { program } = require('commander')
const { execSync } = require("child_process")
const nunjucks = require('nunjucks')
const prompt = require('prompt-sync')();

nunjucks.configure({ autoescape: true })

const askYesNo = (msg, defaultValue) => {
    return prompt(format("%s [%s] ", msg, defaultValue ? "Y/n" : "y/N"), defaultValue ? 'y' : 'n').toLowerCase() == 'y'
}

const runCmd = (cmd, stopIfError = true, printOut = true) => {
    try {
        const output = execSync(cmd, {shell: true}).toString()
        if (printOut) console.log(output)
    } catch (e) {
        if (stopIfError) {
            console.error('[ERROR] ' + cmd)
            process.exit()
        }
    }
}

const runScriptTemplate = (template, ctx) => {
    const content = nunjucks.render(template, ctx)
    const filePath = format("/tmp/lenmay-%s.sh", Math.ceil(Math.random() * 10E10))
    console.log(filePath)
    writeFileSync(filePath, content)
}

program.version('1.0.0');

program
    .command('init')
    .description('Init lenmay')
    .option('-d, --default', 'Default settings, LEMP stack')
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

        runScriptTemplate('templates/init.sh.twig', settings)
    })

program.parse(process.argv);
