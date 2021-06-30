import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/homepage")
def homepage():
    recipes = list(mongo.db.recipes.find())
    try:
        user = mongo.db.users.find_one({"username": session["user"]})
    except BaseException:
        user = mongo.db.users.find()
    for recipe in recipes:
        try:
            username = mongo.db.users.find_one(
                {"_id": ObjectId(recipe["user_id"])})["username"]
            category_name = mongo.db.categories.find_one(
                {"_id": ObjectId(recipe["category_id"])})["category_name"]
            recipe["user_id"] = username
            recipe["category_id"] = category_name
        except BaseException:
            pass
    categories = mongo.db.categories.find()
    return render_template(
        "homepage.html", recipes=recipes, categories=categories, user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Set variables
        username = request.form.get("username").lower()
        password = request.form.get("password")
        password_confirm = request.form.get("password_confirm")
        print(password_confirm)

        # Check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": username})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if password != password_confirm:
            flash("Oh no! Your passwords don't match")
            return redirect(url_for("register"))

        register = {
            "username": username,
            "password": generate_password_hash(password),
            "is_admin": False
        }
        mongo.db.users.insert_one(register)

        # Put new user into session
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return redirect(url_for("profile", username=session["user"]))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Check if username already exists
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # Ensure hashed password matches
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                return redirect(url_for(
                    "profile", username=session["user"]))
            else:
                # Invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))
        else:
            # Username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    # Get the user's username from the database
    user = mongo.db.users.find_one({"username": session["user"]})
    username = user["username"]
    user_id = user["_id"]

    if user["is_admin"]:
        recipes = list(mongo.db.recipes.find())
    else:
        recipes = list(mongo.db.recipes.find({"user_id": ObjectId(user_id)}))
    for recipe in recipes:
        try:
            user_name = mongo.db.users.find_one(
                {"_id": ObjectId(recipe["user_id"])})["username"]
            category_name = mongo.db.categories.find_one(
                {"_id": ObjectId(recipe["category_id"])})["category_name"]
            recipe["user_id"] = user_name
            recipe["category_id"] = category_name
        except BaseException:
            pass

    if session["user"]:
        return render_template(
            "profile.html", recipes=recipes, user=user, username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # Remove user from session cookies
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_cocktail", methods=["GET", "POST"])
def add_cocktail():
    user = mongo.db.users.find_one({"username": session["user"]})

    if request.method == "POST":
        category_name = request.form.get("category_name")
        category = mongo.db.categories.find_one(
            {"category_name": category_name})

        cocktail = {
            "category_id": ObjectId(category["_id"]),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_list": request.form.get("recipe_list"),
            "recipe_description": request.form.get("recipe_description"),
            "recipe_img": request.form.get("recipe_img"),
            "recipe_alt": request.form.get("recipe_alt"),
            "user_id": ObjectId(user["_id"])
        }
        mongo.db.recipes.insert_one(cocktail)
        flash("Cocktail successfully added!")
        return redirect(url_for("homepage"))

    categories = mongo.db.categories.find().sort("category_id", 1)
    return render_template(
        "add_cocktail.html", categories=categories, user=user)


@app.route("/edit_cocktail/<recipe_id>", methods=["GET", "POST"])
def edit_cocktail(recipe_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    category_name = request.form.get("category_name")
    category = mongo.db.categories.find_one({"category_name": category_name})

    if request.method == "POST":
        cocktail = {
            "category_id": ObjectId(category["_id"]),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_list": request.form.get("recipe_list"),
            "recipe_description": request.form.get("recipe_description"),
            "recipe_img": request.form.get("recipe_img"),
            "recipe_alt": request.form.get("recipe_alt"),
            "user_id": ObjectId(user["_id"])
        }
        mongo.db.recipes.update({"_id": ObjectId(recipe_id)}, cocktail)
        flash("Cocktail successfully edited!")

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template(
        "edit_cocktail.html", categories=categories, recipe=recipe, user=user)


@app.route("/delete_cocktail/<recipe_id>")
def delete_cocktail(recipe_id):
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Cocktail Deleted")
    return redirect(url_for("homepage"))


@app.route("/get_categories")
def get_categories():
    user = mongo.db.users.find_one({"username": session["user"]})
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories, user=user)


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("homepage.html", recipes=recipes)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.insert_one(category)
        flash("New category added")
        return redirect(url_for("get_categories"))
    return render_template("add_category.html", user=user)


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category Successfully Updated")
        return redirect(url_for("get_categories"))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})
    return render_template("edit_category.html", category=category, user=user)


@app.route("/delete_category/<category_id>")
def delete_category(category_id):
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category deleted")
    return redirect(url_for("get_categories"))


@app.route("/delete_account/<username>")
def delete_account(username):
    mongo.db.users.remove({"username": username})
    flash("User deleted")
    session.pop("user")
    return redirect(url_for("homepage"))


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
