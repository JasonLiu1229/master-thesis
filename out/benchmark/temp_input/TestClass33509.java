public class TestClass33509 {
@Test public void func_1() throws Exception { Object var_1 = mock(Object.class); TestPojoGetter<Object> var_2 = new TestPojoGetter<Object>(var_1); StormTuple<TestPojoGetter<Object>> var_3 = new StormTuple<TestPojoGetter<Object>>(var_2, null, -1, null, null, null); Assert.assertSame(var_1, var_3.getValueByField(fieldNamePojo)); }
}