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
    name = db.Column(db.String(30), nullable=False)
    color = db.Column(db.String(20), nullable=False, default='#007bff')
    todos = db.relationship('Todo', backref='category', lazy=True)

    def __repr__(self):
        return f"Category(id={self.id},name={self.name},color={self.color})"


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(30), nullable=False)
    desc = db.Column(db.String(40), nullable=False)
    addon = Column(DateTime, default=datetime.now())
    completed = db.Column(db.Boolean, default=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)

    def __repr__(self):
        return f"Todo(id={self.id},title={self.title},desc={self.desc},completed={self.completed},dateadded={self.addon},category_id={self.category_id})"


@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        ttitle = request.form.get("ttitle")
        ttext = request.form.get("ttext")
        category_id = request.form.get("category_id")
        data1 = Todo(title=ttitle, desc=ttext, category_id=category_id if category_id else None)
        db.session.add(data1)
        db.session.flush()
        db.session.commit()
    
    # 获取分类筛选参数
    category_filter = request.args.get("category")
    
    # 构建查询
    if category_filter:
        selectstm = Select(Todo.id, Todo.title, Todo.desc, func.strftime(
            "%d/%m/%Y %H:%M", Todo.addon), Todo.completed, Todo.category_id, Category.name, Category.color).join(
            Category, Todo.category_id == Category.id, isouter=True).where(Todo.category_id == category_filter)
    else:
        selectstm = Select(Todo.id, Todo.title, Todo.desc, func.strftime(
            "%d/%m/%Y %H:%M", Todo.addon), Todo.completed, Todo.category_id, Category.name, Category.color).join(
            Category, Todo.category_id == Category.id, isouter=True)
    
    alltodos = db.session.execute(selectstm).fetchall()
    
    # 获取所有分类
    allcategories = Category.query.all()
    
    print(alltodos)
    return render_template("index.html", todo=alltodos, place={"title": "", "desc": "", "category_id": ""}, 
                           title={"main": "Add Todo", "btn": "ADD"}, categories=allcategories, 
                           selected_category=category_filter)


@app.route("/about")
def aboutpage():
    return render_template("about.html")


@app.route("/update/<int:id>", methods=["POST", "GET"])
def update(id):
    if request.method == "GET":
        stmt = Select(Todo).where(Todo.id == id)
        data = db.session.execute(stmt).scalar_one()
        allcategories = Category.query.all()
        return render_template("update.html", place=data, title={"main": "Update Todo", "btn": "Update"}, categories=allcategories)
    else:
        category_id = request.form.get("category_id")
        updatstmt = Update(Todo).where(Todo.id == id).values(
            title=request.form.get("ttitle"), desc=request.form.get("ttext"), 
            category_id=category_id if category_id else None)
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


# 分类管理路由
@app.route("/categories", methods=["POST", "GET"])
def categories():
    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color")
        new_category = Category(name=name, color=color)
        db.session.add(new_category)
        db.session.commit()
        return redirect(url_for("categories"))
    
    all_categories = Category.query.all()
    return render_template("categories.html", categories=all_categories)


@app.route("/categories/edit/<int:id>", methods=["POST", "GET"])
def edit_category(id):
    category = Category.query.get_or_404(id)
    if request.method == "POST":
        category.name = request.form.get("name")
        category.color = request.form.get("color")
        db.session.commit()
        return redirect(url_for("categories"))
    return render_template("edit_category.html", category=category)


@app.route("/categories/delete/<int:id>")
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for("categories"))


@app.errorhandler(404)
def errorhtml(error):
    return render_template("error.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
