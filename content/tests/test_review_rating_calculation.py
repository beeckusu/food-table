from django.test import TestCase
from django.contrib.auth.models import User
from datetime import date, time
from content.models.review import Review
from content.models.review_dish import ReviewDish


class ReviewRatingCalculationTestCase(TestCase):
    """
    Test cases for automatic overall rating calculation from dish ratings.
    Implements FT-76: Auto-calculate overall rating from dish ratings when not provided.
    """

    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_new_review_without_rating_defaults_to_50(self):
        """Test that a new review without rating gets default value of 50"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided
            created_by=self.user
        )
        self.assertEqual(review.rating, 50)

    def test_new_review_with_explicit_rating_is_preserved(self):
        """Test that a new review with explicit rating keeps that rating"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=75,  # Explicitly set
            created_by=self.user
        )
        self.assertEqual(review.rating, 75)

    def test_review_rating_calculated_from_single_dish(self):
        """Test rating calculation with a single dish"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        # Add a dish with rating
        ReviewDish.objects.create(
            review=review,
            dish_name="Pasta",
            dish_rating=80
        )

        # Refresh from database
        review.refresh_from_db()
        self.assertEqual(review.rating, 80)

    def test_review_rating_calculated_from_multiple_dishes(self):
        """Test rating calculation as average of multiple dish ratings"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        # Add multiple dishes with different ratings
        ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=80)
        ReviewDish.objects.create(review=review, dish_name="Pizza", dish_rating=90)
        ReviewDish.objects.create(review=review, dish_name="Salad", dish_rating=70)

        # Refresh from database
        review.refresh_from_db()
        # Average: (80 + 90 + 70) / 3 = 80
        self.assertEqual(review.rating, 80)

    def test_review_rating_rounds_correctly(self):
        """Test that rating calculation rounds to nearest integer"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        # Add dishes that average to 83.333...
        ReviewDish.objects.create(review=review, dish_name="Dish 1", dish_rating=80)
        ReviewDish.objects.create(review=review, dish_name="Dish 2", dish_rating=85)
        ReviewDish.objects.create(review=review, dish_name="Dish 3", dish_rating=85)

        review.refresh_from_db()
        # Average: (80 + 85 + 85) / 3 = 83.333... -> rounds to 83
        self.assertEqual(review.rating, 83)

    def test_review_rating_ignores_unrated_dishes(self):
        """Test that dishes without ratings are ignored in calculation"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        # Add mix of rated and unrated dishes
        ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=80)
        ReviewDish.objects.create(review=review, dish_name="Pizza", dish_rating=None)  # No rating
        ReviewDish.objects.create(review=review, dish_name="Salad", dish_rating=90)

        review.refresh_from_db()
        # Average: (80 + 90) / 2 = 85 (ignoring unrated Pizza)
        self.assertEqual(review.rating, 85)

    def test_review_with_no_rated_dishes_defaults_to_50(self):
        """Test that review with only unrated dishes defaults to 50"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        # Add dishes without ratings
        ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=None)
        ReviewDish.objects.create(review=review, dish_name="Pizza", dish_rating=None)

        review.refresh_from_db()
        self.assertEqual(review.rating, 50)

    def test_review_rating_updates_when_dish_rating_changes(self):
        """Test that overall rating updates when dish rating is modified"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        dish = ReviewDish.objects.create(
            review=review,
            dish_name="Pasta",
            dish_rating=80
        )

        review.refresh_from_db()
        self.assertEqual(review.rating, 80)

        # Update dish rating
        dish.dish_rating = 90
        dish.save()

        review.refresh_from_db()
        self.assertEqual(review.rating, 90)

    def test_review_rating_updates_when_dish_deleted(self):
        """Test that overall rating updates when a dish is deleted"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        dish1 = ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=80)
        dish2 = ReviewDish.objects.create(review=review, dish_name="Pizza", dish_rating=90)

        review.refresh_from_db()
        self.assertEqual(review.rating, 85)  # Average: (80 + 90) / 2

        # Delete one dish
        dish2.delete()

        review.refresh_from_db()
        self.assertEqual(review.rating, 80)  # Only dish1 remains

    def test_review_rating_reverts_to_50_when_all_dishes_deleted(self):
        """Test that overall rating reverts to 50 when all dishes are deleted"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        dish = ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=80)

        review.refresh_from_db()
        self.assertEqual(review.rating, 80)

        # Delete the dish
        dish.delete()

        review.refresh_from_db()
        self.assertEqual(review.rating, 50)

    def test_explicit_rating_not_overwritten_by_dish_addition(self):
        """Test that explicitly set rating is NOT overwritten when dishes are added"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=95,  # Explicitly set high rating
            created_by=self.user
        )

        # Verify it's not marked as auto-calculated
        self.assertFalse(review.metadata.get('rating_auto_calculated', False))

        # Add a dish with lower rating
        ReviewDish.objects.create(review=review, dish_name="Pasta", dish_rating=70)

        # The review rating should NOT change because it was explicitly set
        review.refresh_from_db()
        self.assertEqual(review.rating, 95)

    def test_rating_with_extreme_values(self):
        """Test rating calculation with boundary values (0 and 100)"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # Not provided - will be auto-calculated
            created_by=self.user
        )

        ReviewDish.objects.create(review=review, dish_name="Terrible", dish_rating=0)
        ReviewDish.objects.create(review=review, dish_name="Perfect", dish_rating=100)

        review.refresh_from_db()
        # Average: (0 + 100) / 2 = 50
        self.assertEqual(review.rating, 50)

    def test_metadata_flag_set_for_auto_calculated_rating(self):
        """Test that metadata flag is set when rating is auto-calculated"""
        # Review with no rating (0) should be auto-calculated
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=0,  # No rating provided
            created_by=self.user
        )

        review.refresh_from_db()
        self.assertTrue(review.metadata.get('rating_auto_calculated', False))

    def test_metadata_flag_not_set_for_explicit_rating(self):
        """Test that metadata flag is NOT set when rating is explicitly provided"""
        review = Review.objects.create(
            restaurant_name="Test Restaurant",
            visit_date=date(2025, 10, 31),
            entry_time=time(18, 30),
            party_size=2,
            rating=75,  # Explicitly provided
            created_by=self.user
        )

        review.refresh_from_db()
        self.assertFalse(review.metadata.get('rating_auto_calculated', False))
