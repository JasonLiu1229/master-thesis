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
