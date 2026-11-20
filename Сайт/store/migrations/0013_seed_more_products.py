from django.db import migrations


MORE_PRODUCTS = [
    ("iphone", "iPhone 17", "iphone-17", "Hamyonbop kuch. Kundalik hayot uchun mukammal.", 11499000, "#d7d7d2", "Qora", "phone", "Mashhur", "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=1200&q=85"),
    ("iphone", "iPhone 17 Air", "iphone-17-air", "O'ta ingichka. O'ta yengil. O'ta zamonaviy.", 12999000, "#cad0d8", "Moviy", "phone", "Yangi", "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=1200&q=85"),
    ("iphone", "iPhone 16", "iphone-16", "Smartfonning barcha kerakli imkoniyatlari.", 8999000, "#aebcca", "Ko'k", "phone", "", "https://images.unsplash.com/photo-1710029617817-779dfd3a6447?auto=format&fit=crop&w=1200&q=85"),
    ("iphone", "iPhone 16e", "iphone-16e", "Zamonaviy iPhone tajribasi qulay narxda.", 7499000, "#d9d5ca", "Oq", "phone", "Yangi", "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=1200&q=85"),
    ("iphone", "iPhone 15", "iphone-15", "Dynamic Island va kuchli kamera bilan.", 6999000, "#cfd8a6", "Yashil", "phone", "Aksiya", "https://images.unsplash.com/photo-1695048133142-1a20484d2569?auto=format&fit=crop&w=1200&q=85"),
    ("mac", "MacBook Pro 14", "macbook-pro-14", "Professional ishlar uchun kuchli noutbuk.", 24999000, "#b9b6b1", "Kosmos rang", "laptop", "Pro", "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=1200&q=85"),
    ("mac", "MacBook Pro 16", "macbook-pro-16", "Katta ekran. Maksimal unumdorlik.", 31999000, "#c0bdb7", "Kumush", "laptop", "Pro", "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=1200&q=85"),
    ("mac", "iMac 24", "imac-24", "Rang va ijod bilan to'la ish stoli.", 18999000, "#9dbfd4", "Ko'k", "laptop", "Yangi", "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?auto=format&fit=crop&w=1200&q=85"),
    ("mac", "Mac mini", "mac-mini", "Kichik korpus. Juda katta quvvat.", 8499000, "#bbb8b3", "Kosmos rang", "laptop", "", "https://images.unsplash.com/photo-1542393545-10f5cde2c810?auto=format&fit=crop&w=1200&q=85"),
    ("ipad", "iPad Air", "ipad-air", "Yengil, rangdor va juda samarali.", 8499000, "#c1aeda", "Binafsha", "tablet", "Mashhur", "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=1200&q=85"),
    ("ipad", "iPad mini", "ipad-mini", "Kichik o'lchamda katta imkoniyatlar.", 6499000, "#c8c6c2", "Kumush", "tablet", "", "https://images.unsplash.com/photo-1585790050230-5dd28404ccb9?auto=format&fit=crop&w=1200&q=85"),
    ("ipad", "iPad 11", "ipad-11", "O'qish va o'yin uchun qulay planshet.", 4999000, "#c4d2c1", "Yashil", "tablet", "Yangi", "https://images.unsplash.com/photo-1561154464-82e9adf32764?auto=format&fit=crop&w=1200&q=85"),
    ("watch", "Apple Watch Series 11", "apple-watch-series-11", "Sog'lik va kundalik hayot uchun aqlli hamroh.", 6499000, "#c8c1bb", "Tilla", "watch", "Yangi", "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?auto=format&fit=crop&w=1200&q=85"),
    ("watch", "Apple Watch SE", "apple-watch-se", "Muhim imkoniyatlar qulay narxda.", 3999000, "#c7d0d8", "Moviy", "watch", "Aksiya", "https://images.unsplash.com/photo-1557438159-51eec7a6c9e8?auto=format&fit=crop&w=1200&q=85"),
    ("watch", "Apple Watch Ultra 2", "apple-watch-ultra-2", "Ekstremal sayohat va sport uchun.", 11999000, "#d08b51", "Tabiiy titan", "watch", "Pro", "https://images.unsplash.com/photo-1544117519-31a4b719223d?auto=format&fit=crop&w=1200&q=85"),
]


def seed_more_products(apps, _schema_editor):
    Category = apps.get_model("store", "Category")
    Product = apps.get_model("store", "Product")

    for category_slug, name, slug, tagline, price, color, finish, visual, badge, image_url in MORE_PRODUCTS:
        category = Category.objects.get(slug=category_slug)
        Product.objects.update_or_create(
            slug=slug,
            defaults={
                "category": category,
                "name": name,
                "tagline": tagline,
                "price": price,
                "color": color,
                "finish": finish,
                "visual": visual,
                "badge": badge,
                "image_url": image_url,
                "is_featured": True,
            },
        )


def remove_more_products(apps, _schema_editor):
    Product = apps.get_model("store", "Product")
    slugs = [product[2] for product in MORE_PRODUCTS]
    Product.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):
    dependencies = [("store", "0012_product_description_highlights")]

    operations = [migrations.RunPython(seed_more_products, remove_more_products)]
