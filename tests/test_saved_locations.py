"""Unit tests for 5-location cap limit and management."""
import unittest
import uuid
from backend.database.db import (
    init_db,
    add_saved_location,
    delete_saved_location,
    get_saved_locations,
    count_saved_locations
)

class TestSavedLocationsLimit(unittest.TestCase):

    def setUp(self):
        init_db()
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        # Clean up any test locations created
        locations = get_saved_locations(self.test_user_id)
        for loc in locations:
            delete_saved_location(loc["id"], self.test_user_id)

    def test_maximum_5_locations_enforced(self):
        """
        Verify that a user can save up to 5 locations,
        and attempting to save a 6th location raises a ValueError with the exact required message:
        'You can save up to 5 farming locations.'
        """
        # Save 5 locations
        for i in range(1, 6):
            loc = add_saved_location(
                name=f"Test Field {i}",
                latitude=16.0 + (i * 0.1),
                longitude=80.0 + (i * 0.1),
                district="Guntur",
                state="Andhra Pradesh",
                user_id=self.test_user_id
            )
            self.assertIsNotNone(loc["id"])

        self.assertEqual(count_saved_locations(self.test_user_id), 5)

        # Attempt to save 6th location - MUST FAIL
        with self.assertRaises(ValueError) as context:
            add_saved_location(
                name="Forbidden 6th Field",
                latitude=16.9,
                longitude=80.9,
                district="Guntur",
                state="Andhra Pradesh",
                user_id=self.test_user_id
            )

        self.assertIn("You can save up to 5 farming locations.", str(context.exception))
        self.assertEqual(count_saved_locations(self.test_user_id), 5)

    def test_delete_and_replace_location(self):
        """Deleting an existing location should allow adding a new one up to 5."""
        loc1 = add_saved_location("Field A", 16.1, 80.1, user_id=self.test_user_id)
        loc2 = add_saved_location("Field B", 16.2, 80.2, user_id=self.test_user_id)
        self.assertEqual(count_saved_locations(self.test_user_id), 2)

        delete_saved_location(loc1["id"], self.test_user_id)
        self.assertEqual(count_saved_locations(self.test_user_id), 1)

if __name__ == "__main__":
    unittest.main()
