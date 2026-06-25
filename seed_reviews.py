import sqlite3, os, random
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), 'lost.db')
conn = sqlite3.connect(db_path)
db = conn.cursor()

# Get all users and products
users = db.execute('SELECT id FROM users').fetchall()
products = db.execute('SELECT id, name FROM products').fetchall()

if not users:
    print('No users found. Register first.')
    exit()
if not products:
    print('No products found. Run seed.py first.')
    exit()

reviews_data = [
    (5, 'Amazing work! The website looks exactly like I wanted. Fast delivery and great communication. Highly recommend!', 'عمل رائع! الموقع طلع زي ما تمنيته بالضبط'),
    (4, 'Good bot, works perfectly. Had a small issue but it was fixed quickly. Will order again.', 'بوت ممتاز، اشتغل بدون مشاكل'),
    (5, 'Best developer I worked with. Understood my requirements immediately and delivered ahead of schedule.', 'أفضل مطور تعاملت معه. فهم متطلباتي فوراً وسلم الشغل قبل الوقت'),
    (3, 'Decent work for the price. Could use some improvements in the design but functionality is solid.', 'شغل مقبول للسعر. يحتاج تحسين في التصميم لكن الوظائف ممتازة'),
    (5, 'The FiveM scripts are incredible! My server runs smoothly and players love the new features.', 'سكريبتات فايف إم خرافية! السيرفر صار يشتغل بسلاسة'),
    (4, 'Quick turnaround on the WordPress fixes. Everything works now. Thanks!', 'إصلاح مشاكل ووردبريس بسرعة. كل شيء شغال الآن. شكراً!'),
    (5, 'Transformed my Figma design into pixel-perfect HTML. Exactly what I needed!', 'حول تصميمي من Figma إلى HTML مضبوط حبة حبة'),
    (5, 'Very patient and professional. Explained everything clearly and made sure I was satisfied.', 'صبر واحترافية. شرح كل شيء بوضوح وتأكد من رضاي'),
    (2, 'Work was okay but took longer than expected. Communication could be better.', 'الشغل كان مقبول لكن أخذ وقت أطول من المتوقع'),
    (5, 'Automation script saved me hours of manual work every day. Worth every penny!', 'سكريبت الأتمتة وفر علي ساعات كل يوم. يستحق كل قرش!'),
    (4, 'Good experience overall. The bot does exactly what I asked for. Would recommend.', 'تجربة جيدة. البوت يسوي بالضبط اللي طلبته'),
    (5, 'FiveM server setup was flawless. Custom scripts work perfectly. This guy knows his stuff!', 'إعداد سيرفر فايف إم كان ممتاز. هذا الشخص يفهم شغله!'),
    (5, 'Second time ordering. Consistent quality and fast delivery. My go-to developer now.', 'ثاني مرة أطلب. جودة ثابتة وتسليم سريع. هذا مطوّري المفضل الآن'),
    (4, 'Great bug fixing service. Found and fixed issues in my code that I had been struggling with for days.', 'خدمة ممتازة في إصلاح الأخطاء. لقى وحل مشاكل كنت أعاني منها أيام'),
]

for rating, comment_en, comment_ar in reviews_data:
    user = random.choice(users)
    product = random.choice(products)
    days_ago = random.randint(1, 60)
    date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')

    comment = f'{comment_en} / {comment_ar}' if random.random() > 0.3 else comment_en

    db.execute('''INSERT INTO reviews (user_id, product_id, rating, comment, created_at)
        VALUES (?,?,?,?,?)''', (user[0], product[0], rating, comment, date))

conn.commit()
conn.close()
print(f'Added {len(reviews_data)} fake reviews!')
