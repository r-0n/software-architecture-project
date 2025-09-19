
## Class Diagram

```mermaid
classDiagram
    %% Django User Model (Built-in)
    class User {
        +id: int
        +username: str
        +email: str
        +first_name: str
        +last_name: str
        +password: str
        +is_active: bool
        +is_superuser: bool
        +date_joined: datetime
        +last_login: datetime
    }

    %% Accounts Module
    class UserProfile {
        +id: int
        +user: OneToOneField(User)
        +phone_number: str
        +address: TextField
        +role: str
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +is_admin() bool
        +__str__() str
    }

    class UserRegistrationForm {
        +email: EmailField
        +first_name: CharField
        +last_name: CharField
        +phone_number: CharField
        +address: CharField
        +role: ChoiceField
        +clean_email() str
        +clean_username() str
        +save() User
    }

    class UserLoginForm {
        +email: EmailField
        +password: CharField
    }

    class CustomUserAdmin {
        +inlines: UserProfileInline
        +list_display: tuple
        +list_filter: tuple
        +search_fields: tuple
    }

    class UserProfileInline {
        +model: UserProfile
        +can_delete: bool
        +verbose_name_plural: str
    }

    %% Products Module
    class Category {
        +id: int
        +name: str
        +description: TextField
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +__str__() str
    }

    class Product {
        +id: int
        +name: str
        +description: TextField
        +sku: str
        +price: DecimalField
        +category: ForeignKey(Category)
        +stock_quantity: int
        +is_active: bool
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +is_in_stock() bool
        +stock_status() str
        +__str__() str
    }

    class ProductForm {
        +name: CharField
        +description: TextField
        +sku: CharField
        +price: DecimalField
        +category: ModelChoiceField
        +stock_quantity: IntegerField
        +is_active: BooleanField
    }

    class ProductSearchForm {
        +search: CharField
        +category: ModelChoiceField
        +stock_status: ChoiceField
    }

    class CategoryForm {
        +name: CharField
        +description: TextField
    }

    %% Cart Module
    class CartItem {
        +id: int
        +product: ForeignKey(Product)
        +quantity: int
        +session_key: str
        +user: ForeignKey(User)
        +created_at: DateTimeField
        +updated_at: DateTimeField
        +total_price() Decimal
        +__str__() str
    }

    class Cart {
        -session: Session
        -user: User
        -session_key: str
        -cart: dict
        +add(product, quantity) void
        +remove(product) void
        +update(product, quantity) void
        +clear() void
        +save() void
        +__iter__() Iterator
        +__len__() int
        +get_total_price() Decimal
        +get_total_items() int
    }

    %% Orders Module
    class Sale {
        +id: int
        +user: ForeignKey(User)
        +address: str
        +total: DecimalField
        +status: str
        +created_at: DateTimeField
        +__str__() str
    }

    class SaleItem {
        +id: int
        +sale: ForeignKey(Sale)
        +product: ForeignKey(Product)
        +quantity: int
        +unit_price: DecimalField
        +subtotal() Decimal
    }

    class Payment {
        +id: int
        +sale: OneToOneField(Sale)
        +method: str
        +reference: str
        +amount: DecimalField
        +status: str
        +processed_at: DateTimeField
        +updated_at: DateTimeField
        +__str__() str
    }

    class CheckoutForm {
        +address: CharField
        +payment_method: ChoiceField
        +card_number: CharField
        +clean() dict
    }

    %% Business Rules Module
    class BusinessRules {
        +validate_product_for_cart(product_active, product_name) bool
        +validate_quantity_limit(quantity, available_stock, product_name) bool
        +validate_cart_update(quantity, available_stock, product_name) bool
        +calculate_cart_total(items) Decimal
        +calculate_item_total(price, quantity) Decimal
    }

    %% Payment Processing Module
    class PaymentProcessor {
        +process_payment(method, amount, card_number) dict
    }

    %% Decorators Module
    class AdminRequired {
        +admin_required(view_func) function
    }

    %% Relationships
    User ||--|| UserProfile : "has profile"
    User ||--o{ CartItem : "owns cart items"
    User ||--o{ Sale : "makes sales"
    
    Category ||--o{ Product : "contains products"
    Product ||--o{ CartItem : "added to cart"
    Product ||--o{ SaleItem : "sold in sales"
    
    Sale ||--o{ SaleItem : "contains items"
    Sale ||--|| Payment : "has payment"
    
    %% Form Relationships
    UserRegistrationForm ..> User : "creates"
    UserRegistrationForm ..> UserProfile : "creates"
    ProductForm ..> Product : "manages"
    CategoryForm ..> Category : "manages"
    CheckoutForm ..> Payment : "validates"
    
    %% Business Logic Relationships
    Cart ..> BusinessRules : "uses validation"
    CartItem ..> BusinessRules : "uses calculation"
    PaymentProcessor ..> Payment : "processes"
```

## Key Relationships and Design Patterns

### 1. **User Management**
- `User` (Django built-in) extended with `UserProfile` via OneToOne relationship
- Role-based access control with customer/admin roles
- Custom registration form that creates both User and UserProfile

### 2. **Product Catalog**
- `Category` → `Product` (One-to-Many)
- Products have SKU, pricing, stock management, and status tracking
- Comprehensive search and filtering capabilities

### 3. **Shopping Cart System**
- Dual storage: Database for authenticated users, Session for anonymous users
- `Cart` utility class manages both storage types transparently
- Stock validation integrated into cart operations

### 4. **Order Processing**
- `Sale` → `SaleItem` (One-to-Many) for order line items
- `Sale` → `Payment` (One-to-One) for payment tracking
- Status tracking throughout the order lifecycle

### 5. **Business Rules Separation**
- Dedicated `BusinessRules` module for reusable validation logic
- Testable business logic separated from Django model methods
- Consistent error handling and validation

### 6. **Payment Integration**
- Mock payment processor with realistic failure scenarios
- Support for Cash and Card payment methods
- Comprehensive validation and error handling

### 7. **Security & Access Control**
- Custom decorator for admin-only functionality
- Form validation with business rule enforcement
- Session management for anonymous users

## Architecture Benefits

1. **Modular Design**: Clear separation of concerns across Django apps
2. **Extensibility**: Easy to add new payment methods, product attributes, or user roles
3. **Testability**: Business logic separated into testable functions
4. **Scalability**: Database indexes and efficient query patterns
5. **User Experience**: Seamless cart persistence across login sessions
6. **Security**: Role-based access control and comprehensive validation

This architecture follows Django best practices while implementing a robust e-commerce system with proper separation of concerns and maintainable code structure.
