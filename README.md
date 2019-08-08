# code-samples

**These two folders contain code samples.**

# Craigslist scraper
This script will run through the craigslist housing results based on location (defaulting to DC if argument not supplied) and optional min and max price arguments -> outputting the results to a text file.

The *craigslist.js* file uses the node-craigslist npm package. 
## From the CLI run this command:
```node craigslist.js scrpeCraigslist --maxPrice=2100```

The *craigslistFetch.js* file fetches json from the `https://washingtondc.craigslist.org/jsonsearch/` endpoint.
This enpoint allows for a `searchQuery` argument which will apply the search word(s) to the PostingTitle (ie. to search for listings in a particular neighborhood (Shaw) or with certain attributes (Spacious)).
## From the CLI run this command:
```node craigslistFetch.js scrpeCraigslist --searchQuery=shaw --maxPrice=2100```

# Flask app outline
I/O application
This application is a condensed and stripped down version of a much larger application created. Intended for the sake of example.
