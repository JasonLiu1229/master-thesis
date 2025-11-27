import org.junit.Test;
import static org.junit.Assert.*;
import static org.evosuite.runtime.EvoAssertions.*;

public class Calculator_ESTest {

    @Test(timeout = 4000)
    public void testAdditionOfTwoNumbers() throws Throwable {
        Calculator calculator = new Calculator();
        int sum = calculator.add(2, 3);

        assertEquals(5, sum);
    }

    @Test public void testMultiplicationByZero() throws Throwable {
        Calculator calculator = new Calculator();
        int multiplicationResult = calculator.multiply(4, 0);

        assertEquals(0, multiplicationResult);
    }

    @Test
    public void testDivisionByZero() throws Throwable {
        Calculator calculator = new Calculator();
        
        try {
            calculator.divide(10, 0);
            fail("Expected ArithmeticException to be thrown");
        }

    @Test(timeout = 4000)
    public void testSubtractionOperation() throws Throwable {
        Calculator calculator = new Calculator();
        int difference = calculator.subtract(10, 7);

        assertEquals(3, difference);
    }

    @Test(timeout = 4000)
    public void testAdditionAndSubtraction() throws Throwable {
        Calculator calculator = new Calculator();

        int firstResult = calculator.add(-5, -3);
        int secondResult = calculator.multiply(firstResult, 2);
        int finalResult = calculator.subtract(secondResult, -4);

        assertEquals(-16, finalResult);
    }
}
