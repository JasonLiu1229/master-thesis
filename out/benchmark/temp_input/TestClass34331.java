public class TestClass34331 {
@SuppressWarnings("unchecked") @Test public void func_1() { Request var_1 = createMockRequest(); Map<String, String[]> var_2 = createMock(Map.class); expect(var_1.getParamValues()).andReturn(var_2); replay(var_1, var_2); RequestWrapper var_3 = createRequestWrapper(var_1); assertEquals(var_2, var_3.getParamValues()); verify(var_1, var_2); }
}