const craigslist = require('node-craigslist')
const yargs = require('yargs')
const hl = require('highland')
const fs = require('fs')
var path = require('path')

/*
#Craigslist scraper
This script will run through the craigslist housing results based on location (defaulting to DC if argument not supplied) and optional min and max price arguments -> outputting the results to a text file.

## From the CLI run this command:
```node craigslist.js scrpeCraigslist --maxPrice=2100```
*/

const scrapeCraigslistCommand = {
    command: 'scrpeCraigslist',
    desc: 'Scrape craigslist for apartments within a specific budget',
    builder: yargs => {
      return yargs.options({
        category: {
            alias: ['category', 'c'],
            describe: 'Craigslist category to search',
            type: 'string',
            requiresArg: true,
            default: 'apa'
        },
        location: {
          alias: ['location', 'l'],
          describe: 'Location of Craigslist search',
          type: 'string',
          requiresArg: true,
          default: 'dc'
        },
        minPrice: {
            alias: ['min'],
            describe: "Minimum price you'd pay",
            type: 'number'
        },
        maxPrice: {
            alias: ['max'],
            describe: "Maximum price you'd pay",
            type: 'number'
        },
        offset: {
            alias: ['offset', 'o'],
            describe: 'Offset number of listings returned',
            type: 'number'
        }
      })
    },
    handler: argv => {
        // create text file
        const txtFile = argv.maxPrice ? path.join(__dirname, `/${argv.location}_housing_${argv.maxPrice}.txt`) : path.join(__dirname, `/${argv.location}_housing.txt`)
        // create text stream to write to
        const textFile = fs.createWriteStream(txtFile, {
            flags: 'a'
          })

        // create craigslist client based on location
        // by default this will run through housing, but can be changed based on `category` argument
        // add in min & max price if provide in initial arguments
        const client = new craigslist.Client({
            city: argv.location
        })
        const options = {
            category: argv.category
        }
        if (argv.minPrice) {
            options.minPrice = argv.minPrice
        }
        if (argv.maxPrice) {
            options.maxPrice = argv.maxPrice
        }

        client
          .search(options)
          .then(listings => {
              var stream = hl(listings)
              // write each result to a text file
              stream.each(item => {
                const { location, price, title } = item
                textFile.write(`Location: ${location.replace('(', '').replace(')', '')}\nPrice: ${price}\nTitle: ${title}\n\n`)
                console.log(`Location: ${location.replace('(', '').replace(')', '')}\nPrice: ${price}\nTitle: ${title}\n`)
            })
            textFile.end()
          })
          .catch((err) => {
            console.error(err)
          })
    }
}

yargs
    .command(scrapeCraigslistCommand)
    .help().argv
