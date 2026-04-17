public class TestClass30831 {
@Test @Override public void func_1() { IAtomContainer var_1 = makeSingleAtom(); IRenderingElement var_2 = generator.generate(var_1, var_1.getAtom(0), model); List<IRenderingElement> var_3 = elementUtil.getAllSimpleElements(var_2); Assert.assertEquals(1, var_3.size()); }
}