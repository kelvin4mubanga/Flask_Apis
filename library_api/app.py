
from flask import Flask, request
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)

class Borrower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrower.id'))
        

class BookList(Resource):
    def get(self):
        return [{'id': b.id, 'title': b.title, 'author': b.author} for b in Book.query.all()]

    def post(self):
        data = request.get_json()
        book = Book(title=data['title'], author=data['author'])
        db.session.add(book)
        db.session.commit()
        return {'message': 'Book added'}, 201

class BorrowerList(Resource):
    def get(self):
        return [{'id': b.id, 'name': b.name} for b in Borrower.query.all()]

    def post(self):
        data = request.get_json()
        borrower = Borrower(name=data['name'])
        db.session.add(borrower)
        db.session.commit()
        return {'message': 'Borrower added'}, 201

class BorrowRecordList(Resource):
    def get(self):
        return [{'id': r.id, 'book_id': r.book_id, 'borrower_id': r.borrower_id} for r in BorrowRecord.query.all()]

    def post(self):
        data = request.get_json()
        record = BorrowRecord(book_id=data['book_id'], borrower_id=data['borrower_id'])
        db.session.add(record)
        db.session.commit()
        return {'message': 'Record created'}, 201
        

api.add_resource(BookList, '/books')
api.add_resource(BorrowerList, '/borrowers')
api.add_resource(BorrowRecordList, '/borrow-records')
        

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
        