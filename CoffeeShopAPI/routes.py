from flask import Flask, request
from flask_restful import Resource, Api
from models import db, Coffee

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coffee.db'
db.init_app(app)
api = Api(app)

class CoffeeResource(Resource):
    def get(self):
        return [{"id": c.id, "name": c.name, "price": c.price} for c in Coffee.query.all()]

    def post(self):
        data = request.json
        coffee = Coffee(name=data['name'], price=data['price'])
        db.session.add(coffee)
        db.session.commit()
        return {"message": "Coffee added"}, 201

api.add_resource(CoffeeResource, '/coffees')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run()