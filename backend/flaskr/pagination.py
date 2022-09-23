"""
function to paginate questions
returns 10 questions per page
"""

def paginate(request, selection, QUESTIONS_PER_PAGE):
    page = request.args.get("page", 1, type=int)
    start = (page -1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question for question in selection]
    return questions[start:end]