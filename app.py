from datetime import datetime
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, DateTime, Select, Update, delete, func, select

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.secret_key = "secretkeyprathamesh"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(7), nullable=False, default="#007bff")  # 存储颜色代码，如 #007bff
    
    def __repr__(self):
        return f"Category(id={self.id},name={self.name},color={self.color})"


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(30), nullable=False)
    desc = db.Column(db.String(40), nullable=False)
    addon = Column(DateTime, default=datetime.now())
    completed = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', backref='todos')

    def __repr__(self):
        return f"Todo(id={self.id},title={self.title},desc={self.desc},completed={self.completed},dateadded={self.addon},category_id={self.category_id})"


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        ttitle = request.form.get("ttitle")
        ttext = request.form.get("ttext")
        category_id = request.form.get("category_id")
        data1 = Todo(title=ttitle, desc=ttext, category_id=category_id)
        db.session.add(data1)
        db.session.flush()
        db.session.commit()
    
    # 获取分类筛选参数
    category_filter = request.args.get('category', type=int)
    
    # 构建查询
    if category_filter:
        selectstm = Select(Todo.id, Todo.title, Todo.desc, func.strftime(
            "%d/%m/%Y %H:%M", Todo.addon), Todo.completed, Todo.category_id).where(Todo.category_id == category_filter)
    else:
        selectstm = Select(Todo.id, Todo.title, Todo.desc, func.strftime(
            "%d/%m/%Y %H:%M", Todo.addon), Todo.completed, Todo.category_id)
    
    alltodos = db.session.execute(selectstm).fetchall()
    
    # 获取所有分类用于筛选
    categories = Category.query.all()
    
    return render_template("index.html", todo=alltodos, categories=categories, 
                         current_category=category_filter, place={"title": "", "desc": ""}, 
                         title={"main": "Add Todo", "btn": "ADD"})


@app.route("/about")
def aboutpage():
    return render_template("about.html")


@app.route("/update/<int:id>", methods=["POST", "GET"])
def update(id):
    if request.method == "GET":
        stmt = Select(Todo).where(Todo.id == id)
        data = db.session.execute(stmt).scalar_one()
        categories = Category.query.all()
        return render_template("update.html", place=data, categories=categories, title={"main": "Update Todo", "btn": "Update"})
    else:
        updatstmt = Update(Todo).where(Todo.id == id).values(
            title=request.form.get("ttitle"), desc=request.form.get("ttext"), 
            category_id=request.form.get("category_id"))
        db.session.execute(updatstmt)
        db.session.commit()
        return redirect(url_for("home"))


@app.route("/delete/<int:id>")
def deleterecord(id):
    deletestmt = delete(Todo).where(Todo.id == id)
    db.session.execute(deletestmt)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/complete/<int:id>")
def completemark(id):
    args = request.args.get("comp")
    if args == "True":
        updatestmt = Update(Todo).where(Todo.id == id).values(completed=False)
    else:
        updatestmt = Update(Todo).where(Todo.id == id).values(completed=True)
    db.session.execute(updatestmt)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/categories", methods=["GET", "POST"])
def manage_categories():
    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color", "#007bff")
        new_category = Category(name=name, color=color)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for("manage_categories"))
    
    categories = Category.query.all()
    return render_template("categories.html", categories=categories)


@app.route("/categories/edit/<int:id>", methods=["POST"])
def edit_category(id):
    name = request.form.get("name")
    color = request.form.get("color", "#007bff")
    updatestmt = Update(Category).where(Category.id == id).values(name=name, color=color)
    db.session.execute(updatestmt)
    db.session.commit()
    return redirect(url_for("manage_categories"))


@app.route("/categories/delete/<int:id>")
def delete_category(id):
    # 先删除该分类下的所有任务
    deletetodos = delete(Todo).where(Todo.category_id == id)
    db.session.execute(deletetodos)
    
    # 再删除分类
    deletestmt = delete(Category).where(Category.id == id)
    db.session.execute(deletestmt)
    db.session.commit()
    return redirect(url_for("manage_categories"))


@app.errorhandler(404)
def errorhtml(error):
    return render_template("error.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
