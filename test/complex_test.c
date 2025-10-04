#include <stdio.h>
#include <string.h>

// Global variables
char global_message[] = "Welcome to the obfuscation test!";
int global_counter = 0;

// Function declarations
int factorial(int n);
int fibonacci(int n);
void print_message(const char* msg);
void process_data(int* data, int size);

// Factorial function
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

// Fibonacci function  
int fibonacci(int n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// Print message function
void print_message(const char* msg) {
    printf("Message: %s\n", msg);
}

// Process data function
void process_data(int* data, int size) {
    printf("Processing %d elements\n", size);
    for (int i = 0; i < size; i++) {
        data[i] = data[i] * 2 + 1;
    }
}

// Main function
int main() {
    printf("Hello, World!\n");
    
    // Test strings and functions
    print_message("Starting complex test");
    
    // Test factorial
    int fact_result = factorial(5);
    printf("Factorial of 5: %d\n", fact_result);
    
    // Test fibonacci
    int fib_result = fibonacci(10);
    printf("Fibonacci of 10: %d\n", fib_result);
    
    // Test global variables
    printf("Global message: %s\n", global_message);
    printf("Global counter: %d\n", global_counter);
    
    // Test array processing
    int numbers[] = {1, 2, 3, 4, 5};
    int size = sizeof(numbers) / sizeof(numbers[0]);
    process_data(numbers, size);
    
    printf("Processed numbers: ");
    for (int i = 0; i < size; i++) {
        printf("%d ", numbers[i]);
    }
    printf("\n");
    
    // Test string literals
    char* strings[] = {"First literal", "Second literal", "Third literal"};
    for (int i = 0; i < 3; i++) {
        printf("String %d: %s\n", i + 1, strings[i]);
    }
    
    printf("=== Test Complete ===\n");
    return 0;
}