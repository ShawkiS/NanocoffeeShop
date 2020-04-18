import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

## ROUTES
@app.route('/drinks')
def get_drinks():
    try:
        return jsonify({
            'success': True,
            'drinks': [drink.short() for drink in Drink.query.all()]
        }), 200
    except Exception:
        abort(404)


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    try:
        query = Drink.query.all()

        if query is None:
            abort(400)

        return jsonify({
            'success': True,
            'drinks': [drink.long() for drink in query]
        }), 200
    except Exception:
        abort(404)


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_new_drink(payload):
    body = request.get_json()
    try:
        drink = Drink(
            title=body.get('title'),
            recipe=json.dumps(body.get('recipe'))
        )
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        }), 200
    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()
    drink = Drink.query.filter(Drink.id == drink_id).first()
    title = body['title']
    recipe = body.get('recipe')

    if (body is {} or title is None or drink is None):
        abort(400)
    try:
        drink.title = title
        drink.recipe = json.dumps([recipe])
        drink.update()

        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200
    except Exception:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    drink = Drink.query.filter(Drink.id == drink_id).first()

    if drink is None:
        abort(404)
    try:
        drink.delete()

        return jsonify({
            'success': True,
            'delete': drink_id
        }), 200
    except Exception:
        abort(422)

# Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 400,
        'message': 'Bad request'
    }), 400

@app.errorhandler(401)
def not_authorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Not authorized"
    }), 401


@app.errorhandler(403)
def forbidden(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": "Forbidden"
    }), 403


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'Not found'
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 405,
        'message': 'Method not allowed'
    }), 405


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    'success': False,
                    'error': 422,
                    'message': 'unprocessable'
                    }), 422


@app.errorhandler(500)
def server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal server error"
    }), 500


@app.errorhandler(AuthError)
def autherror(error):
    print(error)
    return jsonify({
        'success': False,
        'error': error.status_code,
        'message': error.error['description']
    }), error.status_code