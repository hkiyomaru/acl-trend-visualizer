# ACL Investigator

A tool to count how many ACL papers including specific keywords.

## Development Environment

* Python 3.6.0
* requests
* pdfminer.six
* and their dependencies

## How to Run

```
$ python src/run.py data/word-list-dltools.txt \
--year 16,17,18 \  # the year of conferences
--type ls \  # the type of submission ("l" and "s" indicate long and short paper respectively)
--out result.json  # the output will be given as a json file
```

See command line help for other options.

TODO:

- phrase search
