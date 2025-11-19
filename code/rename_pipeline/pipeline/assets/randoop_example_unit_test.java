import org.junit.Test;
import static org.junit.Assert.*;
import static org.evosuite.runtime.EvoAssertions.*;

public class Calculator_ESTest {

    @Test(timeout = 4000)
    public void test0() throws Throwable {
        Calculator calc = new Calculator();
        int result = calc.add(2, 3);

        assertEquals(5, result);
    }

    @Test(timeout = 4000)
    public void test1() throws Throwable {
        Calculator calc = new Calculator();
        int result = calc.multiply(4, 0);

        assertEquals(0, result);
    }

    @Test(timeout = 4000)
    public void test2() throws Throwable {
        Calculator calc = new Calculator();
        
        try {
            calc.divide(10, 0);
            fail("Expected ArithmeticException to be thrown");
        } catch (ArithmeticException e) {
            // Expected exception
        }
    }

    @Test(timeout = 4000)
    public void test3() throws Throwable {
        Calculator calc = new Calculator();
        int result = calc.subtract(10, 7);

        assertEquals(3, result);
    }

    @Test(timeout = 4000)
    public void test4() throws Throwable {
        Calculator calc = new Calculator();

        int a = calc.add(-5, -3);
        int b = calc.multiply(a, 2);
        int c = calc.subtract(b, -4);

        assertEquals(-16, c);
    }
}
