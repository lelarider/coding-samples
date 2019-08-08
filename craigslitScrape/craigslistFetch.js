const yargs = require('yargs')
const fetch = require('node-fetch')
const url = require('url')
const hl = require('highland')
const fs = require('fs')
var path = require('path')

/*
#Craigslist scraper
This script will run through the DC craigslist housing results and optional min and max price arguments -> outputting the results to a text file.

## From the CLI run this command:
```node craigslistFetch.js scrpeCraigslist --searchQuery=shaw --maxPrice=2100```
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
        searchQuery: {
          alias: ['location', 'l'],
          describe: 'Location of Craigslist search',
          type: 'string',
          requiresArg: true,
          default: 'dc'
        },
        minPrice: {
            alias: ['min'],
            describe: "Minimum price you'd pay",
            type: 'number',
            default: 0
        },
        maxPrice: {
            alias: ['max'],
            describe: "Maximum price you'd pay",
            type: 'number',
            default: Infinity
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
      const txtFile = argv.maxPrice ? path.join(__dirname, `/${argv.location}_clSearch_${argv.maxPrice}.txt`) : path.join(__dirname, `/${argv.location}_clSearch.txt`)
      // create text stream to write to
      const textFile = fs.createWriteStream(txtFile, {
          flags: 'a'
        })

      // create URL for fetch
      // add in requested params
      const clUrl = new url.URL(`https://washingtondc.craigslist.org/jsonsearch/${argv.category}/`)
      if (argv.searchQuery) {
        const params = {
          query: argv.searchQuery
        }
        Object.keys(params).forEach(key => clUrl.searchParams.append(key, params[key]))
      }
      fetch(clUrl)
      .then(response => {
        return response.json()
      })
      .then(listings => {
        var stream = hl(listings[0])
        // write each result to a text file
        stream.each(item => {
          const { PostingTitle, Ask } = item
          if (argv.minPrice < Ask && Ask < argv.maxPrice) {
            textFile.write(`Title: ${PostingTitle}\nPrice: ${Ask}\n\n`)
            console.log(`Title: ${PostingTitle}\nPrice: ${Ask}\n`)
          }
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
