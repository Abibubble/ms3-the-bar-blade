import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from flask_paginate import Pagination, get_page_args
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


def get_recipes(offset=0, per_page=10):
    # Give pagination information about recipes
    recipes = list(mongo.db.recipes.find())
    return recipes[offset: offset + per_page]


@app.route("/")
@app.route("/homepage")
def homepage():
    recipes = list(mongo.db.recipes.find())
    categories = mongo.db.categories.find()

    # Pagination
    # pylint: disable=unbalanced-tuple-unpacking
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    # pylint: enable=unbalanced-tuple-unpacking
    total = len(recipes)
    pagination_recipes = get_recipes(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    # Find if a user is logged in
    try:
        user = mongo.db.users.find_one({"username": session["user"]})
    except BaseException:
        user = mongo.db.users.find()

    for recipe in pagination_recipes:
        # Fill in username from user _id
        try:
            username = mongo.db.users.find_one(
                {"_id": ObjectId(recipe["user_id"])})["username"]
            recipe["user_id"] = username
        except BaseException:
            recipe["user_id"] = "undefined"

        # Fill in category_name from category _id
        try:
            category_name = mongo.db.categories.find_one(
                {"_id": ObjectId(recipe["category_id"])})["category_name"]
            recipe["category_id"] = category_name
        except BaseException:
            recipe["category_id"] = "undefined"

    return render_template(
        "homepage.html", recipes=pagination_recipes,
        categories=categories, user=user, page=page,
        per_page=per_page, pagination=pagination)


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
            username = mongo.db.users.find_one(
                {"_id": ObjectId(recipe["user_id"])})["username"]
            recipe["user_id"] = username
        except BaseException:
            recipe["user_id"] = "undefined"
        try:
            category_name = mongo.db.categories.find_one(
                {"_id": ObjectId(recipe["category_id"])})["category_name"]
            recipe["category_id"] = category_name
        except BaseException:
            recipe["category_id"] = "undefined"

    if session["user"]:
        return render_template(
            "profile.html", recipes=recipes, user=user, username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    # Remove user from session cookies and log out
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/add_cocktail", methods=["GET", "POST"])
def add_cocktail():
    # Allow user to add a cocktail recipe
    user = mongo.db.users.find_one({"username": session["user"]})

    if request.method == "POST":
        category_name = request.form.get("category_name")
        category = mongo.db.categories.find_one(
            {"category_name": category_name})

        cocktail = {
            "category_id": ObjectId(category["_id"]),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_list": request.form.getlist("recipe_list"),
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
    # Allow user or admin to edit a cocktail recipe
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
    # Allow user or admin to delete a cocktail recipe
    mongo.db.recipes.remove({"_id": ObjectId(recipe_id)})
    flash("Cocktail Deleted")
    return redirect(url_for("homepage"))


def get_search_recipes(offset=0, per_page=10):
    # Give pagination information about recipes when searched
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return recipes[offset: offset + per_page]


@app.route("/search", methods=["GET", "POST"])
def search():
    # Search function
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    user = mongo.db.users.find_one({"username": session["user"]})

    # Pagination
    # pylint: disable=unbalanced-tuple-unpacking
    page, per_page, offset = get_page_args(page_parameter='page',
                                           per_page_parameter='per_page')
    # pylint: enable=unbalanced-tuple-unpacking
    total = len(recipes)
    pagination_recipes = get_search_recipes(offset=offset, per_page=per_page)
    pagination = Pagination(page=page, per_page=per_page, total=total)

    for recipe in pagination_recipes:
        # Fill in username from user _id
        try:
            username = mongo.db.users.find_one(
                {"_id": ObjectId(recipe["user_id"])})["username"]
            recipe["user_id"] = username
        except BaseException:
            recipe["user_id"] = "undefined"

        # Fill in category_name from category _id
        try:
            category_name = mongo.db.categories.find_one(
                {"_id": ObjectId(recipe["category_id"])})["category_name"]
            recipe["category_id"] = category_name
        except BaseException:
            recipe["category_id"] = "undefined"

    return render_template(
        "homepage.html", recipes=pagination_recipes,
        user=user, page=page, per_page=per_page, pagination=pagination)


@app.route("/get_categories")
def get_categories():
    # Show categories to admin user
    user = mongo.db.users.find_one({"username": session["user"]})
    categories = list(mongo.db.categories.find().sort("category_name", 1))
    return render_template("categories.html", categories=categories, user=user)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():
    # Allow admin user to add categories
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
    # Allow admin user to edit categories
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
    # Allow admin user to delete categories
    mongo.db.categories.remove({"_id": ObjectId(category_id)})
    flash("Category deleted")
    return redirect(url_for("get_categories"))


@app.route("/get_users")
def get_users():
    # Allow admin user to view all users
    user = mongo.db.users.find_one({"username": session["user"]})
    users = list(mongo.db.users.find().sort("category_name", 1))
    return render_template("users.html", users=users, user=user)


@app.route("/admin_user/<user_id>")
def admin_user(user_id):
    # Allow admin to give or remove admin rights on other users
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if user["is_admin"] is False:
        mongo.db.users.update(
            {"_id": ObjectId(user_id)}, {"$set": {"is_admin": True}})
        flash("User Admin Rights Added")
    else:
        mongo.db.users.update(
            {"_id": ObjectId(user_id)}, {"$set": {"is_admin": False}})
        flash("User Admin Rights Removed")

    return redirect(url_for("get_users"))


@app.route("/delete_user/<user_id>")
def delete_user(user_id):
    # Allow admin user to delete other users
    mongo.db.users.remove({"_id": ObjectId(user_id)})
    flash("User deleted")
    return redirect(url_for("get_users"))


@app.route("/delete_account/<username>")
def delete_account(username):
    # Allow user to delete their own account
    mongo.db.users.remove({"username": username})
    flash("User deleted")
    session.pop("user")
    return redirect(url_for("homepage"))


@app.errorhandler(404)
def not_found(error):
    # 404 page for if errors do occur
    try:
        user = mongo.db.users.find_one({"username": session["user"]})
    except BaseException:
        user = mongo.db.users.find()
    return render_template('404.html', error=error, user=user), 404


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
