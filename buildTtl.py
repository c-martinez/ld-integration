"""Build .

Usage:
  buildTtl.py <index_name> <outfile> (--ttl | --nq) [--host HOST] [--prefixes PREFIX_FILE]

Examples:
  buildTtl.py open-beelden-beeldengeluid oai.ttl --nq
  buildTtl.py open-beelden-beeldengeluid oai.ttl --nq --host localhost:9200
  buildTtl.py open-beelden-beeldengeluid oai.ttl --nq --host localhost:9200 --prefixes known_prefixes.txt

Options:
  -h --help     Show this screen.
"""
from docopt import docopt

import json
import logging
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from rdflib import ConjunctiveGraph
from rdflib_jsonld.context import Context

# Settings as defined by: https://github.com/digitalbazaar/pyld
FORMAT_NQUADS = {'algorithm': 'URDNA2015', 'format': 'application/nquads'}

logger = logging.getLogger('buildTtl')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def loadPrefixes(knownPrefixes, global_context):
    if knownPrefixes:
        with open(knownPrefixes, 'r') as fin:
            for line in fin:
                parts = line.split(':', 1)
                prefix = parts[0].strip()
                iri = parts[1].strip()
                global_context[prefix] = iri

if __name__ == '__main__':
    args = docopt(__doc__)
    # index_name = "open-beelden-beeldengeluid"
    index_name = args['<index_name>']
    out_file = args['<outfile>']
    use_ttl = args['--ttl'] # Otherwise --nq should be on args and we use NQ format
    knownPrefixes = args['PREFIX_FILE'] if args['--prefixes'] else None

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

    loadPrefixes(knownPrefixes, global_context)

    ctx = Context(global_context)

    logger.info('Building graph...')
    g = ConjunctiveGraph()
    for item in scroller.scan():
        doc = item['@graph'].to_dict()
        doc_str = json.dumps(doc)

        itemId = doc['@id']
        expandedId = ctx.expand(itemId)
        if expandedId == itemId:
            logger.warning('ID cannot be expanded to URI: ' + itemId)

        g.parse(data=doc_str, context=global_context, format='json-ld')

    logger.info('Serializing to file ' + out_file + '...')
    logger.info('Using %s format...' % ('TTL' if use_ttl else 'NQ'))
    if use_ttl:
        g.serialize(out_file, format='turtle')
    else:
        g.serialize(out_file, format='nquads')
