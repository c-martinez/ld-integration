"""Build .

Usage:
  ttl2nq.py <infile> <outfile>

Examples:
  ttl2nq.py oai.ttl oai.nq

Options:
  -h --help     Show this screen.
"""
from docopt import docopt
from rdflib import ConjunctiveGraph

if __name__ == '__main__':
    args = docopt(__doc__)
    infile = args['<infile>']
    outfile = args['<outfile>']

    g = ConjunctiveGraph()
    g.parse(infile, format='turtle')
    g.serialize(outfile, format='nquads')
