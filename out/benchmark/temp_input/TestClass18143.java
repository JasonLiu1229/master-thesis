public class TestClass18143 {
@Test public void func_1() { OpearPlanMojo var_1 = newMojo(); assertNotNull("always have plan params", var_1.getPlanBuilderParams()); var_1.planParams = new PlanParams(); assertSame("same plan params", var_1.planParams, var_1.getPlanBuilderParams()); }
}