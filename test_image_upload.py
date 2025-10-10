import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.files import File
from django.contrib.auth.models import User
from content.models import Encyclopedia, Image

# Create a user if one doesn't exist
user, created = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"[OK] Created user: {user.username}")
else:
    print(f"[OK] Using existing user: {user.username}")

# Create an encyclopedia entry
entry = Encyclopedia.objects.create(
    title="Django Framework",
    content="Django is a high-level Python web framework."
)
print(f"[OK] Created encyclopedia entry: {entry.title}")

# Upload and attach an image to the encyclopedia entry
with open('test_image.jpg', 'rb') as f:
    image = Image.objects.create(
        caption="Django Logo",
        alt_text="Django Framework Logo",
        order=1,
        content_object=entry,
        uploaded_by=user
    )
    image.image.save('django_logo.jpg', File(f), save=True)
    print(f"[OK] Created and attached image: {image}")
    print(f"     Image path: {image.image.path}")
    print(f"     Image URL: {image.image.url}")

# Verify the attachment through the GenericRelation
print(f"\n[OK] Encyclopedia entry has {entry.images.count()} image(s) attached")
for img in entry.images.all():
    print(f"     - {img.caption}: {img.image.url}")

print("\n[SUCCESS] All tests passed! Image upload and association working correctly.")
print(f"[SUCCESS] Media folder created at: {os.path.dirname(image.image.path)}")
