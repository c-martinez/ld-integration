# Linked data integration

This repo contains tools for exporting data from Elasticsearch (in JSON-LD format) and importing it into Virtuoso.

First, install required libraries from `requirements.txt` file:
```
pip install -r requirements.txt
```

Use `buildTtl.py` to read an elasticsearch index (example: `open-beelden-beeldengeluid`) from an elasticsearch host (example: `http://localhost:9200`) and export it to file (example: `data/oai.ttl`) in turtle format. Run the following command:
```
mkdir data/
python buildTtl.py open-beelden-beeldengeluid data/oai.ttl --host http://localhost:9200
```

Now we will use [joernhees/docker-virtuoso docker image](https://github.com/joernhees/docker-virtuoso) to import the produced ttl file. Triples get imported into the specified graph (example: `https://www.clariah.nl/lod/`). Afterwards, virtuoso is started. Notice that a temporary directory (`db_dump/`) is created to hold the imported triples.
```
mkdir db_dump/
docker run --rm -v $PWD/data:/import -v $PWD/db_dump:/var/lib/virtuoso-opensource-7 joernhees/virtuoso import 'https://www.clariah.nl/lod/'
docker run -d --name virtuoso -v $PWD/db_dump:/var/lib/virtuoso-opensource-7 -p 8891:8890 joernhees/virtuoso
```

Virtuoso should now be running on port `8891`. You can browse to: `http://localhost:8891/sparql` and run your sparql query:
```
SELECT * WHERE {
  ?s ?p ?o
} LIMIT 100
```

Once you are done with your SPARQL repo, you can shut down the container and clear up the `db_dump` directory:
Stop and remove:
```
docker stop virtuoso
docker rm virtuoso
rm -fr db_dump
```

NOTE: `db_dump` might be owned by root.
