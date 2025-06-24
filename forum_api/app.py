
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Forum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'))
        

class ForumList(Resource):
    def get(self):
        return [{'id': f.id, 'title': f.title} for f in Forum.query.all()]

    def post(self):
        data = request.get_json()
        forum = Forum(title=data['title'])
        db.session.add(forum)
        db.session.commit()
        return {'message': 'Forum created'}, 201

class ThreadList(Resource):
    def get(self):
        return [{'id': t.id, 'topic': t.topic, 'forum_id': t.forum_id} for t in Thread.query.all()]

    def post(self):
        data = request.get_json()
        thread = Thread(topic=data['topic'], forum_id=data['forum_id'])
        db.session.add(thread)
        db.session.commit()
        return {'message': 'Thread created'}, 201

class PostList(Resource):
    def get(self):
        return [{'id': p.id, 'content': p.content, 'thread_id': p.thread_id} for p in Post.query.all()]

    def post(self):
        data = request.get_json()
        post = Post(content=data['content'], thread_id=data['thread_id'])
        db.session.add(post)
        db.session.commit()
        return {'message': 'Post added'}, 201
        

api.add_resource(ForumList, '/forums')
api.add_resource(ThreadList, '/threads')
api.add_resource(PostList, '/posts')
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
        