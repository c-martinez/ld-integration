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
from rfc3987 import parse

from rdflib import ConjunctiveGraph
from rdflib_jsonld.context import Context

# Settings as defined by: https://github.com/digitalbazaar/pyld
FORMAT_NQUADS = {'algorithm': 'URDNA2015', 'format': 'application/nquads'}

logger = logging.getLogger('buildTtl')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

def loadPrefixes(knownPrefixes):
    logger.info('Loading context from %s...'%knownPrefixes)
    with open(knownPrefixes, 'r') as fin:
        global_context = {}
        for line in fin:
            parts = line.split(':', 1)
            prefix = parts[0].strip()
            iri = parts[1].strip()
            global_context[prefix] = iri
        return global_context

def savePrefixes(global_context, filename):
    filename = filename.replace('.ttl', '')
    filename = filename.replace('.nq', '')
    filename = filename + '.prefixes'
    logger.info('Saving context tp %s...'%filename)
    with open(filename, 'w') as fout:
        for name,iri in global_context.iteritems():
            fout.write('%s:%s\n'%(name, iri))

def getContext(knownPrefixes, scroller, out_file):
    if knownPrefixes:
        global_context = loadPrefixes(knownPrefixes)
    else:
        logger.info('Building context...')
        global_context = {}
        counter = 0
        limit = 5000
        for item in scroller.scan():
            ctx = item['@context']
            context = ctx.to_dict()
            for prefix,url in context.iteritems():
                global_context[prefix] = url
            counter += 1
            if counter >= limit:
                # HACK! -- exit loop after 5k triples -- by now we probably have seen all the contexts we will ever see
                break
        savePrefixes(global_context, out_file)
    return global_context

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

    global_context = getContext(knownPrefixes, scroller, out_file)
    ctx = Context(global_context)

    logger.info('Building graph...')

    format = 'turtle' if use_ttl else 'nquads'
    logger.info('Serializing to file ' + out_file + '...')
    logger.info('Using %s format...' % format)

    counter = 0
    with open(out_file, 'w') as fout:
        # Write headers first times
        g = ConjunctiveGraph()
        g.parse(data='{}', context=global_context, format='json-ld')
        serialized_data = g.serialize(format=format)
        fout.write(serialized_data)

        for item in scroller.scan():
            counter += 1
#            if counter==100000:
#                break

#            if (counter % 100) == 0:
#                logger.warning('Counter: ' + str(counter))

            g = ConjunctiveGraph()
            try:
                doc = item['@graph'].to_dict()
                doc_str = json.dumps(doc)
            except:
                logger.error('Item without @graph -- is the selected index in JSON-LD format?')
                exit

            itemId = doc['@id']
            expandedId = ctx.expand(itemId)
            if expandedId == itemId:
                try:
                    parse(itemId, rule='IRI')
                except:
                    logger.warning('ID cannot be expanded to URI: ' + itemId)

            g.parse(data=doc_str, context=global_context, format='json-ld')
            serialized_data = g.serialize(format=format)

            lines = serialized_data.split('\n')
            lines = [ line for line in lines if not line.startswith('@prefix') ]
            serialized_data = '\n'.join(lines)
            fout.write(serialized_data)
