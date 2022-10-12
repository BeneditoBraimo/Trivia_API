import os
import unittest
import json
from flask import request
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_user = "postgres"
        self.database_password = "abc"
        self.database_name = "trivia_test"
        self.database_path = "postgresql://{}:{}@{}/{}".format(self.database_user, self.database_password,'localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_categories(self):
        res = self.client().get("/categories")
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertGreater(len(data["categories"]), 0)

    def test_404_get_non_existing_category(self):
        res = self.client().get("/categories/88")
        data = json.loads(res.data)

        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "Resource not found")
        self.assertEqual(data["error"], 404)

    def test_get_questions(self):
        res = self.client().get("/questions")
        data = json.loads(res.data)

        self.assertEqual(data["success"], True)
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(data["questions"]), 0)
        self.assertTrue(data["total_questions"])

    def test_405_get_question(self):
        res = self.client().get("/questions/5")
        data =json.loads(res.data)
        self.assertNotEqual(res.status_code, 200)
        self.assertNotEqual(data["success"], True)
        self.assertEqual(data["error"], 405)
        self.assertEqual(data["message"],"Method not allowed")

    def test_delete_question(self):
        res = self.client().delete("/questions/4")
        data = json.loads(res.data)

        self.assertNotEqual(res.status_code, 422)
        self.assertNotEqual(data["success"], False)

# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()