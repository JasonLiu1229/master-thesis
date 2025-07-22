import org.junit.Test;
import static org.junit.Assert.*;
import java.util.List;
import java.util.ArrayList;

public class UselessIdentifierTest {

    // Function with reasonable names (what we're testing)
    public static int calculateDiscount(int price, int age) {
        if (age >= 65) {
            return (int)(price * 0.8); // 20% discount
        }
        return price;
    }

    // Tests with terrible meaningless identifiers
    @Test
    public void test_var1() {
        int var1 = 10000;
        int var2 = 70;
        int result_var = calculateDiscount(var1, var2);
        assertEquals(8000, result_var);
    }

    @Test
    public void check_value2() {
        int value_a = 5000;
        int value_b = 40;
        int output_val = calculateDiscount(value_a, value_b);
        assertEquals(5000, output_val);
    }

    @Test
    public void test_case3() {
        List<String> list1 = new ArrayList<>();
        list1.add("test");
        list1.add("items");
        
        int param1 = 2000;
        int param2 = 65;
        int return_value = calculateDiscount(param1, param2);
        
        assertFalse(list1.isEmpty());
        assertEquals(1600, return_value);
    }

    @Test
    public void verify_test4() {
        int x = 3000;
        int y = 20;
        int z = calculateDiscount(x, y);
        
        String str_var = "discount";
        assertTrue(str_var.length() > 0);
        assertEquals(3000, z);
    }

    @Test
    public void test_discount_calculation_but_with_bad_vars() {
        int input_data_1 = 7500;
        int input_data_2 = 67;
        int computed_result = calculateDiscount(input_data_1, input_data_2);
        
        assertEquals(6000, computed_result);
    }
}