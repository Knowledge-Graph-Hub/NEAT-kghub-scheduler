# NEAT-kghub-scheduler

Scheduling utility for starting NEAT jobs for KG-Hub resources.

## What does it do?

This scheduler monitors [KG-Hub](https://kg-hub.berkeleybop.io/) for the presence of project directories containing NEAT configuration files. The configuration file:

* must be named `neat.yaml`
* must be in the same directory as a single version's compressed graph files ([see an example here](https://kg-hub.berkeleybop.io/kg-ontoml/20220414/))
* must not have a directory named `graph_ml` in the same directory already (it will store new results here, so it won't overwrite existing files)

If the scheduler finds a NEAT config, it spins up a Google Cloud Platform instance to run NEAT as per the config.
When complete, it uploads outputs (like embeddings, models, results, and logs) to the specified remote bucket and path.

### Writing NEAT configs for scheduled runs

The scheduler won't upload extra files to the compute instance where the NEAT run will start.

Specify a URL for graph files in `neat.yaml` as something like this:

```
graph_data:
  graph:
    graph_path: https://path/to/graph/kg-horse.tar.gz
    node_path: merged-kg_nodes.tsv
    edge_path: merged-kg_edges.tsv
```
The `node_path` and `edge_path` values should be the names of files inside the compressed file.

The value for `embedding_file_name` may also be a URL.