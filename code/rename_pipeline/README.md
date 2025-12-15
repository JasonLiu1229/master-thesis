# Pipeline

## File formats Eval

When the pipeline is used for evaluation, the files that are accepted should be of the form `.jsonl`. This is needed for an input and expected output comparison. The `.jsonl` file should consist therefore of the actual input that needs to be converted and the oracle output.

Here an example of how it should look like:

```jsonl
{
  "prompt": "public class TestClass1 {\r\n@Test public void func_1() { Date var_1 = DateUtils.yearEnd(); assertNotNull(var_1); GregorianCalendar var_2 = new GregorianCalendar(); var_2.setTime(var_1); assertEquals(11, var_2.get(MONTH)); assertEquals(31, var_2.get(DAY_OF_MONTH)); }\r\n}",
  "response": "public class TestClass1 {\r\n@Test public void yearEnd() { Date date = DateUtils.yearEnd(); assertNotNull(date); GregorianCalendar calendar = new GregorianCalendar(); calendar.setTime(date); assertEquals(11, calendar.get(MONTH)); assertEquals(31, calendar.get(DAY_OF_MONTH)); }\r\n}"
}
```

As you can see the prompt will be the obfuscated or input java code and the response should be the oracle output.

## How does it work

So the pipeline works using docker. It is defined as 't3'.

It consist of several arguments:

- mode: with this you can select what mode you will use the pipeline as. You can use it for a single file, a whole directory or for evalutaion.
- file: when selecting single, you have to specify what file you want to process
- dir: when selecting dir or eval, you have to specify what directory you want to process
- force: this flag enables overwriting of existing files, in case files already exist they will be overwritten when this flag is enabled
- output: this flag specifies where the newly generated files will be stored

Note: in the docker compose file you will see, t3 and t3_eval. As you can guess one is for evaluation and makes use of jsonl files. These files needs to be made seperatly, similar to the [tuning](../tuner/README.md) code. The processing code itself can be found in the [tools](../../tools/) folder.

## Note

The pipeline can handle multi-threading but this also depends if the model that you are using can handle multi-threading. For local computing, the`Qwen` model, we make use of a lock, so it is the same as single threading.

If you would use a seperate server, this would be the most optimal because, here you can optimize it so it can handle multithreading. (vLLM, Ollama, ...)
