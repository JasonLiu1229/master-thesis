public class TestClass5353 {
@Test public void func_1() { DropTableIfExistsImpl var_1 = new DropTableIfExistsImpl(null, "table", mock(SqlPart.class)); RawSqlBuilder var_2 = new RawSqlBuilderImpl(); var_1.prependTo(var_2); assertThat(var_2.toString(), is("TABLE IF EXISTS table")); }
}