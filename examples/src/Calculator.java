public class Calculator {

    private double memory;
    private int operationCount;

    public Calculator() {
        this.memory = 0.0;
        this.operationCount = 0;
    }

    // ── Arithmetic ────────────────────────────────────────────

    public double add(double a, double b) {
        operationCount++;
        return a + b;
    }

    public double subtract(double a, double b) {
        operationCount++;
        return a - b;
    }

    public double multiply(double a, double b) {
        operationCount++;
        return a * b;
    }

    public double divide(double a, double b) {
        if (b == 0) throw new ArithmeticException("Division by zero");
        operationCount++;
        return a / b;
    }

    public double power(double base, int exponent) {
        if (exponent < 0) throw new IllegalArgumentException("Exponent must be non-negative");
        operationCount++;
        double result = 1.0;
        for (int i = 0; i < exponent; i++) result *= base;
        return result;
    }

    public double sqrt(double value) {
        if (value < 0) throw new IllegalArgumentException("Cannot take sqrt of negative number");
        operationCount++;
        return Math.sqrt(value);
    }

    public double modulo(double a, double b) {
        if (b == 0) throw new ArithmeticException("Modulo by zero");
        operationCount++;
        return a % b;
    }

    // ── Comparison / Classification ───────────────────────────

    public double max(double a, double b) {
        return a >= b ? a : b;
    }

    public double min(double a, double b) {
        return a <= b ? a : b;
    }

    public double abs(double value) {
        return value < 0 ? -value : value;
    }

    public boolean isPositive(double value) {
        return value > 0;
    }

    public boolean isEven(int value) {
        return value % 2 == 0;
    }

    public String classify(double value) {
        if (value < 0) return "negative";
        if (value == 0) return "zero";
        if (value < 10) return "small";
        if (value < 100) return "medium";
        return "large";
    }

    // ── Memory ────────────────────────────────────────────────

    public void memoryStore(double value) {
        this.memory = value;
    }

    public double memoryRecall() {
        return this.memory;
    }

    public void memoryClear() {
        this.memory = 0.0;
    }

    public double memoryAdd(double value) {
        this.memory += value;
        return this.memory;
    }

    // ── Stats ─────────────────────────────────────────────────

    public int getOperationCount() {
        return operationCount;
    }

    public void reset() {
        this.memory = 0.0;
        this.operationCount = 0;
    }
}
