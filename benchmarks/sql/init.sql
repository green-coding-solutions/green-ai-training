-- PostgreSQL benchmark setup: SELECT * vs SELECT named columns
-- Creates wide tables with substantial text content and realistic data volumes

SET client_min_messages TO WARNING;

-- 52-column products table: mix of numeric metadata and large text fields.
-- The text columns (description, specs, localisations) are the payload that
-- SELECT * drags across the wire even when the caller only needs a handful of fields.
CREATE TABLE IF NOT EXISTS products (
    id                BIGSERIAL PRIMARY KEY,
    sku               VARCHAR(20)    NOT NULL,
    name              VARCHAR(200)   NOT NULL,
    price             NUMERIC(10,2)  NOT NULL,
    compare_at_price  NUMERIC(10,2),
    cost_price        NUMERIC(10,2),
    category          VARCHAR(50)    NOT NULL,
    subcategory       VARCHAR(50),
    brand             VARCHAR(100),
    supplier_id       INTEGER,
    supplier_sku      VARCHAR(50),
    stock_quantity    INTEGER        NOT NULL DEFAULT 0,
    reserved_quantity INTEGER        NOT NULL DEFAULT 0,
    reorder_point     INTEGER        NOT NULL DEFAULT 10,
    lead_time_days    SMALLINT       NOT NULL DEFAULT 7,
    weight_grams      INTEGER,
    length_cm         NUMERIC(8,2),
    width_cm          NUMERIC(8,2),
    height_cm         NUMERIC(8,2),
    -- Large text payload columns
    description       TEXT,
    short_description VARCHAR(500),
    specifications    TEXT,
    warranty_info     TEXT,
    care_instructions TEXT,
    return_policy     TEXT,
    -- Localised content
    name_de           VARCHAR(200),
    name_fr           VARCHAR(200),
    name_es           VARCHAR(200),
    description_de    TEXT,
    description_fr    TEXT,
    description_es    TEXT,
    -- SEO / marketing
    meta_title        VARCHAR(200),
    meta_description  VARCHAR(500),
    tags              VARCHAR(500),
    images_json       TEXT,
    attributes_json   TEXT,
    -- Boolean flags
    is_active         BOOLEAN        NOT NULL DEFAULT TRUE,
    is_featured       BOOLEAN        NOT NULL DEFAULT FALSE,
    is_digital        BOOLEAN        NOT NULL DEFAULT FALSE,
    requires_shipping BOOLEAN        NOT NULL DEFAULT TRUE,
    taxable           BOOLEAN        NOT NULL DEFAULT TRUE,
    -- Aggregate stats
    average_rating    NUMERIC(3,2)   DEFAULT 0.00,
    review_count      INTEGER        NOT NULL DEFAULT 0,
    view_count        INTEGER        NOT NULL DEFAULT 0,
    purchase_count    INTEGER        NOT NULL DEFAULT 0,
    -- Warehouse
    warehouse_location VARCHAR(20),
    bin_number        VARCHAR(10),
    seo_url           VARCHAR(300),
    -- Timestamps
    created_at        TIMESTAMP      NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMP      NOT NULL DEFAULT NOW(),
    published_at      TIMESTAMP,
    last_ordered_at   TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_is_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_sku       ON products(sku);

-- 44-column orders table
CREATE TABLE IF NOT EXISTS orders (
    id                 BIGSERIAL PRIMARY KEY,
    order_number       VARCHAR(20)   NOT NULL,
    customer_id        INTEGER       NOT NULL,
    customer_email     VARCHAR(200)  NOT NULL,
    customer_name      VARCHAR(200)  NOT NULL,
    status             VARCHAR(20)   NOT NULL DEFAULT 'pending',
    subtotal           NUMERIC(12,2) NOT NULL,
    discount_amount    NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    tax_amount         NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    shipping_amount    NUMERIC(12,2) NOT NULL DEFAULT 0.00,
    total_amount       NUMERIC(12,2) NOT NULL,
    billing_name       VARCHAR(200),
    billing_company    VARCHAR(200),
    billing_street1    VARCHAR(200),
    billing_street2    VARCHAR(200),
    billing_city       VARCHAR(100),
    billing_state      VARCHAR(50),
    billing_zip        VARCHAR(20),
    billing_country    CHAR(2),
    shipping_name      VARCHAR(200),
    shipping_company   VARCHAR(200),
    shipping_street1   VARCHAR(200),
    shipping_street2   VARCHAR(200),
    shipping_city      VARCHAR(100),
    shipping_state     VARCHAR(50),
    shipping_zip       VARCHAR(20),
    shipping_country   CHAR(2),
    payment_method     VARCHAR(50),
    payment_reference  VARCHAR(100),
    payment_status     VARCHAR(20),
    promo_code         VARCHAR(50),
    notes              TEXT,
    internal_notes     TEXT,
    ip_address         VARCHAR(45),
    user_agent         VARCHAR(500),
    source             VARCHAR(50),
    order_date         TIMESTAMP     NOT NULL DEFAULT NOW(),
    paid_at            TIMESTAMP,
    shipped_at         TIMESTAMP,
    delivered_at       TIMESTAMP,
    cancelled_at       TIMESTAMP,
    refunded_at        TIMESTAMP,
    created_at         TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_order_date  ON orders(order_date);

-- 15-column order_items table (no FK constraints for fast bulk insert)
CREATE TABLE IF NOT EXISTS order_items (
    id                BIGSERIAL PRIMARY KEY,
    order_id          BIGINT        NOT NULL,
    product_id        BIGINT        NOT NULL,
    sku               VARCHAR(20)   NOT NULL,
    product_name      VARCHAR(200)  NOT NULL,
    quantity          INTEGER       NOT NULL,
    unit_price        NUMERIC(10,2) NOT NULL,
    discount_amount   NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    tax_rate          NUMERIC(5,4)  NOT NULL DEFAULT 0.0000,
    tax_amount        NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    subtotal          NUMERIC(12,2) NOT NULL,
    weight_grams      INTEGER,
    is_digital        BOOLEAN       NOT NULL DEFAULT FALSE,
    fulfilled_quantity INTEGER      NOT NULL DEFAULT 0,
    created_at        TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

-- --------------------------------------------------------------------------
-- Data generation
-- --------------------------------------------------------------------------

-- Products: 50 000 rows, ~1.5 KB text per row (~75 MB total text payload).
-- All TEXT fields use repeat() to produce realistic column widths.
INSERT INTO products (
    sku, name, price, compare_at_price, cost_price,
    category, subcategory, brand,
    supplier_id, supplier_sku,
    stock_quantity, reserved_quantity, reorder_point, lead_time_days,
    weight_grams, length_cm, width_cm, height_cm,
    description, short_description, specifications,
    warranty_info, care_instructions, return_policy,
    name_de, name_fr, name_es,
    description_de, description_fr, description_es,
    meta_title, meta_description, tags, images_json, attributes_json,
    is_active, is_featured, is_digital, requires_shipping, taxable,
    average_rating, review_count, view_count, purchase_count,
    warehouse_location, bin_number, seo_url,
    created_at, updated_at, published_at, last_ordered_at
)
SELECT
    'SKU-' || LPAD(gs::TEXT, 8, '0'),
    (ARRAY['Laptop','Mouse','Keyboard','Monitor','Headset','Webcam','USB Hub','Cable',
           'T-Shirt','Jeans','Sneakers','Hat','Jacket','Socks','Belt','Watch',
           'Novel','Textbook','Pen Set','Notebook'])[1 + (gs % 20)]
        || ' Model ' || gs,
    (5 + (gs % 1990) * 0.5)::NUMERIC(10,2),
    (10 + (gs % 2400) * 0.5)::NUMERIC(10,2),
    (3 + (gs % 900) * 0.5)::NUMERIC(10,2),
    (ARRAY['Electronics','Clothing','Books','Sports','Home & Garden',
           'Toys','Automotive','Food & Drink'])[1 + (gs % 8)],
    (ARRAY['Computers','Accessories','Peripherals','Audio','Video',
           'Men','Women','Kids','Fiction','Non-Fiction','Technical','Garden','Kitchen'])[1 + (gs % 13)],
    (ARRAY['BrandAlpha','BrandBeta','BrandGamma','BrandDelta',
           'BrandEpsilon','BrandZeta','BrandEta','BrandTheta'])[1 + (gs % 8)],
    1 + (gs % 50),
    'SUPP-' || LPAD(gs::TEXT, 6, '0'),
    (gs % 1000),
    (gs % 50),
    5 + (gs % 20),
    1 + (gs % 30),
    50 + (gs % 4950),
    (1 + (gs % 100))::NUMERIC(8,2),
    (1 + (gs % 80))::NUMERIC(8,2),
    (1 + (gs % 60))::NUMERIC(8,2),
    -- ~300-char description
    'Product ' || gs || ': ' ||
    CASE gs % 3
        WHEN 0 THEN 'Designed for professionals, this item delivers superior performance and reliability. '
        WHEN 1 THEN 'Perfect for everyday use, combining durability with elegant design. '
        ELSE 'Outstanding value with all the features needed for success in demanding environments. '
    END ||
    repeat('High-quality materials ensure long-lasting performance across all use cases. ', 3) ||
    'Ships within 2–3 business days.',
    -- ~120-char short description
    'Model ' || gs || ' from ' ||
    (ARRAY['BrandAlpha','BrandBeta','BrandGamma','BrandDelta'])[1 + (gs % 4)] ||
    '. Top-rated in its category. Fast shipping, easy returns.',
    -- ~280-char specifications
    'SKU: SKU-' || LPAD(gs::TEXT, 8, '0') || ' | ' ||
    repeat('Input voltage: 100-240V AC. Operating temp: 0-40°C. Dimensions vary by variant. Certifications: CE, FCC, RoHS. ', 2),
    -- ~120-char warranty
    repeat('2-year manufacturer warranty covering defects in materials and workmanship. ', 1) ||
    'Contact support@example.com for warranty claims.',
    -- ~100-char care instructions
    repeat('Store in a cool, dry place away from direct sunlight. Clean with a soft dry cloth. ', 1),
    -- ~100-char return policy
    '30-day hassle-free returns. Items must be unused and in original packaging. ' ||
    'Refunds processed within 5 business days.',
    -- Localised names (~30 chars)
    'Produkt ' || gs || ' - ' || (ARRAY['Alpha','Beta','Gamma','Delta'])[1 + (gs % 4)] || ' Modell',
    'Produit ' || gs || ' - ' || (ARRAY['Alpha','Bêta','Gamma','Delta'])[1 + (gs % 4)] || ' Modèle',
    'Producto ' || gs || ' - ' || (ARRAY['Alfa','Beta','Gamma','Delta'])[1 + (gs % 4)] || ' Modelo',
    -- Localised descriptions (~220 chars each)
    repeat('Hohe Qualität und ausgezeichnete Leistung für anspruchsvolle Nutzer. Langlebige Materialien. ', 2) || 'Schneller Versand.',
    repeat('Haute qualité et excellentes performances pour les utilisateurs exigeants. Matériaux durables. ', 2) || 'Livraison rapide.',
    repeat('Alta calidad y excelente rendimiento para usuarios exigentes. Materiales duraderos. ', 2) || 'Envío rápido.',
    -- SEO fields
    'Buy ' || (ARRAY['Laptop','Mouse','Keyboard','Monitor','Headset'])[1 + (gs % 5)] || ' Model ' || gs || ' – Best Price',
    'Shop Model ' || gs || ' at unbeatable prices. Fast shipping, easy returns, satisfaction guaranteed.',
    (ARRAY['electronics','clothing','books','sports','home'])[1 + (gs % 5)] || ',quality,value,model-' || gs,
    '[{"url":"img' || gs || '-1.jpg"},{"url":"img' || gs || '-2.jpg"}]',
    '{"color":"' || (ARRAY['black','white','silver','blue','red'])[1 + (gs % 5)] || '","material":"premium"}',
    -- Flags
    (gs % 10 != 0),
    (gs % 20 = 0),
    (gs % 50 = 0),
    (gs % 50 != 0),
    TRUE,
    -- Stats
    (1.0 + (gs % 40) * 0.1)::NUMERIC(3,2),
    (gs % 5000),
    (gs % 500000),
    (gs % 50000),
    -- Warehouse
    'WH-' || LPAD((1 + (gs % 5))::TEXT, 2, '0'),
    'B-' || LPAD((gs % 999)::TEXT, 3, '0'),
    (ARRAY['electronics','clothing','books','sports','home'])[1 + (gs % 5)] || '/model-' || gs,
    -- Timestamps
    NOW() - ((365 - (gs % 365)) || ' days')::INTERVAL,
    NOW() - ((30  - (gs % 30))  || ' days')::INTERVAL,
    NOW() - ((300 - (gs % 300)) || ' days')::INTERVAL,
    CASE WHEN gs % 3 != 0
         THEN NOW() - ((90 - (gs % 90)) || ' days')::INTERVAL
         ELSE NULL END
FROM generate_series(1, 50000) gs;

-- Orders: 100 000 rows
INSERT INTO orders (
    order_number, customer_id, customer_email, customer_name, status,
    subtotal, discount_amount, tax_amount, shipping_amount, total_amount,
    billing_name, billing_company,
    billing_street1, billing_city, billing_state, billing_zip, billing_country,
    shipping_name, shipping_street1, shipping_city, shipping_state, shipping_zip, shipping_country,
    payment_method, payment_reference, payment_status,
    promo_code, notes, internal_notes, ip_address, user_agent, source,
    order_date, paid_at, shipped_at, delivered_at, created_at, updated_at
)
SELECT
    'ORD-' || LPAD(gs::TEXT, 10, '0'),
    1 + (gs % 50000),
    'customer' || (gs % 50000) || '@example.com',
    'Customer ' || (gs % 50000),
    (ARRAY['pending','processing','shipped','delivered','cancelled'])[1 + (gs % 5)],
    (10 + (gs % 990))::NUMERIC(12,2),
    (gs % 50)::NUMERIC(12,2),
    (gs % 80)::NUMERIC(12,2),
    (5 + (gs % 20))::NUMERIC(12,2),
    (25 + (gs % 1100))::NUMERIC(12,2),
    'Billing Person ' || gs,
    CASE WHEN gs % 3 = 0 THEN 'Company ' || (gs % 5000) ELSE NULL END,
    gs || ' Main Street',
    (ARRAY['New York','Los Angeles','Chicago','Houston','Phoenix','Seattle','Boston'])[1 + (gs % 7)],
    (ARRAY['NY','CA','IL','TX','AZ','WA','MA'])[1 + (gs % 7)],
    LPAD((10000 + (gs % 90000))::TEXT, 5, '0'),
    'US',
    'Ship To Person ' || gs,
    gs || ' Delivery Ave',
    (ARRAY['New York','Los Angeles','Chicago','Houston','Phoenix','Seattle','Boston'])[1 + ((gs + 2) % 7)],
    (ARRAY['NY','CA','IL','TX','AZ','WA','MA'])[1 + ((gs + 2) % 7)],
    LPAD((10000 + ((gs + 5) % 90000))::TEXT, 5, '0'),
    'US',
    (ARRAY['credit_card','paypal','bank_transfer','crypto'])[1 + (gs % 4)],
    'REF-' || LPAD(gs::TEXT, 12, '0'),
    (ARRAY['paid','pending','failed','refunded'])[1 + (gs % 4)],
    CASE WHEN gs % 5 = 0 THEN 'PROMO' || (gs % 10) ELSE NULL END,
    CASE WHEN gs % 7 = 0 THEN 'Customer note for order ' || gs ELSE NULL END,
    CASE WHEN gs % 11 = 0 THEN 'Internal: verify shipping address' ELSE NULL END,
    '192.168.' || (gs % 255) || '.' || ((gs * 7) % 255),
    'Mozilla/5.0 (compatible; benchmark/1.0)',
    (ARRAY['web','mobile','api','pos'])[1 + (gs % 4)],
    NOW() - ((365 - (gs % 365)) || ' days')::INTERVAL,
    CASE WHEN gs % 5 != 0 THEN NOW() - ((360 - (gs % 360)) || ' days')::INTERVAL ELSE NULL END,
    CASE WHEN gs % 5 IN (2,3) THEN NOW() - ((300 - (gs % 300)) || ' days')::INTERVAL ELSE NULL END,
    CASE WHEN gs % 5 = 3 THEN NOW() - ((250 - (gs % 250)) || ' days')::INTERVAL ELSE NULL END,
    NOW() - ((365 - (gs % 365)) || ' days')::INTERVAL,
    NOW() - ((30  - (gs % 30))  || ' days')::INTERVAL
FROM generate_series(1, 100000) gs;

-- Order items: 250 000 rows
INSERT INTO order_items (
    order_id, product_id, sku, product_name, quantity,
    unit_price, discount_amount, tax_rate, tax_amount, subtotal,
    weight_grams, is_digital, fulfilled_quantity
)
SELECT
    1 + (gs % 100000),
    1 + (gs % 50000),
    'SKU-' || LPAD((1 + (gs % 50000))::TEXT, 8, '0'),
    (ARRAY['Laptop','Mouse','Keyboard','Monitor','Headset','Webcam','USB Hub','Cable',
           'T-Shirt','Jeans','Sneakers','Hat','Jacket','Socks','Belt','Watch',
           'Novel','Textbook','Pen Set','Notebook'])[1 + (gs % 20)]
        || ' Model ' || (1 + (gs % 50000)),
    1 + (gs % 5),
    (5 + (gs % 995))::NUMERIC(10,2),
    (gs % 30)::NUMERIC(10,2),
    (0.05 + (gs % 5) * 0.01)::NUMERIC(5,4),
    (gs % 40)::NUMERIC(10,2),
    (10 + (gs % 2490))::NUMERIC(12,2),
    50 + (gs % 4950),
    (gs % 50 = 0),
    CASE WHEN gs % 5 = 3 THEN 1 + (gs % 5) ELSE 0 END
FROM generate_series(1, 250000) gs;

VACUUM ANALYZE products;
VACUUM ANALYZE orders;
VACUUM ANALYZE order_items;

-- Lightweight event-log table used exclusively by the bulk-insert benchmarks.
-- No FK constraints so each insert method is measured in isolation.
CREATE TABLE IF NOT EXISTS bench_inserts (
    id         BIGSERIAL     PRIMARY KEY,
    session_id INTEGER       NOT NULL,
    event_type VARCHAR(30)   NOT NULL,
    user_id    INTEGER       NOT NULL,
    value      NUMERIC(12,2) NOT NULL,
    payload    VARCHAR(200),
    ts         TIMESTAMP     NOT NULL DEFAULT NOW()
);
