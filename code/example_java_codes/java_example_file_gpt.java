import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;

public class X9yZ {

    public double f1(int a) {
        if (a >= 65) {
            return 0.2;
        } else {
            return 0.0;
        }
    }

    @Test
    public void t1() {
        int a1 = 70;
        double b1 = f1(a1);
        assertEquals(0.2, b1);
    }

    @Test
    public void t2() {
        int xx = 30;
        double yy = f1(xx);
        assertEquals(0.0, yy);
    }

    @Test
    public void t3() {
        int z = 65;
        double zz = f1(z);
        assertEquals(0.2, zz);
    }

    @Test
    public void t4() {
        int p = 64;
        double q = f1(p);
        assertEquals(0.0, q);
    }
}
