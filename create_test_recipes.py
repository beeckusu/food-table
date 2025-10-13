#!/usr/bin/env python
"""
Script to create test recipe records for FT-16
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from content.models import Recipe, Encyclopedia
from django.contrib.auth.models import User
from django.utils.text import slugify

# Get or create a user
user, _ = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True}
)

# Create test recipes
recipes_data = [
    {
        'name': 'Classic Margherita Pizza',
        'description': 'A simple and delicious pizza with fresh mozzarella, tomatoes, and basil. The perfect introduction to homemade pizza making.',
        'servings': 4,
        'prep_time_minutes': 20,
        'cook_time_minutes': 15,
        'total_time_minutes': 35,
        'difficulty': 'easy',
        'ingredients': [
            {'item': 'pizza dough', 'quantity': '1 lb', 'notes': 'store-bought or homemade'},
            {'item': 'tomato sauce', 'quantity': '1 cup', 'notes': 'good quality'},
            {'item': 'fresh mozzarella', 'quantity': '8 oz', 'notes': 'sliced'},
            {'item': 'fresh basil leaves', 'quantity': '1/4 cup', 'notes': ''},
            {'item': 'olive oil', 'quantity': '2 tbsp', 'notes': 'extra virgin'},
            {'item': 'salt', 'quantity': 'to taste', 'notes': ''},
        ],
        'steps': [
            {'order': 1, 'instruction': 'Preheat oven to 475°F (245°C) with a pizza stone if you have one.', 'time_minutes': 15},
            {'order': 2, 'instruction': 'Roll out pizza dough on a floured surface to desired thickness.', 'time_minutes': 5},
            {'order': 3, 'instruction': 'Spread tomato sauce evenly over the dough, leaving a 1-inch border.', 'time_minutes': 2},
            {'order': 4, 'instruction': 'Distribute mozzarella slices evenly over the sauce.', 'time_minutes': 2},
            {'order': 5, 'instruction': 'Drizzle with olive oil and season with salt.', 'time_minutes': 1},
            {'order': 6, 'instruction': 'Bake for 12-15 minutes until crust is golden and cheese is bubbly.', 'time_minutes': 15},
            {'order': 7, 'instruction': 'Remove from oven, top with fresh basil, slice and serve.', 'time_minutes': 2},
        ],
        'tips': 'For best results, use a pizza stone preheated in the oven. If you don\'t have one, use an inverted baking sheet. The key is high heat!',
        'dietary_restrictions': ['vegetarian'],
    },
    {
        'name': 'Beef Bourguignon',
        'description': 'A classic French beef stew braised in red wine with carrots, onions, and mushrooms. Rich, hearty, and perfect for special occasions.',
        'servings': 6,
        'prep_time_minutes': 30,
        'cook_time_minutes': 180,
        'total_time_minutes': 210,
        'difficulty': 'hard',
        'ingredients': [
            {'item': 'beef chuck', 'quantity': '3 lbs', 'notes': 'cut into 2-inch cubes'},
            {'item': 'red wine', 'quantity': '3 cups', 'notes': 'good quality Burgundy'},
            {'item': 'pearl onions', 'quantity': '1 lb', 'notes': 'peeled'},
            {'item': 'carrots', 'quantity': '4 large', 'notes': 'cut into chunks'},
            {'item': 'mushrooms', 'quantity': '1 lb', 'notes': 'quartered'},
            {'item': 'bacon', 'quantity': '6 oz', 'notes': 'diced'},
            {'item': 'tomato paste', 'quantity': '2 tbsp', 'notes': ''},
            {'item': 'beef stock', 'quantity': '2 cups', 'notes': ''},
            {'item': 'garlic cloves', 'quantity': '4', 'notes': 'minced'},
            {'item': 'thyme', 'quantity': '2 sprigs', 'notes': 'fresh'},
            {'item': 'bay leaves', 'quantity': '2', 'notes': ''},
            {'item': 'flour', 'quantity': '1/4 cup', 'notes': 'for coating'},
        ],
        'steps': [
            {'order': 1, 'instruction': 'Pat beef dry and season with salt and pepper. Coat lightly with flour.', 'time_minutes': 10},
            {'order': 2, 'instruction': 'In a Dutch oven, cook bacon until crispy. Remove and set aside.', 'time_minutes': 8},
            {'order': 3, 'instruction': 'Brown beef in batches in bacon fat. Set aside with bacon.', 'time_minutes': 15},
            {'order': 4, 'instruction': 'Sauté carrots and onions until golden. Add garlic and tomato paste.', 'time_minutes': 10},
            {'order': 5, 'instruction': 'Return beef and bacon to pot. Add wine, stock, thyme, and bay leaves.', 'time_minutes': 5},
            {'order': 6, 'instruction': 'Bring to a boil, cover, and transfer to 325°F oven. Braise for 2.5 hours.', 'time_minutes': 150},
            {'order': 7, 'instruction': 'Sauté mushrooms separately and add to stew 30 minutes before done.', 'time_minutes': 10},
            {'order': 8, 'instruction': 'Remove bay leaves and thyme sprigs. Adjust seasoning and serve.', 'time_minutes': 5},
        ],
        'tips': 'This dish tastes even better the next day! Make it ahead and reheat gently. Serve with crusty bread or over egg noodles.',
        'dietary_restrictions': [],
    },
    {
        'name': 'Quick Chicken Stir Fry',
        'description': 'A fast and healthy weeknight dinner with tender chicken and crisp vegetables in a savory sauce.',
        'servings': 4,
        'prep_time_minutes': 15,
        'cook_time_minutes': 12,
        'total_time_minutes': 27,
        'difficulty': 'easy',
        'ingredients': [
            {'item': 'chicken breast', 'quantity': '1.5 lbs', 'notes': 'sliced thin'},
            {'item': 'bell peppers', 'quantity': '2', 'notes': 'sliced'},
            {'item': 'broccoli florets', 'quantity': '2 cups', 'notes': ''},
            {'item': 'soy sauce', 'quantity': '3 tbsp', 'notes': ''},
            {'item': 'oyster sauce', 'quantity': '2 tbsp', 'notes': ''},
            {'item': 'sesame oil', 'quantity': '1 tbsp', 'notes': ''},
            {'item': 'ginger', 'quantity': '1 tbsp', 'notes': 'minced'},
            {'item': 'garlic', 'quantity': '3 cloves', 'notes': 'minced'},
            {'item': 'cornstarch', 'quantity': '1 tbsp', 'notes': 'mixed with water'},
            {'item': 'vegetable oil', 'quantity': '2 tbsp', 'notes': 'for cooking'},
        ],
        'steps': [
            {'order': 1, 'instruction': 'Mix soy sauce, oyster sauce, sesame oil, and cornstarch slurry in a bowl.', 'time_minutes': 3},
            {'order': 2, 'instruction': 'Heat wok or large skillet over high heat. Add oil.', 'time_minutes': 2},
            {'order': 3, 'instruction': 'Stir-fry chicken until just cooked through, about 4-5 minutes. Remove.', 'time_minutes': 5},
            {'order': 4, 'instruction': 'Add more oil if needed. Stir-fry vegetables for 3-4 minutes.', 'time_minutes': 4},
            {'order': 5, 'instruction': 'Add ginger and garlic, cook for 30 seconds until fragrant.', 'time_minutes': 1},
            {'order': 6, 'instruction': 'Return chicken to wok. Pour in sauce and toss everything together.', 'time_minutes': 2},
            {'order': 7, 'instruction': 'Cook for another minute until sauce thickens. Serve over rice.', 'time_minutes': 2},
        ],
        'tips': 'The key to a good stir fry is high heat and quick cooking. Have all ingredients prepped before you start cooking!',
        'dietary_restrictions': [],
    },
    {
        'name': 'Vegetarian Pad Thai',
        'description': 'Thai rice noodles stir-fried with tofu, vegetables, and a tangy tamarind sauce. A satisfying meat-free take on this classic dish.',
        'servings': 4,
        'prep_time_minutes': 25,
        'cook_time_minutes': 15,
        'total_time_minutes': 40,
        'difficulty': 'medium',
        'ingredients': [
            {'item': 'rice noodles', 'quantity': '8 oz', 'notes': 'flat, medium width'},
            {'item': 'firm tofu', 'quantity': '14 oz', 'notes': 'pressed and cubed'},
            {'item': 'bean sprouts', 'quantity': '2 cups', 'notes': ''},
            {'item': 'green onions', 'quantity': '4', 'notes': 'cut into 2-inch pieces'},
            {'item': 'eggs', 'quantity': '2', 'notes': 'lightly beaten'},
            {'item': 'tamarind paste', 'quantity': '3 tbsp', 'notes': ''},
            {'item': 'fish sauce', 'quantity': '3 tbsp', 'notes': 'or soy sauce for vegan'},
            {'item': 'brown sugar', 'quantity': '2 tbsp', 'notes': ''},
            {'item': 'lime', 'quantity': '2', 'notes': 'cut into wedges'},
            {'item': 'peanuts', 'quantity': '1/2 cup', 'notes': 'crushed'},
            {'item': 'cilantro', 'quantity': '1/4 cup', 'notes': 'chopped'},
        ],
        'steps': [
            {'order': 1, 'instruction': 'Soak rice noodles in warm water for 30 minutes. Drain.', 'time_minutes': 30},
            {'order': 2, 'instruction': 'Mix tamarind paste, fish sauce, and brown sugar for the sauce.', 'time_minutes': 3},
            {'order': 3, 'instruction': 'Heat oil in wok. Fry tofu until golden. Remove and set aside.', 'time_minutes': 5},
            {'order': 4, 'instruction': 'Scramble eggs in the wok, then push to the side.', 'time_minutes': 2},
            {'order': 5, 'instruction': 'Add drained noodles and sauce. Stir-fry for 3-4 minutes.', 'time_minutes': 4},
            {'order': 6, 'instruction': 'Add tofu, bean sprouts, and green onions. Toss to combine.', 'time_minutes': 2},
            {'order': 7, 'instruction': 'Serve topped with peanuts, cilantro, and lime wedges.', 'time_minutes': 2},
        ],
        'tips': 'Don\'t over-soak the noodles - they should still be slightly firm. They\'ll finish cooking in the wok.',
        'dietary_restrictions': ['vegetarian'],
    },
    {
        'name': 'Chocolate Chip Cookies',
        'description': 'The perfect chocolate chip cookie - crispy edges, chewy center, and loaded with chocolate chips.',
        'servings': 24,
        'prep_time_minutes': 15,
        'cook_time_minutes': 12,
        'total_time_minutes': 27,
        'difficulty': 'easy',
        'ingredients': [
            {'item': 'all-purpose flour', 'quantity': '2 1/4 cups', 'notes': ''},
            {'item': 'butter', 'quantity': '1 cup', 'notes': 'softened'},
            {'item': 'granulated sugar', 'quantity': '3/4 cup', 'notes': ''},
            {'item': 'brown sugar', 'quantity': '3/4 cup', 'notes': 'packed'},
            {'item': 'eggs', 'quantity': '2', 'notes': 'large'},
            {'item': 'vanilla extract', 'quantity': '2 tsp', 'notes': ''},
            {'item': 'baking soda', 'quantity': '1 tsp', 'notes': ''},
            {'item': 'salt', 'quantity': '1 tsp', 'notes': ''},
            {'item': 'chocolate chips', 'quantity': '2 cups', 'notes': 'semi-sweet'},
        ],
        'steps': [
            {'order': 1, 'instruction': 'Preheat oven to 375°F (190°C).', 'time_minutes': 10},
            {'order': 2, 'instruction': 'Cream together butter and both sugars until fluffy.', 'time_minutes': 3},
            {'order': 3, 'instruction': 'Beat in eggs and vanilla extract.', 'time_minutes': 2},
            {'order': 4, 'instruction': 'In separate bowl, whisk together flour, baking soda, and salt.', 'time_minutes': 2},
            {'order': 5, 'instruction': 'Gradually mix dry ingredients into wet ingredients.', 'time_minutes': 2},
            {'order': 6, 'instruction': 'Fold in chocolate chips.', 'time_minutes': 1},
            {'order': 7, 'instruction': 'Drop rounded tablespoons onto ungreased baking sheets.', 'time_minutes': 5},
            {'order': 8, 'instruction': 'Bake for 9-11 minutes until golden brown. Cool on baking sheet.', 'time_minutes': 12},
        ],
        'tips': 'For chewier cookies, slightly underbake them. They\'ll continue cooking on the hot pan after removal from oven.',
        'dietary_restrictions': ['vegetarian'],
    },
]

print("Creating test recipes...")
created_count = 0

for recipe_data in recipes_data:
    slug = slugify(recipe_data['name'])

    # Check if recipe already exists
    if Recipe.objects.filter(slug=slug).exists():
        print(f"Recipe '{recipe_data['name']}' already exists, skipping...")
        continue

    # Create the recipe
    recipe = Recipe.objects.create(
        name=recipe_data['name'],
        slug=slug,
        description=recipe_data['description'],
        servings=recipe_data['servings'],
        prep_time_minutes=recipe_data['prep_time_minutes'],
        cook_time_minutes=recipe_data['cook_time_minutes'],
        total_time_minutes=recipe_data['total_time_minutes'],
        difficulty=recipe_data['difficulty'],
        ingredients=recipe_data['ingredients'],
        steps=recipe_data['steps'],
        tips=recipe_data['tips'],
        dietary_restrictions=recipe_data['dietary_restrictions'],
        created_by=user,
        is_private=False,
    )

    print(f"[OK] Created recipe: {recipe.name}")
    created_count += 1

print(f"\nDone! Created {created_count} new recipes.")
print(f"Total recipes in database: {Recipe.objects.count()}")
