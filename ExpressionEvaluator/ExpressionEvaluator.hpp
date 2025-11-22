#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <map>
#include <memory>
#include <functional>
#include <cmath>
#include <stdexcept>
#include <sstream>
#include <cctype>
#include <variant>

namespace expr {

// Exception types
class ParseError : public std::runtime_error {
public:
    explicit ParseError(const std::string& msg) : std::runtime_error(msg) {}
};

class EvaluationError : public std::runtime_error {
public:
    explicit EvaluationError(const std::string& msg) : std::runtime_error(msg) {}
};

// Token types
enum class TokenType {
    Number,
    Identifier,
    Plus,
    Minus,
    Star,
    Slash,
    Percent,
    Caret,
    LParen,
    RParen,
    Comma,
    Equal,
    NotEqual,
    Less,
    Greater,
    LessEqual,
    GreaterEqual,
    And,
    Or,
    Not,
    End
};

// Token structure
struct Token {
    TokenType type;
    std::string value;
    double number_value = 0.0;

    Token(TokenType t, std::string v = "", double n = 0.0)
        : type(t), value(std::move(v)), number_value(n) {}
};

// Tokenizer
class Tokenizer {
public:
    explicit Tokenizer(std::string_view input) : input_(input), pos_(0) {}

    std::vector<Token> tokenize() {
        std::vector<Token> tokens;

        while (pos_ < input_.size()) {
            skip_whitespace();
            if (pos_ >= input_.size()) break;

            char ch = input_[pos_];

            // Numbers
            if (std::isdigit(ch) || ch == '.') {
                tokens.push_back(read_number());
            }
            // Identifiers and keywords
            else if (std::isalpha(ch) || ch == '_') {
                tokens.push_back(read_identifier());
            }
            // Operators
            else if (ch == '+') {
                tokens.emplace_back(TokenType::Plus, "+");
                ++pos_;
            }
            else if (ch == '-') {
                tokens.emplace_back(TokenType::Minus, "-");
                ++pos_;
            }
            else if (ch == '*') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '*') {
                    tokens.emplace_back(TokenType::Caret, "**");
                    pos_ += 2;
                } else {
                    tokens.emplace_back(TokenType::Star, "*");
                    ++pos_;
                }
            }
            else if (ch == '/') {
                tokens.emplace_back(TokenType::Slash, "/");
                ++pos_;
            }
            else if (ch == '%') {
                tokens.emplace_back(TokenType::Percent, "%");
                ++pos_;
            }
            else if (ch == '^') {
                tokens.emplace_back(TokenType::Caret, "^");
                ++pos_;
            }
            else if (ch == '(') {
                tokens.emplace_back(TokenType::LParen, "(");
                ++pos_;
            }
            else if (ch == ')') {
                tokens.emplace_back(TokenType::RParen, ")");
                ++pos_;
            }
            else if (ch == ',') {
                tokens.emplace_back(TokenType::Comma, ",");
                ++pos_;
            }
            else if (ch == '=') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '=') {
                    tokens.emplace_back(TokenType::Equal, "==");
                    pos_ += 2;
                } else {
                    throw ParseError("Unexpected '=' (use '==' for comparison)");
                }
            }
            else if (ch == '!') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '=') {
                    tokens.emplace_back(TokenType::NotEqual, "!=");
                    pos_ += 2;
                } else {
                    tokens.emplace_back(TokenType::Not, "!");
                    ++pos_;
                }
            }
            else if (ch == '<') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '=') {
                    tokens.emplace_back(TokenType::LessEqual, "<=");
                    pos_ += 2;
                } else {
                    tokens.emplace_back(TokenType::Less, "<");
                    ++pos_;
                }
            }
            else if (ch == '>') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '=') {
                    tokens.emplace_back(TokenType::GreaterEqual, ">=");
                    pos_ += 2;
                } else {
                    tokens.emplace_back(TokenType::Greater, ">");
                    ++pos_;
                }
            }
            else if (ch == '&') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '&') {
                    tokens.emplace_back(TokenType::And, "&&");
                    pos_ += 2;
                } else {
                    throw ParseError("Unexpected '&' (use '&&' for logical AND)");
                }
            }
            else if (ch == '|') {
                if (pos_ + 1 < input_.size() && input_[pos_ + 1] == '|') {
                    tokens.emplace_back(TokenType::Or, "||");
                    pos_ += 2;
                } else {
                    throw ParseError("Unexpected '|' (use '||' for logical OR)");
                }
            }
            else {
                throw ParseError("Unexpected character: " + std::string(1, ch));
            }
        }

        tokens.emplace_back(TokenType::End);
        return tokens;
    }

private:
    void skip_whitespace() {
        while (pos_ < input_.size() && std::isspace(input_[pos_])) {
            ++pos_;
        }
    }

    Token read_number() {
        size_t start = pos_;
        bool has_dot = false;

        while (pos_ < input_.size()) {
            char ch = input_[pos_];
            if (std::isdigit(ch)) {
                ++pos_;
            } else if (ch == '.' && !has_dot) {
                has_dot = true;
                ++pos_;
            } else {
                break;
            }
        }

        std::string num_str(input_.substr(start, pos_ - start));
        double value = std::stod(num_str);
        return Token(TokenType::Number, num_str, value);
    }

    Token read_identifier() {
        size_t start = pos_;

        while (pos_ < input_.size() &&
               (std::isalnum(input_[pos_]) || input_[pos_] == '_')) {
            ++pos_;
        }

        std::string id(input_.substr(start, pos_ - start));

        // Check for keywords
        if (id == "and") {
            return Token(TokenType::And, id);
        } else if (id == "or") {
            return Token(TokenType::Or, id);
        } else if (id == "not") {
            return Token(TokenType::Not, id);
        }

        return Token(TokenType::Identifier, id);
    }

    std::string_view input_;
    size_t pos_;
};

// Forward declarations
class Expression;
using ExprPtr = std::shared_ptr<Expression>;

// Expression base class
class Expression {
public:
    virtual ~Expression() = default;
    virtual double evaluate(const std::map<std::string, double>& variables,
                          const std::map<std::string, std::function<double(const std::vector<double>&)>>& functions) const = 0;
    virtual std::string to_string() const = 0;
    virtual ExprPtr optimize() const = 0;
    virtual ExprPtr clone() const = 0;
};

// Constant expression
class ConstantExpr : public Expression {
public:
    explicit ConstantExpr(double value) : value_(value) {}

    double evaluate(const std::map<std::string, double>&,
                   const std::map<std::string, std::function<double(const std::vector<double>&)>>&) const override {
        return value_;
    }

    std::string to_string() const override {
        return std::to_string(value_);
    }

    ExprPtr optimize() const override {
        return std::make_shared<ConstantExpr>(value_);
    }

    ExprPtr clone() const override {
        return std::make_shared<ConstantExpr>(value_);
    }

    double value() const { return value_; }

private:
    double value_;
};

// Variable expression
class VariableExpr : public Expression {
public:
    explicit VariableExpr(std::string name) : name_(std::move(name)) {}

    double evaluate(const std::map<std::string, double>& variables,
                   const std::map<std::string, std::function<double(const std::vector<double>&)>>&) const override {
        auto it = variables.find(name_);
        if (it == variables.end()) {
            throw EvaluationError("Undefined variable: " + name_);
        }
        return it->second;
    }

    std::string to_string() const override {
        return name_;
    }

    ExprPtr optimize() const override {
        return std::make_shared<VariableExpr>(name_);
    }

    ExprPtr clone() const override {
        return std::make_shared<VariableExpr>(name_);
    }

    const std::string& name() const { return name_; }

private:
    std::string name_;
};

// Binary operation expression
class BinaryOpExpr : public Expression {
public:
    enum class Op { Add, Sub, Mul, Div, Mod, Pow, Equal, NotEqual, Less, Greater, LessEqual, GreaterEqual, And, Or };

    BinaryOpExpr(Op op, ExprPtr left, ExprPtr right)
        : op_(op), left_(std::move(left)), right_(std::move(right)) {}

    double evaluate(const std::map<std::string, double>& variables,
                   const std::map<std::string, std::function<double(const std::vector<double>&)>>& functions) const override {
        double lval = left_->evaluate(variables, functions);
        double rval = right_->evaluate(variables, functions);

        switch (op_) {
            case Op::Add: return lval + rval;
            case Op::Sub: return lval - rval;
            case Op::Mul: return lval * rval;
            case Op::Div:
                if (rval == 0.0) throw EvaluationError("Division by zero");
                return lval / rval;
            case Op::Mod: return std::fmod(lval, rval);
            case Op::Pow: return std::pow(lval, rval);
            case Op::Equal: return lval == rval ? 1.0 : 0.0;
            case Op::NotEqual: return lval != rval ? 1.0 : 0.0;
            case Op::Less: return lval < rval ? 1.0 : 0.0;
            case Op::Greater: return lval > rval ? 1.0 : 0.0;
            case Op::LessEqual: return lval <= rval ? 1.0 : 0.0;
            case Op::GreaterEqual: return lval >= rval ? 1.0 : 0.0;
            case Op::And: return (lval != 0.0 && rval != 0.0) ? 1.0 : 0.0;
            case Op::Or: return (lval != 0.0 || rval != 0.0) ? 1.0 : 0.0;
        }
        return 0.0;
    }

    std::string to_string() const override {
        std::string op_str;
        switch (op_) {
            case Op::Add: op_str = "+"; break;
            case Op::Sub: op_str = "-"; break;
            case Op::Mul: op_str = "*"; break;
            case Op::Div: op_str = "/"; break;
            case Op::Mod: op_str = "%"; break;
            case Op::Pow: op_str = "^"; break;
            case Op::Equal: op_str = "=="; break;
            case Op::NotEqual: op_str = "!="; break;
            case Op::Less: op_str = "<"; break;
            case Op::Greater: op_str = ">"; break;
            case Op::LessEqual: op_str = "<="; break;
            case Op::GreaterEqual: op_str = ">="; break;
            case Op::And: op_str = "&&"; break;
            case Op::Or: op_str = "||"; break;
        }
        return "(" + left_->to_string() + " " + op_str + " " + right_->to_string() + ")";
    }

    ExprPtr optimize() const override {
        auto opt_left = left_->optimize();
        auto opt_right = right_->optimize();

        // Constant folding
        auto left_const = dynamic_cast<ConstantExpr*>(opt_left.get());
        auto right_const = dynamic_cast<ConstantExpr*>(opt_right.get());

        if (left_const && right_const) {
            std::map<std::string, double> empty_vars;
            std::map<std::string, std::function<double(const std::vector<double>&)>> empty_funcs;
            double result = BinaryOpExpr(op_, opt_left, opt_right).evaluate(empty_vars, empty_funcs);
            return std::make_shared<ConstantExpr>(result);
        }

        // Algebraic simplifications
        if (right_const) {
            double rval = right_const->value();
            switch (op_) {
                case Op::Add:
                    if (rval == 0.0) return opt_left;  // x + 0 = x
                    break;
                case Op::Sub:
                    if (rval == 0.0) return opt_left;  // x - 0 = x
                    break;
                case Op::Mul:
                    if (rval == 0.0) return std::make_shared<ConstantExpr>(0.0);  // x * 0 = 0
                    if (rval == 1.0) return opt_left;  // x * 1 = x
                    break;
                case Op::Div:
                    if (rval == 1.0) return opt_left;  // x / 1 = x
                    break;
                case Op::Pow:
                    if (rval == 0.0) return std::make_shared<ConstantExpr>(1.0);  // x^0 = 1
                    if (rval == 1.0) return opt_left;  // x^1 = x
                    break;
                default:
                    break;
            }
        }

        if (left_const) {
            double lval = left_const->value();
            switch (op_) {
                case Op::Add:
                    if (lval == 0.0) return opt_right;  // 0 + x = x
                    break;
                case Op::Mul:
                    if (lval == 0.0) return std::make_shared<ConstantExpr>(0.0);  // 0 * x = 0
                    if (lval == 1.0) return opt_right;  // 1 * x = x
                    break;
                default:
                    break;
            }
        }

        return std::make_shared<BinaryOpExpr>(op_, opt_left, opt_right);
    }

    ExprPtr clone() const override {
        return std::make_shared<BinaryOpExpr>(op_, left_->clone(), right_->clone());
    }

private:
    Op op_;
    ExprPtr left_;
    ExprPtr right_;
};

// Unary operation expression
class UnaryOpExpr : public Expression {
public:
    enum class Op { Neg, Not };

    UnaryOpExpr(Op op, ExprPtr operand)
        : op_(op), operand_(std::move(operand)) {}

    double evaluate(const std::map<std::string, double>& variables,
                   const std::map<std::string, std::function<double(const std::vector<double>&)>>& functions) const override {
        double val = operand_->evaluate(variables, functions);
        switch (op_) {
            case Op::Neg: return -val;
            case Op::Not: return val == 0.0 ? 1.0 : 0.0;
        }
        return 0.0;
    }

    std::string to_string() const override {
        std::string op_str = (op_ == Op::Neg) ? "-" : "!";
        return op_str + operand_->to_string();
    }

    ExprPtr optimize() const override {
        auto opt_operand = operand_->optimize();

        // Constant folding
        if (auto const_expr = dynamic_cast<ConstantExpr*>(opt_operand.get())) {
            std::map<std::string, double> empty_vars;
            std::map<std::string, std::function<double(const std::vector<double>&)>> empty_funcs;
            double result = UnaryOpExpr(op_, opt_operand).evaluate(empty_vars, empty_funcs);
            return std::make_shared<ConstantExpr>(result);
        }

        return std::make_shared<UnaryOpExpr>(op_, opt_operand);
    }

    ExprPtr clone() const override {
        return std::make_shared<UnaryOpExpr>(op_, operand_->clone());
    }

private:
    Op op_;
    ExprPtr operand_;
};

// Function call expression
class FunctionCallExpr : public Expression {
public:
    FunctionCallExpr(std::string name, std::vector<ExprPtr> args)
        : name_(std::move(name)), args_(std::move(args)) {}

    double evaluate(const std::map<std::string, double>& variables,
                   const std::map<std::string, std::function<double(const std::vector<double>&)>>& functions) const override {
        // Built-in functions
        std::vector<double> arg_values;
        for (const auto& arg : args_) {
            arg_values.push_back(arg->evaluate(variables, functions));
        }

        // Try custom functions first
        auto it = functions.find(name_);
        if (it != functions.end()) {
            return it->second(arg_values);
        }

        // Built-in math functions
        if (name_ == "sin" && arg_values.size() == 1) return std::sin(arg_values[0]);
        if (name_ == "cos" && arg_values.size() == 1) return std::cos(arg_values[0]);
        if (name_ == "tan" && arg_values.size() == 1) return std::tan(arg_values[0]);
        if (name_ == "asin" && arg_values.size() == 1) return std::asin(arg_values[0]);
        if (name_ == "acos" && arg_values.size() == 1) return std::acos(arg_values[0]);
        if (name_ == "atan" && arg_values.size() == 1) return std::atan(arg_values[0]);
        if (name_ == "sinh" && arg_values.size() == 1) return std::sinh(arg_values[0]);
        if (name_ == "cosh" && arg_values.size() == 1) return std::cosh(arg_values[0]);
        if (name_ == "tanh" && arg_values.size() == 1) return std::tanh(arg_values[0]);
        if (name_ == "sqrt" && arg_values.size() == 1) return std::sqrt(arg_values[0]);
        if (name_ == "cbrt" && arg_values.size() == 1) return std::cbrt(arg_values[0]);
        if (name_ == "exp" && arg_values.size() == 1) return std::exp(arg_values[0]);
        if (name_ == "log" && arg_values.size() == 1) return std::log(arg_values[0]);
        if (name_ == "log10" && arg_values.size() == 1) return std::log10(arg_values[0]);
        if (name_ == "abs" && arg_values.size() == 1) return std::abs(arg_values[0]);
        if (name_ == "floor" && arg_values.size() == 1) return std::floor(arg_values[0]);
        if (name_ == "ceil" && arg_values.size() == 1) return std::ceil(arg_values[0]);
        if (name_ == "round" && arg_values.size() == 1) return std::round(arg_values[0]);
        if (name_ == "pow" && arg_values.size() == 2) return std::pow(arg_values[0], arg_values[1]);
        if (name_ == "min" && arg_values.size() == 2) return std::min(arg_values[0], arg_values[1]);
        if (name_ == "max" && arg_values.size() == 2) return std::max(arg_values[0], arg_values[1]);

        throw EvaluationError("Unknown function: " + name_);
    }

    std::string to_string() const override {
        std::string result = name_ + "(";
        for (size_t i = 0; i < args_.size(); ++i) {
            if (i > 0) result += ", ";
            result += args_[i]->to_string();
        }
        result += ")";
        return result;
    }

    ExprPtr optimize() const override {
        std::vector<ExprPtr> opt_args;
        bool all_const = true;

        for (const auto& arg : args_) {
            auto opt_arg = arg->optimize();
            opt_args.push_back(opt_arg);
            if (!dynamic_cast<ConstantExpr*>(opt_arg.get())) {
                all_const = false;
            }
        }

        // Constant folding for functions
        if (all_const) {
            std::map<std::string, double> empty_vars;
            std::map<std::string, std::function<double(const std::vector<double>&)>> empty_funcs;
            try {
                double result = FunctionCallExpr(name_, opt_args).evaluate(empty_vars, empty_funcs);
                return std::make_shared<ConstantExpr>(result);
            } catch (...) {
                // If evaluation fails, return non-optimized version
            }
        }

        return std::make_shared<FunctionCallExpr>(name_, opt_args);
    }

    ExprPtr clone() const override {
        std::vector<ExprPtr> cloned_args;
        for (const auto& arg : args_) {
            cloned_args.push_back(arg->clone());
        }
        return std::make_shared<FunctionCallExpr>(name_, cloned_args);
    }

private:
    std::string name_;
    std::vector<ExprPtr> args_;
};

// Parser
class Parser {
public:
    explicit Parser(std::vector<Token> tokens)
        : tokens_(std::move(tokens)), pos_(0) {}

    ExprPtr parse() {
        auto expr = parse_or();
        if (current().type != TokenType::End) {
            throw ParseError("Unexpected token after expression");
        }
        return expr;
    }

private:
    ExprPtr parse_or() {
        auto left = parse_and();

        while (current().type == TokenType::Or) {
            advance();
            auto right = parse_and();
            left = std::make_shared<BinaryOpExpr>(BinaryOpExpr::Op::Or, left, right);
        }

        return left;
    }

    ExprPtr parse_and() {
        auto left = parse_comparison();

        while (current().type == TokenType::And) {
            advance();
            auto right = parse_comparison();
            left = std::make_shared<BinaryOpExpr>(BinaryOpExpr::Op::And, left, right);
        }

        return left;
    }

    ExprPtr parse_comparison() {
        auto left = parse_additive();

        while (true) {
            BinaryOpExpr::Op op;
            if (current().type == TokenType::Equal) {
                op = BinaryOpExpr::Op::Equal;
            } else if (current().type == TokenType::NotEqual) {
                op = BinaryOpExpr::Op::NotEqual;
            } else if (current().type == TokenType::Less) {
                op = BinaryOpExpr::Op::Less;
            } else if (current().type == TokenType::Greater) {
                op = BinaryOpExpr::Op::Greater;
            } else if (current().type == TokenType::LessEqual) {
                op = BinaryOpExpr::Op::LessEqual;
            } else if (current().type == TokenType::GreaterEqual) {
                op = BinaryOpExpr::Op::GreaterEqual;
            } else {
                break;
            }

            advance();
            auto right = parse_additive();
            left = std::make_shared<BinaryOpExpr>(op, left, right);
        }

        return left;
    }

    ExprPtr parse_additive() {
        auto left = parse_multiplicative();

        while (current().type == TokenType::Plus || current().type == TokenType::Minus) {
            auto op = current().type == TokenType::Plus ? BinaryOpExpr::Op::Add : BinaryOpExpr::Op::Sub;
            advance();
            auto right = parse_multiplicative();
            left = std::make_shared<BinaryOpExpr>(op, left, right);
        }

        return left;
    }

    ExprPtr parse_multiplicative() {
        auto left = parse_power();

        while (current().type == TokenType::Star ||
               current().type == TokenType::Slash ||
               current().type == TokenType::Percent) {
            BinaryOpExpr::Op op;
            if (current().type == TokenType::Star) {
                op = BinaryOpExpr::Op::Mul;
            } else if (current().type == TokenType::Slash) {
                op = BinaryOpExpr::Op::Div;
            } else {
                op = BinaryOpExpr::Op::Mod;
            }
            advance();
            auto right = parse_power();
            left = std::make_shared<BinaryOpExpr>(op, left, right);
        }

        return left;
    }

    ExprPtr parse_power() {
        auto left = parse_unary();

        if (current().type == TokenType::Caret) {
            advance();
            auto right = parse_power();  // Right associative
            return std::make_shared<BinaryOpExpr>(BinaryOpExpr::Op::Pow, left, right);
        }

        return left;
    }

    ExprPtr parse_unary() {
        if (current().type == TokenType::Minus) {
            advance();
            return std::make_shared<UnaryOpExpr>(UnaryOpExpr::Op::Neg, parse_unary());
        }

        if (current().type == TokenType::Not) {
            advance();
            return std::make_shared<UnaryOpExpr>(UnaryOpExpr::Op::Not, parse_unary());
        }

        return parse_primary();
    }

    ExprPtr parse_primary() {
        // Numbers
        if (current().type == TokenType::Number) {
            double value = current().number_value;
            advance();
            return std::make_shared<ConstantExpr>(value);
        }

        // Identifiers (variables, constants, or functions)
        if (current().type == TokenType::Identifier) {
            std::string name = current().value;
            advance();

            // Constants
            if (name == "pi" || name == "PI") {
                return std::make_shared<ConstantExpr>(3.14159265358979323846);
            }
            if (name == "e" || name == "E") {
                return std::make_shared<ConstantExpr>(2.71828182845904523536);
            }

            // Function call
            if (current().type == TokenType::LParen) {
                advance();
                std::vector<ExprPtr> args;

                if (current().type != TokenType::RParen) {
                    args.push_back(parse_or());
                    while (current().type == TokenType::Comma) {
                        advance();
                        args.push_back(parse_or());
                    }
                }

                if (current().type != TokenType::RParen) {
                    throw ParseError("Expected ')' after function arguments");
                }
                advance();

                return std::make_shared<FunctionCallExpr>(name, args);
            }

            // Variable
            return std::make_shared<VariableExpr>(name);
        }

        // Parenthesized expression
        if (current().type == TokenType::LParen) {
            advance();
            auto expr = parse_or();
            if (current().type != TokenType::RParen) {
                throw ParseError("Expected ')'");
            }
            advance();
            return expr;
        }

        throw ParseError("Unexpected token: " + current().value);
    }

    const Token& current() const {
        return tokens_[pos_];
    }

    void advance() {
        if (pos_ < tokens_.size() - 1) {
            ++pos_;
        }
    }

    std::vector<Token> tokens_;
    size_t pos_;
};

// Bytecode instruction set
enum class OpCode {
    Push,       // Push constant
    Load,       // Load variable
    Add,
    Sub,
    Mul,
    Div,
    Mod,
    Pow,
    Neg,
    Call,       // Call function
    Equal,
    NotEqual,
    Less,
    Greater,
    LessEqual,
    GreaterEqual,
    And,
    Or,
    Not
};

struct Instruction {
    OpCode opcode;
    double value = 0.0;
    std::string name;
    size_t arg_count = 0;
};

// Bytecode compiler
class BytecodeCompiler {
public:
    std::vector<Instruction> compile(const ExprPtr& expr) {
        instructions_.clear();
        compile_expr(expr);
        return instructions_;
    }

private:
    void compile_expr(const ExprPtr& expr) {
        if (auto const_expr = dynamic_cast<ConstantExpr*>(expr.get())) {
            instructions_.push_back({OpCode::Push, const_expr->value()});
        }
        else if (auto var_expr = dynamic_cast<VariableExpr*>(expr.get())) {
            instructions_.push_back({OpCode::Load, 0.0, var_expr->name()});
        }
        else if (auto bin_expr = dynamic_cast<BinaryOpExpr*>(expr.get())) {
            compile_binary(bin_expr);
        }
        else if (auto unary_expr = dynamic_cast<UnaryOpExpr*>(expr.get())) {
            compile_unary(unary_expr);
        }
        else if (auto func_expr = dynamic_cast<FunctionCallExpr*>(expr.get())) {
            compile_function(func_expr);
        }
    }

    void compile_binary(BinaryOpExpr* expr) {
        // This is a simplified approach - would need more sophisticated handling in production
        auto bin_op = const_cast<BinaryOpExpr*>(expr);

        // Compile operands (would need to access private members in real implementation)
        // For now, we'll throw - this is a placeholder
        throw std::runtime_error("Bytecode compilation not fully implemented");
    }

    void compile_unary(UnaryOpExpr* expr) {
        throw std::runtime_error("Bytecode compilation not fully implemented");
    }

    void compile_function(FunctionCallExpr* expr) {
        throw std::runtime_error("Bytecode compilation not fully implemented");
    }

    std::vector<Instruction> instructions_;
};

// Evaluator class
class Evaluator {
public:
    Evaluator() {
        // Initialize built-in constants
        variables_["pi"] = 3.14159265358979323846;
        variables_["PI"] = 3.14159265358979323846;
        variables_["e"] = 2.71828182845904523536;
        variables_["E"] = 2.71828182845904523536;
    }

    // Parse and evaluate expression
    double evaluate(const std::string& expression) {
        auto expr = parse(expression);
        return expr->evaluate(variables_, functions_);
    }

    // Parse expression to AST
    ExprPtr parse(const std::string& expression) {
        Tokenizer tokenizer(expression);
        auto tokens = tokenizer.tokenize();
        Parser parser(tokens);
        return parser.parse();
    }

    // Compile expression to callable
    std::function<double()> compile(const std::string& expression) {
        auto expr = parse(expression);
        auto optimized = expr->optimize();

        // Capture variables and functions by reference
        return [this, optimized]() {
            return optimized->evaluate(variables_, functions_);
        };
    }

    // Variable management
    void set_variable(const std::string& name, double value) {
        variables_[name] = value;
    }

    double get_variable(const std::string& name) const {
        auto it = variables_.find(name);
        if (it == variables_.end()) {
            throw EvaluationError("Undefined variable: " + name);
        }
        return it->second;
    }

    void clear_variables() {
        variables_.clear();
    }

    // Function registration
    void register_function(const std::string& name, std::function<double(double)> func) {
        functions_[name] = [func](const std::vector<double>& args) {
            if (args.size() != 1) {
                throw EvaluationError("Function expects 1 argument");
            }
            return func(args[0]);
        };
    }

    void register_function(const std::string& name, std::function<double(double, double)> func) {
        functions_[name] = [func](const std::vector<double>& args) {
            if (args.size() != 2) {
                throw EvaluationError("Function expects 2 arguments");
            }
            return func(args[0], args[1]);
        };
    }

    void register_function(const std::string& name,
                          std::function<double(const std::vector<double>&)> func) {
        functions_[name] = func;
    }

    // Optimize expression and return as string
    std::string optimize(const std::string& expression) {
        auto expr = parse(expression);
        auto optimized = expr->optimize();
        return optimized->to_string();
    }

private:
    std::map<std::string, double> variables_;
    std::map<std::string, std::function<double(const std::vector<double>&)>> functions_;
};

// Type alias for compiled function
using CompiledFunction = std::function<double()>;

} // namespace expr
