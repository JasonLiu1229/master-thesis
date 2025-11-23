import static org.junit.Assert.*;
import org.junit.Test;

public class BankAccount_RandoopTest {

    @Test
    public void test1() throws Throwable {

        BankAccount acc0 = new BankAccount(50.0);
        double bal0 = acc0.getBalance();
        assertTrue(bal0 == 50.0);

        acc0.deposit(25.0);
        double bal1 = acc0.getBalance();
        assertTrue(bal1 == 75.0);

        acc0.withdraw(30.0);
        double bal2 = acc0.getBalance();
        assertTrue(bal2 == 45.0);
    }

    @Test
    public void test2() throws Throwable {

        BankAccount acc1 = new BankAccount(0.0);

        // Invalid withdrawal: should throw IllegalStateException
        try {
            acc1.withdraw(10.0);
            fail("Expected IllegalStateException");
        } catch (IllegalStateException e) {
            // expected
        }

        double bal = acc1.getBalance();
        assertTrue(bal == 0.0);

        // Valid deposit
        acc1.deposit(100.0);
        double bal2 = acc1.getBalance();
        assertTrue(bal2 == 100.0);
    }

    @Test
    public void test3() throws Throwable {

        // Invalid negative balance initialization
        try {
            new BankAccount(-5.0);
            fail("Expected IllegalArgumentException");
        } catch (IllegalArgumentException e) {
            // expected
        }

        BankAccount acc2 = new BankAccount(10.0);

        // Negative deposit should be rejected
        try {
            acc2.deposit(-1.0);
            fail("Expected IllegalArgumentException");
        } catch (IllegalArgumentException e) {
            // expected
        }

        // Negative withdrawal should be rejected
        try {
            acc2.withdraw(-2.0);
            fail("Expected IllegalArgumentException");
        } catch (IllegalArgumentException e) {
            // expected
        }

        double bal3 = acc2.getBalance();
        assertTrue(bal3 == 10.0);
    }
}
