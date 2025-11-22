#include "ExpressionEvaluator.hpp"
#include <iostream>
#include <iomanip>
#include <chrono>
#include <vector>

using namespace expr;

void example_basic_evaluation() {
    std::cout << "\n=== Example 1: Basic Expression Evaluation ===" << std::endl;

    Evaluator eval;

    // Simple arithmetic
    std::cout << "2 + 3 * 4 = " << eval.evaluate("2 + 3 * 4") << std::endl;
    std::cout << "(5 + 3) / 2 = " << eval.evaluate("(5 + 3) / 2") << std::endl;
    std::cout << "10 % 3 = " << eval.evaluate("10 % 3") << std::endl;
    std::cout << "2^8 = " << eval.evaluate("2^8") << std::endl;
    std::cout << "2**10 = " << eval.evaluate("2**10") << std::endl;
}

void example_math_functions() {
    std::cout << "\n=== Example 2: Math Functions ===" << std::endl;

    Evaluator eval;

    std::cout << "sin(3.14159/2) = " << eval.evaluate("sin(3.14159/2)") << std::endl;
    std::cout << "cos(0) = " << eval.evaluate("cos(0)") << std::endl;
    std::cout << "sqrt(16) = " << eval.evaluate("sqrt(16)") << std::endl;
    std::cout << "pow(2, 10) = " << eval.evaluate("pow(2, 10)") << std::endl;
    std::cout << "log(e) = " << eval.evaluate("log(e)") << std::endl;
    std::cout << "abs(-42) = " << eval.evaluate("abs(-42)") << std::endl;
    std::cout << "min(5, 3) = " << eval.evaluate("min(5, 3)") << std::endl;
    std::cout << "max(5, 3) = " << eval.evaluate("max(5, 3)") << std::endl;
    std::cout << "floor(3.7) = " << eval.evaluate("floor(3.7)") << std::endl;
    std::cout << "ceil(3.2) = " << eval.evaluate("ceil(3.2)") << std::endl;
}

void example_variables() {
    std::cout << "\n=== Example 3: Variables ===" << std::endl;

    Evaluator eval;

    // Set variables
    eval.set_variable("x", 10.0);
    eval.set_variable("y", 20.0);
    eval.set_variable("z", 30.0);

    std::cout << "x = " << eval.get_variable("x") << std::endl;
    std::cout << "y = " << eval.get_variable("y") << std::endl;
    std::cout << "z = " << eval.get_variable("z") << std::endl;

    // Use in expressions
    std::cout << "x + y + z = " << eval.evaluate("x + y + z") << std::endl;
    std::cout << "x * (y - z) = " << eval.evaluate("x * (y - z)") << std::endl;
    std::cout << "x^2 + y^2 + z^2 = " << eval.evaluate("x^2 + y^2 + z^2") << std::endl;

    // Update variables
    eval.set_variable("x", 5.0);
    std::cout << "\nAfter setting x = 5:" << std::endl;
    std::cout << "x + y + z = " << eval.evaluate("x + y + z") << std::endl;
}

void example_custom_functions() {
    std::cout << "\n=== Example 4: User-Defined Functions ===" << std::endl;

    Evaluator eval;

    // Register custom functions
    eval.register_function("double", [](double x) {
        return x * 2.0;
    });

    eval.register_function("average", [](double a, double b) {
        return (a + b) / 2.0;
    });

    eval.register_function("cube", [](double x) {
        return x * x * x;
    });

    // Use custom functions
    std::cout << "double(5) = " << eval.evaluate("double(5)") << std::endl;
    std::cout << "average(10, 20) = " << eval.evaluate("average(10, 20)") << std::endl;
    std::cout << "cube(3) = " << eval.evaluate("cube(3)") << std::endl;
    std::cout << "double(average(4, 8)) = " << eval.evaluate("double(average(4, 8))") << std::endl;
}

void example_jit_compilation() {
    std::cout << "\n=== Example 5: JIT Compilation ===" << std::endl;

    Evaluator eval;
    eval.set_variable("x", 0.0);

    // Compile expression once
    auto compiled = eval.compile("x^2 + 2*x + 1");

    std::cout << "Compiled expression: x^2 + 2*x + 1" << std::endl;
    std::cout << "\nEvaluating for different values of x:" << std::endl;

    for (int i = 0; i <= 10; ++i) {
        eval.set_variable("x", static_cast<double>(i));
        double result = compiled();
        std::cout << "  x = " << i << " => " << result << std::endl;
    }
}

void example_optimization() {
    std::cout << "\n=== Example 6: Expression Optimization ===" << std::endl;

    Evaluator eval;

    std::vector<std::string> expressions = {
        "2 + 3 * 4",
        "x * 1 + 0",
        "x * 0 + 5",
        "x / 1",
        "x^1",
        "x^0",
        "sin(0) + cos(0)",
        "(a + b) * 2 + (a + b) * 3"
    };

    for (const auto& expr_str : expressions) {
        std::string optimized = eval.optimize(expr_str);
        std::cout << expr_str << " => " << optimized << std::endl;
    }
}

void example_complex_expressions() {
    std::cout << "\n=== Example 7: Complex Expressions ===" << std::endl;

    Evaluator eval;

    // Physics: kinetic energy
    eval.set_variable("m", 10.0);  // mass
    eval.set_variable("v", 5.0);   // velocity
    double ke = eval.evaluate("0.5 * m * v^2");
    std::cout << "Kinetic Energy (m=10, v=5): " << ke << " J" << std::endl;

    // Financial: compound interest
    eval.set_variable("P", 1000.0);  // principal
    eval.set_variable("r", 0.05);    // rate
    eval.set_variable("n", 12.0);    // compounds per year
    eval.set_variable("t", 5.0);     // time in years
    double amount = eval.evaluate("P * (1 + r/n)^(n*t)");
    std::cout << "Compound Interest (P=1000, r=0.05, n=12, t=5): $" << amount << std::endl;

    // Distance formula
    eval.set_variable("x1", 0.0);
    eval.set_variable("y1", 0.0);
    eval.set_variable("x2", 3.0);
    eval.set_variable("y2", 4.0);
    double distance = eval.evaluate("sqrt((x2-x1)^2 + (y2-y1)^2)");
    std::cout << "Distance from (0,0) to (3,4): " << distance << std::endl;

    // Quadratic formula: (-b ± sqrt(b^2 - 4ac)) / 2a
    eval.set_variable("a", 1.0);
    eval.set_variable("b", -5.0);
    eval.set_variable("c", 6.0);
    double root1 = eval.evaluate("(-b + sqrt(b^2 - 4*a*c)) / (2*a)");
    double root2 = eval.evaluate("(-b - sqrt(b^2 - 4*a*c)) / (2*a)");
    std::cout << "Quadratic roots (a=1, b=-5, c=6): " << root1 << ", " << root2 << std::endl;
}

void example_comparison_operators() {
    std::cout << "\n=== Example 8: Comparison Operators ===" << std::endl;

    Evaluator eval;

    std::cout << "5 == 5: " << eval.evaluate("5 == 5") << std::endl;
    std::cout << "5 != 3: " << eval.evaluate("5 != 3") << std::endl;
    std::cout << "3 < 5: " << eval.evaluate("3 < 5") << std::endl;
    std::cout << "5 > 3: " << eval.evaluate("5 > 3") << std::endl;
    std::cout << "5 <= 5: " << eval.evaluate("5 <= 5") << std::endl;
    std::cout << "5 >= 3: " << eval.evaluate("5 >= 3") << std::endl;
}

void example_logical_operators() {
    std::cout << "\n=== Example 9: Logical Operators ===" << std::endl;

    Evaluator eval;

    std::cout << "1 && 1: " << eval.evaluate("1 && 1") << std::endl;
    std::cout << "1 && 0: " << eval.evaluate("1 && 0") << std::endl;
    std::cout << "1 || 0: " << eval.evaluate("1 || 0") << std::endl;
    std::cout << "0 || 0: " << eval.evaluate("0 || 0") << std::endl;
    std::cout << "!0: " << eval.evaluate("!0") << std::endl;
    std::cout << "!1: " << eval.evaluate("!1") << std::endl;

    // Combined with comparisons
    std::cout << "(5 > 3) && (2 < 4): " << eval.evaluate("(5 > 3) && (2 < 4)") << std::endl;
    std::cout << "(5 < 3) || (2 < 4): " << eval.evaluate("(5 < 3) || (2 < 4)") << std::endl;
}

void example_array_operations() {
    std::cout << "\n=== Example 10: Array Operations ===" << std::endl;

    Evaluator eval;

    std::vector<double> x_values = {1, 2, 3, 4, 5};
    std::vector<double> results;

    // Compile expression once
    auto compiled = eval.compile("x^2 + 2*x + 1");

    std::cout << "Evaluating x^2 + 2*x + 1 for x in [1, 2, 3, 4, 5]:" << std::endl;
    std::cout << "Results: [ ";

    for (double x : x_values) {
        eval.set_variable("x", x);
        double result = compiled();
        results.push_back(result);
        std::cout << result << " ";
    }

    std::cout << "]" << std::endl;
}

void example_error_handling() {
    std::cout << "\n=== Example 11: Error Handling ===" << std::endl;

    Evaluator eval;

    // Parse error
    try {
        eval.evaluate("2 + * 3");
    } catch (const ParseError& e) {
        std::cout << "Parse error caught: " << e.what() << std::endl;
    }

    // Undefined variable
    try {
        eval.evaluate("x + 5");
    } catch (const EvaluationError& e) {
        std::cout << "Evaluation error caught: " << e.what() << std::endl;
    }

    // Division by zero
    try {
        eval.evaluate("10 / 0");
    } catch (const EvaluationError& e) {
        std::cout << "Division by zero caught: " << e.what() << std::endl;
    }

    // Unknown function
    try {
        eval.evaluate("unknown_func(5)");
    } catch (const EvaluationError& e) {
        std::cout << "Unknown function caught: " << e.what() << std::endl;
    }
}

void benchmark_performance() {
    std::cout << "\n=== Performance Benchmark ===" << std::endl;

    Evaluator eval;
    eval.set_variable("x", 0.0);

    const int iterations = 100000;
    std::string expression = "x^2 + 2*x + 1";

    // Benchmark 1: Parse and evaluate each time
    auto start1 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        eval.set_variable("x", static_cast<double>(i % 100));
        eval.evaluate(expression);
    }
    auto end1 = std::chrono::high_resolution_clock::now();
    auto duration1 = std::chrono::duration_cast<std::chrono::milliseconds>(end1 - start1);

    // Benchmark 2: Parse once, evaluate AST
    auto parsed = eval.parse(expression);
    auto start2 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        eval.set_variable("x", static_cast<double>(i % 100));
        std::map<std::string, double> vars = {{"x", static_cast<double>(i % 100)}};
        std::map<std::string, std::function<double(const std::vector<double>&)>> funcs;
        parsed->evaluate(vars, funcs);
    }
    auto end2 = std::chrono::high_resolution_clock::now();
    auto duration2 = std::chrono::duration_cast<std::chrono::milliseconds>(end2 - start2);

    // Benchmark 3: Compiled/optimized
    auto compiled = eval.compile(expression);
    auto start3 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        eval.set_variable("x", static_cast<double>(i % 100));
        compiled();
    }
    auto end3 = std::chrono::high_resolution_clock::now();
    auto duration3 = std::chrono::duration_cast<std::chrono::milliseconds>(end3 - start3);

    std::cout << "Expression: " << expression << std::endl;
    std::cout << "Iterations: " << iterations << std::endl;
    std::cout << "\nResults:" << std::endl;
    std::cout << "  Parse each time:     " << std::setw(6) << duration1.count() << " ms (1.00x)" << std::endl;
    std::cout << "  Cached AST:          " << std::setw(6) << duration2.count() << " ms ("
              << std::fixed << std::setprecision(2) << static_cast<double>(duration1.count()) / duration2.count()
              << "x speedup)" << std::endl;
    std::cout << "  Compiled/Optimized:  " << std::setw(6) << duration3.count() << " ms ("
              << std::fixed << std::setprecision(2) << static_cast<double>(duration1.count()) / duration3.count()
              << "x speedup)" << std::endl;
}

void example_ast_inspection() {
    std::cout << "\n=== Example 12: AST Inspection ===" << std::endl;

    Evaluator eval;

    std::vector<std::string> expressions = {
        "2 + 3",
        "x * y",
        "sin(x) + cos(y)",
        "a^2 + b^2",
        "(x + y) * (x - y)"
    };

    for (const auto& expr_str : expressions) {
        auto expr = eval.parse(expr_str);
        std::cout << "Expression: " << expr_str << std::endl;
        std::cout << "AST string: " << expr->to_string() << std::endl;
        std::cout << std::endl;
    }
}

void example_constants() {
    std::cout << "\n=== Example 13: Mathematical Constants ===" << std::endl;

    Evaluator eval;

    std::cout << "pi = " << eval.evaluate("pi") << std::endl;
    std::cout << "PI = " << eval.evaluate("PI") << std::endl;
    std::cout << "e = " << eval.evaluate("e") << std::endl;
    std::cout << "E = " << eval.evaluate("E") << std::endl;
    std::cout << "2 * pi = " << eval.evaluate("2 * pi") << std::endl;
    std::cout << "e^2 = " << eval.evaluate("e^2") << std::endl;
    std::cout << "log(e) = " << eval.evaluate("log(e)") << std::endl;
    std::cout << "sin(pi/2) = " << eval.evaluate("sin(pi/2)") << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "   ExpressionEvaluator - Examples      " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        example_basic_evaluation();
        example_math_functions();
        example_variables();
        example_custom_functions();
        example_jit_compilation();
        example_optimization();
        example_complex_expressions();
        example_comparison_operators();
        example_logical_operators();
        example_array_operations();
        example_error_handling();
        benchmark_performance();
        example_ast_inspection();
        example_constants();

        std::cout << "\n========================================" << std::endl;
        std::cout << "   All examples completed successfully  " << std::endl;
        std::cout << "========================================" << std::endl;

    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
