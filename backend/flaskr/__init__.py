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
        categories_list = [category.format() for category in categories]

        return jsonify(
            {
                "success": True,
                "questions": questions,
                "total_questions": len(Question.query.all()),
                "categories": categories_list,
                "current_category": None,
            }
        )

    @app.route("/categories/<int:category_id>/questions", methods=["GET"])
    def get_questions_by_category(category_id):

        """
        since the member category of the class Question is a string and the provided
        category_id is an int value, it is necessary to cast the category_id to string data type
        """
        category = str(category_id)

        # fetch all the questions of the same category as the category_id parameter
        questions = (
            Question.query.filter(Question.category == category)
            .order_by(Question.difficulty)
            .all()
        )
        if len(questions) != 0:

            # paginate the questions
            paginated_questions = paginate(request, questions, QUESTIONS_PER_PAGE)
            questions_list = [question.format() for question in paginated_questions]
            categories = Category.query.order_by(Category.type).all()
            formatted_categories = [c.format() for c in categories]
            all_questions = Question.query.all()
            return jsonify(
                {
                    "success": True,
                    "questions": questions_list,
                    "total_questions": len(all_questions),
                    "categories": formatted_categories,
                    "current_category": None,
                }
            )
        else:
            abort(404)

    @app.route("/quizzes", methods=["POST"])
    def play_quiz():
        body = request.get_json()

        # previous_questions(as defined in QuizView.js line 57 col 9)
        previous_questions = body.get("previous_questions")

        # quiz_category (as specified in QuizView.js source file, line 58 col 9)
        quiz_category = body.get("quiz_category")

        next_question = []

        try:
            """
            assuming that the the request provides th previous_question as a list of question IDs
            ( QuizView.js source file at line 93 col 7)
            """
            # check if there a any previous questions
            if quiz_category == None and len(previous_questions) == 0:
                questions = Question.query.order_by(Question.difficulty).all()
                questions_list = [q.format() for q in questions]
                index = random.randint(0, len(questions_list) - 1)
                next_question.append(questions_list[index])

            else:
                # fetch all the questions of a given category
                questions = Question.query.filter(
                    Question.category == quiz_category
                ).all()
                questions_list = [q.format() for q in questions]

                # filter questions that have not been displayed to the user
                available_questions = questions_list not in previous_questions
                index = random.randint(0, len(available_questions) - 1)

                # choose a random question
                next_question.append(available_questions[index])

            return jsonify(
                {
                    "success": True,
                    "question": next_question,
                }
            )

        except:
            abort(422)

    """
    function to handle 'not found' error (404)
    """

    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify(
                {
                    "success": False,
                    "error": 404,
                    "message": "Resource not found",
                }
            ),
            404,
        )

    """
    function to handle 'method not allowed' error (405)
    """

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify(
            {"success": False, "error": 405, "message": "method not allowed"}
        ), 405

    """
    function to handle 'unprocessable entity' error
    """

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify(
                {
                    "sucess": False,
                    "error": 422,
                    "message": "Unprocessable entity",
                }
            ),
            422,
        )

    return app
