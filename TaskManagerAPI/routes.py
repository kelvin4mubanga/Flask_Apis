from flask import Flask, request
from flask_restful import Resource, Api
from models import db, Task

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db.init_app(app)
api = Api(app)

class TaskResource(Resource):
    def get(self):
        return [{"id": t.id, "title": t.title, "completed": t.completed} for t in Task.query.all()]

    def post(self):
        data = request.json
        task = Task(title=data['title'], completed=data.get('completed', False))
        db.session.add(task)
        db.session.commit()
        return {"message": "Task added"}, 201

api.add_resource(TaskResource, '/tasks')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()