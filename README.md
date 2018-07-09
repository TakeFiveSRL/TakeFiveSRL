# TakeFiveSRL

## Pre-requisites:

### Python Libraries

jsonrpclib<br/>
nltk<br/>
simplejson<br/>
rdflib<br/>
pyyaml<br/>
ast<br/>
requests<br/>
SPARQLWrapper<br/>

## Standford NLP:

Stanford parser is one of the major components. It should be running on the port 127.0.0.1:9000. The version of Stanford NLP to be used for running the TakeFive SRL  is available from [1].

## How to run TakeFiveSRL:

Finally, in order to run the SRL algorithm, simply run the following command:

 python SemanticRoleLabelingVerbNetCentred.py  "I am eating an apple."
 
The software is also available as the Docker version which can be requested, please contact us at: diego.reforgiato@unica.it or mehwish.alam@istc.cnr.it.

[1] https://hub.docker.com/r/motiz88/corenlp/~/dockerfile/
