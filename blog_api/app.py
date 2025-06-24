
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'))
        

class AuthorList(Resource):
    def get(self):
        return [{'id': a.id, 'name': a.name} for a in Author.query.all()]

    def post(self):
        data = request.get_json()
        author = Author(name=data['name'])
        db.session.add(author)
        db.session.commit()
        return {'message': 'Author added'}, 201

class BlogPostList(Resource):
    def get(self):
        return [{'id': b.id, 'title': b.title, 'content': b.content, 'author_id': b.author_id} for b in BlogPost.query.all()]

    def post(self):
        data = request.get_json()
        blog = BlogPost(title=data['title'], content=data['content'], author_id=data['author_id'])
        db.session.add(blog)
        db.session.commit()
        return {'message': 'Blog post created'}, 201
        

api.add_resource(AuthorList, '/authors')
api.add_resource(BlogPostList, '/blog-posts')
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
        