# Master thesis: Renaming identifiers using LLM

## Tools

In the `tools/` folder you can find several tools I made to help you with running this project.
In case you are running this on Windows, you can use the `change_java_version.ps1` to switch java versions in case needed.
In linux this is done by changing the `JAVA_HOME` variable.

## Enviroment variables

Note this project makes use of private enviroment variables. This is because we work with api keys and to inialize this, you need to generate one for your own model. This is only applied for the API version of this project.

These are the keys that needs to be specified in your `.env` file:

```txt
    API_KEY=sk-example-api-code
    API_URL=https://api.example.com
```

## Setup steps

### Prerequirements

- Docker
- Python (Optionally with Poetry)
  - Version 3.12.4 for main software
  - Version 3.8.4 for Refbert (benchmarking)
  - Version 3.7 for GNN (benchmarking)
- Rust (for one the tooling)
- Java (depending on what you want, you might need to install different versions of Java)

Note: Windows might need seperate compilers to make some things work. This is needed for `pybind11` and other libraries.

### Steps

#### Benchmarking

Benchmarking is done using docker containers. To fully seperate each technique from interfering with each other, we setup a docker container for each technique and parse the results to a seperate file. So make sure docker is installed and working.

#### LLM tool
