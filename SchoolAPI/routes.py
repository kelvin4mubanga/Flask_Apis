from flask import Flask, request
from flask_restful import Resource, Api
from models import db, Student

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school.db'
db.init_app(app)
api = Api(app)

class StudentResource(Resource):
    def get(self):
        return [{"id": s.id, "name": s.name, "grade": s.grade} for s in Student.query.all()]

    def post(self):
        data = request.json
        student = Student(name=data['name'], grade=data['grade'])
        db.session.add(student)
        db.session.commit()
        return {"message": "Student added"}, 201

api.add_resource(StudentResource, '/students')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()