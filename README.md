# Master thesis: Renaming identifiers using LLM

## Tools

In the `tools/` folder you can find several tools I made to help you with running this project.
In case you are running this on windows, you can use the `change_java_version.ps1` to switch java versions in case needed.
In linux this is done by changing the `JAVA_HOME` variable.

## Enviroment variables

Note this project makes use of private enviroment variables. This is because we work with api keys and to inialize this, you need to generate one for your own model. This is only applied for the API version of this project.

These are the keys that needs to be specified in your `.env` file:

```txt
    API_KEY=blablabla
    API_URL=https://api.example.com
```
