-- Retail Management System Database Schema
-- Generated from Django models
-- This file contains the database schema for the retail management system

-- ==============================================
-- DJANGO CORE TABLES (auth_user, django_migrations, etc.)
-- ==============================================

-- Django's built-in User table
CREATE TABLE "auth_user" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "password" varchar(128) NOT NULL,
    "last_login" datetime,
    "is_superuser" bool NOT NULL,
    "username" varchar(150) NOT NULL UNIQUE,
    "first_name" varchar(150) NOT NULL,
    "last_name" varchar(150) NOT NULL,
    "email" varchar(254) NOT NULL,
    "is_staff" bool NOT NULL,
    "is_active" bool NOT NULL,
    "date_joined" datetime NOT NULL
);

-- Django migrations tracking
CREATE TABLE "django_migrations" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "app" varchar(255) NOT NULL,
    "name" varchar(255) NOT NULL,
    "applied" datetime NOT NULL
);

-- Django content types
CREATE TABLE "django_content_type" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "app_label" varchar(100) NOT NULL,
    "model" varchar(100) NOT NULL,
    UNIQUE ("app_label", "model")
);

-- Django sessions
CREATE TABLE "django_session" (
    "session_key" varchar(40) NOT NULL PRIMARY KEY,
    "session_data" text NOT NULL,
    "expire_date" datetime NOT NULL
);

-- Django admin log
CREATE TABLE "django_admin_log" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "action_time" datetime NOT NULL,
    "object_id" text,
    "object_repr" varchar(200) NOT NULL,
    "action_flag" smallint unsigned NOT NULL,
    "change_message" text NOT NULL,
    "content_type_id" integer,
    "user_id" integer NOT NULL,
    FOREIGN KEY ("content_type_id") REFERENCES "django_content_type" ("id"),
    FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id")
);

-- ==============================================
-- ACCOUNTS APP TABLES
-- ==============================================

-- User profiles extending Django's User model
CREATE TABLE "accounts_userprofile" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "role" varchar(20) NOT NULL,
    "phone_number" varchar(15) NOT NULL,
    "address" text NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ==============================================
-- PRODUCTS APP TABLES
-- ==============================================

-- Product categories
CREATE TABLE "products_category" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(100) NOT NULL UNIQUE,
    "description" text NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL
);

-- Products
CREATE TABLE "products_product" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "name" varchar(200) NOT NULL,
    "description" text NOT NULL,
    "sku" varchar(50) NOT NULL UNIQUE,
    "price" decimal NOT NULL,
    "stock_quantity" integer unsigned NOT NULL CHECK ("stock_quantity" >= 0),
    "is_active" bool NOT NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "category_id" bigint NOT NULL REFERENCES "products_category" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ==============================================
-- CART APP TABLES
-- ==============================================

-- Shopping cart items
CREATE TABLE "cart_cartitem" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0),
    "session_key" varchar(40) NULL,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "product_id" bigint NOT NULL REFERENCES "products_product" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);
CREATE UNIQUE INDEX "cart_cartitem_product_id_session_key_user_id_dd412987_uniq" ON "cart_cartitem" ("product_id", "session_key", "user_id");

-- ==============================================
-- ORDERS APP TABLES
-- ==============================================

-- Sales/Orders
CREATE TABLE "orders_sale" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "status" varchar(10) NOT NULL,
    "address" varchar(255) NOT NULL,
    "total" decimal NOT NULL,
    "created_at" datetime NOT NULL,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Sale items (products in each sale)
CREATE TABLE "orders_saleitem" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "quantity" integer unsigned NOT NULL CHECK ("quantity" >= 0),
    "unit_price" decimal NOT NULL,
    "product_id" bigint NOT NULL REFERENCES "products_product" ("id") DEFERRABLE INITIALLY DEFERRED,
    "sale_id" bigint NOT NULL REFERENCES "orders_sale" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Payments
CREATE TABLE "orders_payment" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "method" varchar(10) NOT NULL,
    "reference" varchar(100) NULL,
    "amount" decimal NOT NULL,
    "status" varchar(10) NOT NULL,
    "processed_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "sale_id" bigint NOT NULL UNIQUE REFERENCES "orders_sale" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ==============================================
-- INDEXES FOR PERFORMANCE
-- ==============================================

-- Product indexes (Django-generated names)
CREATE INDEX "products_product_category_id_9b594869" ON "products_product" ("category_id");
CREATE INDEX "products_pr_sku_ca0cdc_idx" ON "products_product" ("sku");
CREATE INDEX "products_pr_categor_9edb3d_idx" ON "products_product" ("category_id");
CREATE INDEX "products_pr_is_acti_ca4d9a_idx" ON "products_product" ("is_active");

-- Cart indexes (Django-generated names)
CREATE INDEX "cart_cartitem_product_id_b24e265a" ON "cart_cartitem" ("product_id");
CREATE INDEX "cart_cartitem_user_id_292943b8" ON "cart_cartitem" ("user_id");

-- Order indexes (Django-generated names)
CREATE INDEX "orders_sale_user_id_e9b59eb1" ON "orders_sale" ("user_id");
CREATE INDEX "orders_saleitem_product_id_3f25ccde" ON "orders_saleitem" ("product_id");
CREATE INDEX "orders_saleitem_sale_id_beab7240" ON "orders_saleitem" ("sale_id");

-- ==============================================
-- SAMPLE DATA (Optional)
-- ==============================================

-- Sample categories
INSERT INTO "products_category" ("name", "description", "created_at", "updated_at") VALUES
('Electronics', 'Electronic devices and gadgets', datetime('now'), datetime('now')),
('Clothing', 'Apparel and fashion items', datetime('now'), datetime('now')),
('Books', 'Books and educational materials', datetime('now'), datetime('now'));

-- Sample products
INSERT INTO "products_product" ("name", "description", "sku", "price", "stock_quantity", "is_active", "created_at", "updated_at", "category_id") VALUES
('Laptop', 'High-performance laptop computer', 'LAP001', 999.99, 10, 1, datetime('now'), datetime('now'), 1),
('T-Shirt', 'Comfortable cotton t-shirt', 'TSH001', 19.99, 50, 1, datetime('now'), datetime('now'), 2),
('Python Book', 'Learn Python programming', 'BOK001', 49.99, 25, 1, datetime('now'), datetime('now'), 3);

