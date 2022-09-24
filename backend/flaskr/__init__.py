import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from .pagination import paginate

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app)

    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"
        )
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Types, Authorization, True"
        )
        response.headers.add("Access-Control-Allow-Origin", "*")

        return response

    """
    get_categories endpoint
    """

    @app.route("/categories", methods=["GET"])
    def get_categories():
        # retrieve categories and sort by category types
        categories = Category.query.order_by(Category.type).all()
        categories_list = [category.format() for category in categories]

        if len(categories_list) != 0:

            return jsonify(
                {
                    "success": True,
                    "categories": categories_list,
                }
            )
        else:
            # abort if the query result is empty
            abort(404)

    """
    get_questions endpoint
    """

    @app.route("/questions", methods=["GET"])
    def get_questions():

        # fetch from the db all the available questions
        # the questions are ordered by difficulty
        questions = Question.query.all()
        # format questions objects. Otherwise, it will throw 'TypeError: Object of type X is not JSON serializable' exception
        questions_list = [question.format() for question in questions]
        # paginate the questions in order to display ten questions per page
        paginated_questions = paginate(request, questions_list, QUESTIONS_PER_PAGE)
        # fetch all categories from the database
        categories = Category.query.order_by(Category.type).all()
        # format the categories
        formatted_categories = [category.format() for category in categories]

        if len(questions) != 0:
            # return a JSON object in a format as expected in QuestionView.js source file
            return jsonify(
                {
                    "success": True,
                    "questions": paginated_questions,
                    "total_questions": len(questions_list),
                    "category": formatted_categories,
                    "current_category": None,
                }
            )
        else:
            # Throw 404 http error when empty questions list is returned from the database queries
            abort(404)

    """
    delete_question endpoint
    """

    @app.route("/questions/<int:question_id>", methods=["DELETE"])
    def delete_question(question_id):
        # fetch the question with the provided question_id
        question = Question.query.filter(Question.id == question_id).one_or_none()
        if question == None:
            # alert the user when the provided question ID is not valid
            abort(422)
        else:

            # delete the question with the matching question_id provided by the user
            question.delete()

            # fetch the current questions present in the 'questions' table after the deletion
            questions_list = Question.query.all()

            # query the categories
            categories_list = Category.query.order_by(Category.type).all()

            # paginate the questions
            paginated_questions = paginate(request, questions_list, QUESTIONS_PER_PAGE)
            categories = [category.format() for category in categories_list]
            return jsonify(
                {
                    "success": True,
                    "questions": [q.format() for q in paginated_questions],
                    "total_questions": len(questions_list),
                    "categories": categories,
                    "current_category": None,
                }
            )

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """

    @app.route("/questions/create", methods=["POST"])
    def add_question():

        try:
            """
            instantiate a Question object and initialize with the data retrieved from
            the form as is in the FormView.js source file
            """
            question = Question(
                question=request.json.get("question"),
                answer=request.json.get("answer"),
                category=request.json.get("category"),
                difficulty=request.json.get("difficulty"),
            )

            # persist the inserted question in the database
            question.insert()

            # return a JSON object with success value and the ID of the added question
            return jsonify(
                {
                    "success": True,
                    "created": question.id,
                }
            )
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """

    @app.route("/question/search", methods=["POST"])
    def search_question():
        body = request.get_json()

        # searchTerm is a key of JSON returned in QuestionView.js source file, line 91 col 30
        search_term = body.get("searchTerm")

        if search_term is None:
            abort(404)
        # fetch any question whom the search term is a substring of a question
        matching_questions = (
            Question.query.filter(Question.question.ilike(f"%{search_term}%"))
            .order_by(Question.difficulty)
            .all()
        )
        categories = Category.query.order_by(Category.type).all()
        questions = [question.format() for question in matching_questions]

        return jsonify(
            {
                "success": True,
                "questions": questions,
                "total_questions": len(Question.query.all()),
                "categories": [category.format() for category in categories],
                "current_category": None,
            }
        )

    """
    @TODO:
    Create a GET endpoint to get questions based on category.
    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):

        """
        since the member category of the class Question is a string and the provided 
        category_id is an int value, it is necessary to cast the category_id to string data type
        """
        category = str(category_id)
        
        # fetch all the questions of the same category as the category_id parameter
        questions = Question.query.filter(Question.category == category).order_by(Question.difficulty).all()
        if len(questions) != 0:
        
            # paginate the questions
            paginated_questions = paginate(request, questions, QUESTIONS_PER_PAGE)
            questions_list = [question.format() for question in paginated_questions]
            categories = Category.query.order_by(Category.type).all()
            return jsonify({
                "success": True,
                "questions": questions_list,
                "total_questions": len(Question.query.all()),
                "categories": [c.format() for c in categories],
                "current_category": None,
            })
        else:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """

    return app
