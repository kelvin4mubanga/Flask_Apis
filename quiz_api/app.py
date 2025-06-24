
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'))
        

class CategoryList(Resource):
    def get(self):
        return [{'id': c.id, 'name': c.name} for c in Category.query.all()]

    def post(self):
        data = request.get_json()
        cat = Category(name=data['name'])
        db.session.add(cat)
        db.session.commit()
        return {'message': 'Category created'}, 201

class QuestionList(Resource):
    def get(self):
        return [{'id': q.id, 'content': q.content, 'category_id': q.category_id} for q in Question.query.all()]

    def post(self):
        data = request.get_json()
        question = Question(content=data['content'], category_id=data['category_id'])
        db.session.add(question)
        db.session.commit()
        return {'message': 'Question added'}, 201

class AnswerList(Resource):
    def get(self):
        return [{'id': a.id, 'content': a.content, 'question_id': a.question_id} for a in Answer.query.all()]

    def post(self):
        data = request.get_json()
        ans = Answer(content=data['content'], question_id=data['question_id'])
        db.session.add(ans)
        db.session.commit()
        return {'message': 'Answer added'}, 201
        

api.add_resource(CategoryList, '/categories')
api.add_resource(QuestionList, '/questions')
api.add_resource(AnswerList, '/answers')
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
        