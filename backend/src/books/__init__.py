from datetime import datetime
from http import HTTPStatus

import src.models as md
import src.p_models as pmd
from flask import jsonify, make_response, request
from flask_jwt_extended import current_user, jwt_required
from flask_restx import Namespace, Resource, fields
from sqlalchemy import delete, insert, or_, select, update
from sqlalchemy.orm import joinedload
from src.auth.oauth import admin_required
from src.utils import atomic_transaction, session, sql_compile
from sqlalchemy import text

book_namespace = Namespace("Books", description="Book operations", path="/")

new_book_input = book_namespace.model(
    "NewBookInput",
    {
        "title": fields.String(required=True, description="Title"),
        "author": fields.String(required=True, description="Author"),
        "category_id": fields.Integer(required=True, description="Category ID"),
        "isbn": fields.String(required=True, description="ISBN"),
        "quantity": fields.Integer(required=True, description="Quantity"),
        "location": fields.String(required=True, description="Location"),
    },
)

update_book_input = book_namespace.model(
    "UpdateBookInput",
    {
        "title": fields.String(description="Title"),
        "author": fields.String(description="Author"),
        "category_id": fields.Integer(description="Category ID"),
        "isbn": fields.String(description="ISBN"),
        "quantity": fields.Integer(description="Quantity"),
        "location": fields.String(description="Location"),
    },
)


@book_namespace.route("/categories")
class Categories(Resource):
    def get(self):
        stmt = select(md.Category.id, md.Category.name)
        categories = session.execute(stmt).mappings().all()
        categories = [pmd.ListCategorySchema.model_validate(category) for category in categories]
        return jsonify(
            {
                "categories": [category.model_dump() for category in categories],
                "queries": [sql_compile(stmt)],
            }
        )


@book_namespace.route("/categories/<int:category_id>")
@book_namespace.doc(params={"category_id": "Category ID"})
class Category(Resource):
    @jwt_required(optional=True)
    def get(self, category_id):
        stmt = select(md.Category).where(md.Category.id == category_id)
        schema = pmd.CategoryDetailSchema
        if request.args.get("detail") == "true" and current_user and current_user.role == "admin":
            stmt = stmt.options(joinedload(md.Category.category_added_by))
            schema = pmd.AdminCategoryDetailSchema

        category = session.scalars(stmt).first()
        category = schema.model_validate(category)
        return jsonify({"category": category.model_dump(), "queries": [sql_compile(stmt)]})


@book_namespace.route("/books")
class Books(Resource):
    def get(self):
        """✅ Fetch books with filtering options."""

        # I modified query below so the books displayed on the UI are only those which have not been borrowed
        stmt = """
            SELECT book.*, category.name AS book_category 
            FROM book 
            JOIN category ON book.category_id = category.id
            WHERE book.current_quantity >= 1
        """
        
        or_list = []
        title = request.args.get("title")
        if title:
            or_list.append(f"book.title LIKE '%{title}%'")

        author = request.args.get("author")
        if author:
            or_list.append(f"book.author LIKE '%{author}%'")

        isbn = request.args.get("isbn")
        if isbn:
            or_list.append(f"book.isbn LIKE '%{isbn}%'")

        category = request.args.get("category")
        if category:
            or_list.append(f"category.name = '{category}'")

        # Combine filters with "AND" instead of another "WHERE"
        if or_list:
            stmt += " AND " + " OR ".join(or_list)

        stmt += " ORDER BY book.title ASC"

        print(f"Generated SQL Query: {stmt}")  # Debugging

        # Execute query
        books = session.execute(text(stmt)).mappings().all()

        # Validate results with schema
        books = [pmd.ListBookSchema.model_validate(book) for book in books]

        return jsonify({"books": [book.model_dump() for book in books], "queries": [stmt]})

    @jwt_required()  # Require authentication
    @atomic_transaction  # Ensure atomic DB operation
    def post(self):
        """✅ Add a new book"""
        data = request.json

        # ✅ Validate required fields
        required_fields = ["title", "author", "category_id", "isbn", "quantity", "location"]
        if not all(field in data for field in required_fields):
            return make_response(jsonify(message="Missing required fields"), HTTPStatus.BAD_REQUEST)

        # ✅ Insert new book into the database
        stmt = insert(md.Book).values(
            title=data["title"],
            author=data["author"],
            category_id=data["category_id"],
            isbn=data["isbn"],
            current_quantity=data["quantity"],
            location=data["location"],
            date_added=datetime.now() , # ✅ Add this line
            added_by_id=current_user.id  # ✅ Fix: Add the user who is adding the book
        )

        queries = [sql_compile(stmt)]  # Store the query for debugging/logging
        session.execute(stmt)
        session.commit()

        return make_response(jsonify(message="Book added successfully", queries=queries), HTTPStatus.CREATED)




@book_namespace.route("/books/<int:book_id>")
@book_namespace.doc(params={"book_id": "Book ID"})
class Book(Resource):
    @jwt_required(optional=True)
    def get(self, book_id):
        schema = pmd.BookDetailSchema
        # Base query to select a book by its ID and join with its category
        stmt = (
            # Select all columns from the Book table
            select(md.Book)
            # Join with the Category table using the book_category relationship
            .join(md.Book.book_category)
            # Filter the query to only include the book with the specified book_id
            .where(md.Book.id == book_id)
            # Use joinedload to eagerly load the book_category relationship
            # and restrict the loaded fields to only id and name from the Category table
            .options(joinedload(md.Book.book_category).load_only(md.Category.id, md.Category.name))
        )

        if request.args.get("detail") == "true" and current_user and current_user.role == "admin":
            stmt = (
                stmt
                # Join with the UserAccount table to get details about the user who added the book
                .join(md.Book.book_added_by)
                # Perform an outer join with the Borrow table to include borrow details (if any)
                # Outer join ensures that books without borrow records are still included
                .outerjoin(md.Book.borrows).options(
                    # Use joinedload to eagerly load the book_added_by relationship
                    # and restrict the loaded fields to only first_name and last_name from the UserAccount table
                    joinedload(md.Book.book_added_by).load_only(
                        md.UserAccount.first_name, md.UserAccount.last_name
                    ),
                    # Use joinedload to eagerly load the borrows relationship
                    # and restrict the loaded fields to only id, borrowed_by_id, borrow_date, and is_returned from the Borrow table
                    joinedload(md.Book.borrows).load_only(
                        md.Borrow.id,
                        md.Borrow.borrowed_by_id,
                        md.Borrow.borrow_date,
                        md.Borrow.is_returned,
                    ),
                    # Use joinedload to eagerly load the borrowed_by relationship within the borrows relationship
                    # and restrict the loaded fields to only first_name and last_name from the UserAccount table
                    joinedload(md.Book.borrows)
                    .joinedload(md.Borrow.borrowed_by)
                    .load_only(md.UserAccount.first_name, md.UserAccount.last_name),
                )
            )
            schema = pmd.MoreBookDetailSchema

        book = session.scalars(stmt).first()
        book = schema.model_validate(book)
        return jsonify({"book": book.model_dump(), "queries": [sql_compile(stmt)]})

    @book_namespace.expect(update_book_input)
    @admin_required
    @atomic_transaction
    def put(self, book_id):
        # Get the fields to update from the request
        update_data = {}
        field_names = list(update_book_input.keys())
        for name in field_names:
            if name in request.json:
                if name == "quantity":
                    update_data["current_quantity"] = request.json[name]
                else:
                    update_data[name] = request.json[name]

        # If no fields to update, return an error
        if not update_data:
            return make_response(
                jsonify(error="No fields to update", queries=[]), HTTPStatus.NOT_MODIFIED
            )

        # Build the update statement dynamically
        update_stmt = update(md.Book).where(md.Book.id == book_id).values(**update_data)
        queries = [sql_compile(update_stmt)]
        result = session.execute(update_stmt)
        if result.rowcount == 0:
            return make_response(jsonify(error="Book not found"), 404)
        return make_response(
            jsonify(message="Book updated successfully", queries=queries), HTTPStatus.OK
        )

    @admin_required
    @atomic_transaction
    def delete(self, book_id):
        book_exists_stmt = select(md.Book.id).where(md.Book.id == book_id)
        queries = [sql_compile(book_exists_stmt)]
        book_exists = session.scalars(book_exists_stmt).first()
        if not book_exists:
            return make_response(
                jsonify(error="Book not found", queries=queries), HTTPStatus.NOT_FOUND
            )

        borrow_exists_stmt = (
            select(md.Borrow.id)
            .where(md.Borrow.book_id == book_id, md.Borrow.is_returned.is_(False))
            .exists()
        )
        queries.append("SELECT " + sql_compile(borrow_exists_stmt))
        borrow_exists = session.scalar(select(borrow_exists_stmt))
        if borrow_exists:
            return make_response(
                jsonify(
                    error="Book is borrowed and not returned yet, cannot delete",
                    queries=queries,
                ),
                HTTPStatus.BAD_REQUEST,
            )

        delete_stmt = delete(md.Book).where(md.Book.id == book_id)
        queries.append(sql_compile(delete_stmt))
        session.execute(delete_stmt)
        return make_response(
            jsonify(message="Book deleted successfully", queries=queries), HTTPStatus.OK
        )
