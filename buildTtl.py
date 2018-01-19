"""Build .

Usage:
  buildTtl.py <index_name> <outfile> [--host HOST]

Examples:
  buildTtl.py open-beelden-beeldengeluid oai.ttl
  buildTtl.py open-beelden-beeldengeluid oai.ttl --host localhost:9200

Options:
  -h --help     Show this screen.
"""
from docopt import docopt

import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from rdflib import Graph

# Settings as defined by: https://github.com/digitalbazaar/pyld
FORMAT_NQUADS = {'algorithm': 'URDNA2015', 'format': 'application/nquads'}

logger = logging.getLogger('buildTtl')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == '__main__':
    args = docopt(__doc__)
    # index_name = "open-beelden-beeldengeluid"
    index_name = args['<index_name>']
    out_file = args['<outfile>']

    host = args['HOST'] if args['--host'] else None
    client = Elasticsearch(host)

    scroller = Search(using=client, index=index_name).query()

    logger.info('Using index: ' + index_name)

    logger.info('Building context...')
    global_context = {}
    for item in scroller.scan():
        ctx = item['@context']
        context = ctx.to_dict()
        for prefix,url in context.iteritems():
            global_context[prefix] = url

    logger.info('Building graph...')
    g = Graph()
    for item in scroller.scan():
        doc = item['@graph'].to_dict()
        doc_str = json.dumps(doc)
        g.parse(data=doc_str, context=global_context, format='json-ld')

    logger.info('Serializing to file ' + out_file + '...')
    g.serialize(out_file, format='turtle')
