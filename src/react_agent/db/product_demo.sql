CREATE TABLE Products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    reorder_level INTEGER DEFAULT 10,
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);

INSERT INTO Products (name, description, price, stock_quantity, reorder_level) VALUES
('Laptop', '15-inch, 16GB RAM, 512GB SSD', 1200.00, 50, 10),
('Smartphone', '6.5-inch display, 128GB storage', 800.00, 100, 20),
('Headphones', 'Wireless noise-canceling', 250.00, 75, 15),
('Smartwatch', 'Fitness tracking, heart rate monitor', 300.00, 60, 10),
('Gaming Console', 'Latest generation console', 500.00, 30, 5),
('Monitor', '27-inch, 4K resolution', 450.00, 40, 10),
('Keyboard', 'Mechanical RGB gaming keyboard', 150.00, 90, 15),
('Mouse', 'Wireless ergonomic mouse', 80.00, 120, 20),
('External Hard Drive', '2TB USB-C SSD', 200.00, 35, 10),
('Tablet', '10-inch, 256GB storage', 600.00, 45, 10),
('Printer', 'Wireless all-in-one printer', 250.00, 20, 5),
('Router', 'Wi-Fi 6 high-speed router', 180.00, 60, 10),
('Webcam', '1080p HD video webcam', 90.00, 50, 10),
('Speakers', 'Bluetooth stereo speakers', 220.00, 70, 15),
('Graphics Card', 'RTX 4070 12GB GDDR6X', 900.00, 25, 5),
('Power Bank', '20000mAh fast-charging', 70.00, 80, 15),
('Projector', '4K home theater projector', 1100.00, 15, 5),
('Desk Lamp', 'Smart LED desk lamp', 60.00, 40, 10),
('VR Headset', 'Virtual reality gaming headset', 650.00, 25, 5),
('SSD', '1TB NVMe M.2 SSD', 140.00, 100, 20),
('Surge Protector', '8-outlet power strip', 50.00, 75, 15),
('Wireless Charger', 'Fast charging pad', 45.00, 90, 15),
('Microphone', 'USB condenser microphone', 120.00, 35, 10),
('Smart Plug', 'Wi-Fi enabled smart plug', 30.00, 60, 10),
('E-Reader', '6-inch e-ink display', 130.00, 25, 5),
('CCTV Camera', 'Wireless security camera', 150.00, 45, 10),
('Electric Kettle', 'Smart temperature control', 70.00, 50, 10),
('Mechanical Watch', 'Automatic wristwatch', 300.00, 20, 5),
('Drone', '4K camera drone', 750.00, 10, 5);