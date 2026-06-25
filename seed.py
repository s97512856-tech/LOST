import sqlite3, os

db_path = os.path.join(os.path.dirname(__file__), 'lost.db')
conn = sqlite3.connect(db_path)
db = conn.cursor()

# Test product ($0)
db.execute('''INSERT OR IGNORE INTO products (id, name, name_ar, description, desc_ar, price, category)
    VALUES (1, 'Test Product', 'منتج تجريبي', 'A test product to try the payment flow. Price: $0 —完全免费!',
    'منتج تجريبي لاختبار نظام الدفع. السعر: 0', 0, 'Test')''')

# 8 services
services = [
    ('Website Development', 'تطوير مواقع', 'Clean, responsive websites with HTML, CSS, and JavaScript.',
     'مواقع متجاوبة ونظيفة', 40, 'Web Development'),
    ('WordPress Setup', 'ووردبريس', 'Theme customization, plugin config, and bug fixes.',
     'تعديل ثيمات وإصلاح أخطاء', 30, 'Web Development'),
    ('Discord Bot Development', 'بوتات دسكورد', 'Custom bots for moderation, music, games, and more.',
     'بوتات إدارة موسيقى وألعاب', 50, 'Discord'),
    ('Figma to HTML', 'تصميم إلى كود', 'Convert your designs into pixel-perfect responsive code.',
     'تحويل التصميم إلى كود', 40, 'Web Development'),
    ('Bug Fixing', 'إصلاح أخطاء', 'Fix layout, logic, or functionality issues in your code.',
     'إصلاح مشاكل المواقع', 30, 'Development'),
    ('Automation Scripts', 'سكريبتات أتمتة', 'Python or JavaScript scripts to automate repetitive tasks.',
     'أتمتة المهام المتكررة', 35, 'Development'),
    ('FiveM Server Development', 'تطوير فايف إم', 'Custom scripts, mods, and full server setup for FiveM.',
     'سكريبتات وإعداد سيرفرات فايف إم', 100, 'FiveM'),
    ('Programmer for Hire', 'مبرمج للإيجار', 'Tell me your idea and I will build it for you.',
     'أبرمج لك أي فكرة', 50, 'Development'),
]

for i, (name, name_ar, desc, desc_ar, price, category) in enumerate(services, start=2):
    db.execute('''INSERT OR IGNORE INTO products (id, name, name_ar, description, desc_ar, price, category)
        VALUES (?,?,?,?,?,?,?)''', (i, name, name_ar, desc, desc_ar, price, category))

conn.commit()
conn.close()
print(f'Added 9 products (1 test + 8 services)')
print('Run: python seed.py')
