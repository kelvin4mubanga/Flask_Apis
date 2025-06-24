from flask import Flask, request
from flask_restful import Resource, Api
from models import db, Item

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auction.db'
db.init_app(app)
api = Api(app)

class ItemResource(Resource):
    def get(self):
        return [{"id": i.id, "name": i.name, "starting_price": i.starting_price} for i in Item.query.all()]

    def post(self):
        data = request.json
        item = Item(name=data['name'], starting_price=data['starting_price'])
        db.session.add(item)
        db.session.commit()
        return {"message": "Item added"}, 201

api.add_resource(ItemResource, '/items')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()