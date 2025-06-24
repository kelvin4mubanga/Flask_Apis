from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

@app.route("/products", methods=["POST", "GET"])
def manage_products():
    if request.method == "POST":
        data = request.json
        new_product = Product(name=data["name"], price=data["price"])
        db.session.add(new_product)
        db.session.commit()
        return jsonify({"message": "Product added"}), 201
    products = Product.query.all()
    return jsonify([{"id": p.id, "name": p.name, "price": p.price} for p in products]), 200

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)