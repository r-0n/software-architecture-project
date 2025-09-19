classDiagram
    %% Core Models
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

    %% Forms
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

    class CheckoutForm {
        +address: CharField
        +payment_method: ChoiceField
        +card_number: CharField
        +clean() dict
    }

    %% Admin Classes
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

    class ProductAdmin {
        +list_display: tuple
        +list_filter: tuple
        +search_fields: tuple
        +list_editable: tuple
        +fieldsets: tuple
    }

    class CategoryAdmin {
        +list_display: tuple
        +list_filter: tuple
        +search_fields: tuple
    }

    %% Business Logic
    class BusinessRules {
        +validate_product_for_cart() bool
        +validate_quantity_limit() bool
        +validate_cart_update() bool
        +calculate_cart_total() Decimal
        +calculate_item_total() Decimal
    }

    class PaymentProcessor {
        +process_payment() dict
    }

    %% Support Classes
    class AdminRequired {
        +admin_required(view_func) function
    }

    class PDFReceiptGenerator {
        +download_receipt() HttpResponse
        +generate_pdf_content() bytes
        +create_order_table() Table
        +create_items_table() Table
    }

    class CreateSampleDataCommand {
        +help: str
        +handle() void
    }

    %% Context Processors
    class UserAdminStatusProcessor {
        +user_admin_status(request) dict
    }

    class CartContextProcessor {
        +cart_context(request) dict
    }

    %% View Classes
    class RegisterView {
        +form_class: UserRegistrationForm
        +template_name: str
        +success_url: str
        +form_valid() HttpResponseRedirect
    }

    %% Core Relationships
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
    
    %% Admin Relationships
    CustomUserAdmin ..> User : "manages"
    UserProfileInline ..> UserProfile : "inline"
    ProductAdmin ..> Product : "manages"
    CategoryAdmin ..> Category : "manages"
    
    %% Business Logic Relationships
    Cart ..> BusinessRules : "uses validation"
    CartItem ..> BusinessRules : "uses calculation"
    PaymentProcessor ..> Payment : "processes"
    PDFReceiptGenerator ..> Sale : "generates receipts"
    PDFReceiptGenerator ..> SaleItem : "includes items"
    PDFReceiptGenerator ..> Payment : "includes payment info"
    
    %% Context Processor Relationships
    UserAdminStatusProcessor ..> UserProfile : "provides context"
    CartContextProcessor ..> Cart : "provides context"