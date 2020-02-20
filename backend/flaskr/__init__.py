import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# ------------------------------------
# To paginate 10 questions per page
# -------------------------------------
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  # setting up cors
  CORS(app , resources={r'/*': {'origins': '*'}})

  #----------------------------
  # setting acess control allow
  #----------------------------
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers','Content-type,Authorization,true')
      response.headers.add('Access-Control-Allow-Headers','GET,PUT,POST,PATCH,DELETE,OPTIONS')
      return response




  @app.route('/categories' , methods=['GET'])
  def get_all_categories():
      categories = {}

      for category in Category.query.all():
          categories[category.id] = category.type

      return jsonify({
            'success' : True,
            'categories' : categories
        })



  # endpoint to get all questions
  @app.route('/questions' , methods=['GET'])
  def get_questions():
      categories = {}
      for category in Category.query.all():
          categories[category.id] = category.type
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      if len(current_questions) == 0:
          abort(404)

      return jsonify({
            'success':True,
            'questions':current_questions,
            'total_questions':len(current_questions),
            'categories':categories
       })

  # endpoint to delete specific question
  @app.route('/questions/<int:que_id>', methods=['DELETE'])
  def delete_question(que_id):
      try:
          question = Question.query.filter(Question.id == que_id).one_or_none()
          question.delete()

          return jsonify({
            'success':True,
            'deleted':que_id
            })
      except:
         abort(404)

  # endpoint to create new question
  @app.route('/questions',methods=['POST'])
  def add_questions():
      body = request.get_json()
      new_question   = body.get('question')
      new_answer     = body.get('answer')
      new_difficulty = body.get('difficulty')
      new_category   = body.get('category')
      try:
          if not (question and answer and category and difficulty):
            return abort(400)
          question = Question(question=new_question,answer=new_answer,difficulty=new_difficulty,category=new_category)
          question.insert()
          return jsonify({
          'success':True,
          'created':question.id
          })
      except:
          abort(422)

  # endpoint to search for questions
  @app.route('/questions/search',methods=['POST'])
  def search_questions():
      body = request.get_json()
      search_term = body.get('searchTerm',None)

      if search_term:
           search_results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

           return jsonify({
                'success': True,
                'questions': [question.format() for question in search_results],
                'total_questions': len(search_results),
                'current_category': None
           })
      else:
          abort(404)


  # endpoint to get questions for a specific category
  @app.route('/categories/<int:category_id>/questions')
  def get_question_by_id(category_id):
      questions  = Question.query.filter(Question.category == category_id).order_by(Question.id).all()

      return jsonify({
                'success': True,
                'questions': [question.format() for question in questions],
                'total_questions': len(questions),
                'current_category': category_id
            })


  # endpoint to play the quiz
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():

        try:
            body = request.get_json()
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)

            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_((previous_questions))).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_((previous_questions))).all()

            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(422)



# error handlers
  @app.errorhandler(404)
  def not_found(error):
      return jsonify({
        'success':False,
        'error':404,
        'message':'resource not found'
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
      return jsonify({
        'success':False,
        'error':422,
        'message':'unprocessable'
      }), 422
  @app.errorhandler(400)
  def bad_request(error):
      return jsonify({
      'success':False,
      'error':400,
      'message':'corrupt request'
      }),400
  @app.errorhandler(405)
  def not_allowed(error):
      return jsonify({
        'success':False,
        'error':405,
        'message':'method not allowed'
      }), 405
  return app
