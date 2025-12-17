# Clean Code for AI-Assisted PRs: Complete Code Samples

Complete executable code samples demonstrating clean code principles for reviewing AI-assisted pull requests.

## Overview

This repository contains before/after examples showing how to refactor AI-generated code to be more readable, maintainable, and changeable:

- **Before examples**: Messy AI-generated code that "works" but is hard to read
- **After examples**: Clean, refactored code that's easy to understand and change
- **Review checklist**: Practical checks you can apply during code review
- **Test examples**: How to test clean code with proper dependency injection

## Architecture

```
┌─────────────────┐
│  AI-Generated   │
│  Messy Code     │
└────────┬────────┘
         │
         │ Review Checklist
         │
         ▼
┌─────────────────┐
│  Clean Code     │
│  Refactored     │
└─────────────────┘
```

## Prerequisites

- Node.js 18+ installed
- TypeScript 5.0+
- npm installed

## Installation

```bash
npm install
```

## Quick Start

### 1. Build the Project

```bash
npm run build
```

### 2. Run Examples

```bash
# Run before example (messy code)
npm run example:before

# Run after example (clean code)
npm run example:after
```

### 3. Run Tests

```bash
npm test
```

## Repository Structure

```
.
├── README.md
├── package.json
├── tsconfig.json
├── src/
│   ├── before/                    # Messy AI-generated code examples
│   │   ├── order-processor.ts     # Before: messy order processing
│   │   ├── user-handler.ts        # Before: generic handler pattern
│   │   └── data-util.ts           # Before: helper soup
│   ├── after/                     # Clean refactored code
│   │   ├── order-service.ts       # After: clean order service
│   │   ├── user-service.ts        # After: domain-specific service
│   │   └── order-calculator.ts    # After: focused calculator
│   ├── types.ts                   # Shared TypeScript types
│   └── examples/                  # Complete before/after examples
│       ├── before-example.ts      # Full messy example
│       └── after-example.ts       # Full clean example
├── tests/
│   ├── before.test.ts             # Tests for messy code (hard to test)
│   ├── after.test.ts              # Tests for clean code (easy to test)
│   └── order-service.test.ts      # Comprehensive service tests
└── scripts/
    └── compare-complexity.ts      # Script to compare code complexity
```

## Key Examples

### Example 1: Order Processing

**Before (Messy):**
- Generic function names (`processData`, `handleRequest`)
- Deep nesting (4-5 levels)
- Mixed validation and business logic
- Inconsistent error handling
- Hidden dependencies

**After (Clean):**
- Clear function names (`processUserOrders`, `filterActiveOrders`)
- Linear flow with early returns
- Validation at boundaries
- Consistent error model
- Explicit dependencies

See `src/examples/before-example.ts` and `src/examples/after-example.ts` for the complete comparison.

### Example 2: User Handler

**Before:**
```typescript
function handleUserRequest(data: any): any {
  // Generic handler with nested conditionals
}
```

**After:**
```typescript
class UserService {
  async getUserOrders(userId: string): Promise<Order[]> {
    // Clear, focused service method
  }
}
```

### Example 3: Helper Soup

**Before:**
```typescript
// utils.ts - 200 lines of unrelated functions
function transformArray(...) { }
function processData(...) { }
function validateInput(...) { }
```

**After:**
```typescript
// order-calculator.ts - focused calculator
class OrderCalculator {
  calculateTotal(order: Order): number { }
}
```

## Review Checklist

Use this checklist during code review:

1. **Naming**: Functions are verbs, variables are nouns, no generic "Handler/Manager"
2. **Scope**: Variables declared close to use, no long-lived setup blocks
3. **Duplication**: No repeated conditionals or mapping logic
4. **Function shape**: Short functions, early returns, max 2-3 levels nesting
5. **Boundaries**: Validation at API edges, not in business logic
6. **Errors**: Consistent error model, no swallowed exceptions
7. **Dependencies**: Injected, not global; no helper soup

## Testing

### Testing Messy Code (Hard)

```typescript
// Hard to test because of hidden dependencies
test('processes order', () => {
  // Need to mock global database
  // Can't easily swap implementations
});
```

### Testing Clean Code (Easy)

```typescript
// Easy to test with dependency injection
test('processes active orders', async () => {
  const mockRepo = { findByUserId: jest.fn() };
  const service = new OrderService(mockRepo);
  // Clear, testable
});
```

## Code Complexity Comparison

Run the complexity comparison script:

```bash
npm run compare-complexity
```

This shows:
- Cyclomatic complexity scores
- Function length metrics
- Nesting depth analysis
- Dependency coupling scores

## Best Practices Demonstrated

1. **Clear Naming**: Names that explain intent
2. **Single Responsibility**: Each function does one thing
3. **Dependency Injection**: Testable, flexible code
4. **Early Returns**: Linear flow, less nesting
5. **Boundary Validation**: Validate at edges
6. **Consistent Errors**: Predictable error handling
7. **Type Safety**: Leverage TypeScript for correctness

## Common AI-Generated Patterns to Watch For

- Over-abstracted interfaces with one implementation
- Generic utilities instead of domain concepts
- Too many optional parameters
- Magic defaults and silent fallbacks
- Deep nesting and long functions
- Mixed validation and business logic

## Migration Guide

If you have messy AI-generated code:

1. **Start with naming**: Rename generic functions to be specific
2. **Extract functions**: Break down long functions into smaller ones
3. **Add types**: Use TypeScript to enforce structure
4. **Inject dependencies**: Replace globals with constructor injection
5. **Consolidate errors**: Use a consistent error model
6. **Move validation**: Push validation to API boundaries
7. **Remove duplication**: Extract repeated patterns

## Configuration

Set environment variables:

```bash
# Development
export NODE_ENV=development

# Testing
export NODE_ENV=test
```

## Scripts

- `npm run build` - Compile TypeScript
- `npm run dev` - Run in development mode
- `npm test` - Run tests
- `npm run example:before` - Run messy code example
- `npm run example:after` - Run clean code example
- `npm run compare-complexity` - Compare code complexity metrics

## Resources

- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring by Martin Fowler](https://refactoring.com/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## License

MIT

## Author

Yusuf Elborey
