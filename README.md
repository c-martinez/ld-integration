# Linked data integration

This repo contains tools for exporting data from Elasticsearch (in JSON-LD format) and importing it into Virtuoso.

First, install required libraries from `requirements.txt` file:
```
pip install -r requirements.txt
```

Use `buildTtl.py` to read an elasticsearch index (example: `open-beelden-beeldengeluid`) from an elasticsearch host (example: `http://localhost:9200`) and export it to file (example: `rawdata/oai.ttl`) in turtle format. Run the following command:
```
mkdir rawdata/
python buildTtl.py open-beelden-beeldengeluid rawdata/oai.ttl --host http://localhost:9200
```

Now we will use [tenforce/docker-virtuoso docker image](https://github.com/tenforce/docker-virtuoso) to import the produced ttl file. We need to convert turtle files to nquads for virtuoso to import them. Triples get imported into the specified graph (example: `https://www.clariah.nl/lod/`). Afterwards, virtuoso is started. Notice that a data directory (`data/`) is created to contain virtuoso specific data, and the data is loaded from the `toLoad` directory.
```
mkdir data/
mkdir data/toLoad
python ttl2nq.py rawdata/oai.ttl data/toLoad/oai.nq
docker run --name virtuoso -p 8891:8890 -v $PWD/data:/data/ -e DEFAULT_GRAPH=https://www.clariah.nl/lod/ -d tenforce/virtuoso
```

Virtuoso should now be running on port `8891`. You can browse to: `http://localhost:8891/sparql` and run your sparql query:
```
SELECT * WHERE {
  ?s ?p ?o
} LIMIT 100
```

Or slightly more interesting:
```
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT * WHERE {
  ?id dcterms:title   ?title .
  ?id dcterms:subject ?subject .
  OPTIONAL { ?id dcterms:date      ?date   }
  OPTIONAL { ?id dcterms:issued    ?issued }

} LIMIT 100
```

Once you are done with your SPARQL repo, you can shut down the container and clear up the `data` directory:
Stop and remove:
```
docker stop virtuoso
docker rm virtuoso
rm -fr dump
```
