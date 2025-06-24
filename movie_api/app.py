
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
        

class GenreList(Resource):
    def get(self):
        return [{'id': g.id, 'name': g.name} for g in Genre.query.all()]

    def post(self):
        data = request.get_json()
        genre = Genre(name=data['name'])
        db.session.add(genre)
        db.session.commit()
        return {'message': 'Genre added'}, 201

class MovieList(Resource):
    def get(self):
        return [{'id': m.id, 'title': m.title, 'genre_id': m.genre_id} for m in Movie.query.all()]

    def post(self):
        data = request.get_json()
        movie = Movie(title=data['title'], genre_id=data['genre_id'])
        db.session.add(movie)
        db.session.commit()
        return {'message': 'Movie added'}, 201

class ReviewList(Resource):
    def get(self):
        return [{'id': r.id, 'content': r.content, 'movie_id': r.movie_id} for r in Review.query.all()]

    def post(self):
        data = request.get_json()
        review = Review(content=data['content'], movie_id=data['movie_id'])
        db.session.add(review)
        db.session.commit()
        return {'message': 'Review added'}, 201
        

api.add_resource(GenreList, '/genres')
api.add_resource(MovieList, '/movies')
api.add_resource(ReviewList, '/reviews')
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
        