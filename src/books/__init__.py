from datetime import datetime
from http import HTTPStatus

from flask import jsonify, make_response, request
from flask_jwt_extended import current_user
from flask_restx import Namespace, Resource, fields
from sqlalchemy import delete, func, insert, select, update

import src.models as md
import src.p_models as pmd
from src.auth.oauth import admin_required
from src.utils import calculate_due_date, calculate_fine, session, sql_compile

book_namespace = Namespace("Books", description="Book operations", path="/")

new_book_input = book_namespace.model(
    "NewBookInput",
    {
        "title": fields.String(required=True, description="Title"),
        "author": fields.String(required=True, description="Author"),
        "category_id": fields.Integer(required=True, description="Category ID"),
        "isbn": fields.String(required=True, description="ISBN"),
        "quantity": fields.Integer(required=True, description="Quantity"),
        "location": fields.String(description="Location"),
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


borrow_book_input = book_namespace.model(
    "BorrowBookInput",
    {
        "book_id": fields.Integer(required=True, description="Book ID"),
        "borrower_id": fields.Integer(required=True, description="Borrower ID"),
    },
)


return_book_input = book_namespace.model(
    "ReturnBookInput",
    {
        "borrow_id": fields.Integer(required=True, description="Borrower ID"),
    },
)


@book_namespace.route("/books")
class Books(Resource):
    def get(self):
        stmt = select(md.Book, md.Category.name).join(md.Category)
        title = request.args.get("title")
        if title:
            stmt = stmt.where(md.Book.title.ilike(f"%{title}%"))

        author = request.args.get("author")
        if author:
            stmt = stmt.where(md.Book.author.ilike(f"%{author}%"))

        isbn = request.args.get("isbn")
        if isbn:
            stmt = stmt.where(md.Book.isbn.ilike(f"%{isbn}%"))

        category = request.args.get("category")
        if category:
            stmt = stmt.where(md.Category.name == category)

        res = session.scalars(stmt)
        books = res.all()
        books = [pmd.ListBookSchema.model_validate(book) for book in books]
        return jsonify(
            {"books": [book.model_dump() for book in books], "queries": [sql_compile(stmt)]}
        )

    @admin_required
    @book_namespace.expect(new_book_input)
    def post(self):
        data = request.json
        book = md.Book(
            title=data["title"],
            author=data["author"],
            category_id=data["category_id"],
            isbn=data["isbn"],
            original_quantity=data["quantity"],
            current_quantity=data["quantity"],
            date_added=datetime.now(),
            added_by_id=current_user.id,
        )

        # Generate INSERT statement
        query = sql_compile(
            insert(md.Book).values(
                title=book.title,
                author=book.author,
                category_id=book.category_id,
                isbn=book.isbn,
                original_quantity=book.original_quantity,
                current_quantity=book.current_quantity,
                date_added=book.date_added,
                added_by_id=book.added_by_id,
            )
        )

        try:
            session.add(book)
            session.commit()
            return make_response(jsonify(book_id=book.id, queries=[query]), HTTPStatus.CREATED)
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=[query]), HTTPStatus.INTERNAL_SERVER_ERROR
            )


@book_namespace.route("/books/<int:id>")
@book_namespace.doc(params={"id": "Book ID"})
class Book(Resource):
    def get(self, id):
        stmt = select(md.Book).where(md.Book.id == id).join(md.Category).join(md.UserAccount)
        res = session.scalars(stmt)
        book = res.first()
        book = pmd.BookDetailSchema.model_validate(book)
        return jsonify({"book": book.model_dump(), "queries": [sql_compile(stmt)]})

    @admin_required
    @book_namespace.expect(update_book_input)
    def put(self, id):
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
        update_stmt = update(md.Book).where(md.Book.id == id).values(**update_data)
        queries = [sql_compile(update_stmt)]

        try:
            result = session.execute(update_stmt)
            if result.rowcount == 0:
                return make_response(jsonify(error="Book not found"), 404)

            session.commit()
            return make_response(
                jsonify(message="Book updated successfully", queries=queries), HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=queries), HTTPStatus.INTERNAL_SERVER_ERROR
            )

    @admin_required
    def delete(self, id):
        book_exists_stmt = select(md.Book.id).where(md.Book.id == id)
        queries = [sql_compile(book_exists_stmt)]
        book_exists = session.scalars(book_exists_stmt).first()
        if not book_exists:
            return make_response(
                jsonify(error="Book not found", queries=queries), HTTPStatus.NOT_FOUND
            )

        borrow_exists_stmt = (
            select(md.Borrow.id)
            .where(md.Borrow.book_id == id, md.Borrow.is_returned.is_(False))
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

        delete_stmt = delete(md.Book).where(md.Book.id == id)
        queries.append(sql_compile(delete_stmt))
        try:
            session.execute(delete_stmt)
            session.commit()
            return make_response(
                jsonify(message="Book deleted successfully", queries=queries), HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=queries), HTTPStatus.INTERNAL_SERVER_ERROR
            )


@book_namespace.route("/borrow")
class BorrowBook(Resource):
    @admin_required
    @book_namespace.expect(borrow_book_input)
    def post(self):
        data = request.json
        book_id = data["book_id"]
        borrower_id = data["borrower_id"]
        stmt = select(func.count()).where(md.Borrow.borrowed_by_id == borrower_id)
        queries = [sql_compile(stmt)]
        borrow_count = session.scalar(stmt)
        if borrow_count >= 5:
            return make_response(
                jsonify(
                    error="Borrower has reached the maximum limit of 5 borrowed books",
                    queries=queries,
                ),
                HTTPStatus.BAD_REQUEST,
            )

        stmt = select(md.Book.id, md.Book.current_quantity).where(md.Book.id == book_id)
        queries.append(sql_compile(stmt))
        book = session.execute(stmt).mappings().first()
        if not book:
            return make_response(
                jsonify(error="Book not found", queries=queries), HTTPStatus.NOT_FOUND
            )

        if book.current_quantity == 0:
            return make_response(
                jsonify(error="Book is out of stock or is borrowed", queries=queries),
                HTTPStatus.BAD_REQUEST,
            )

        due_date = calculate_due_date()
        stmt = insert(md.Borrow).values(
            book_id=book_id,
            borrowed_by_id=borrower_id,
            given_by_id=current_user.id,
            borrow_date=datetime.now(),
            due_date=due_date,
        )
        queries.append(sql_compile(stmt))
        session.execute(stmt)
        stmt = (
            update(md.Book)
            .where(md.Book.id == book_id)
            .values(current_quantity=md.Book.current_quantity - 1)
        )
        queries.append(sql_compile(stmt))
        session.execute(stmt)
        session.commit()
        return make_response(
            jsonify(message="Book borrowed successfully", queries=queries), HTTPStatus.CREATED
        )


@book_namespace.route("/return")
class ReturnBook(Resource):
    @admin_required
    @book_namespace.expect(return_book_input)
    def post(self):
        data = request.json
        borrow_id = data["borrow_id"]
        stmt = select(md.Borrow).where(md.Borrow.id == borrow_id)
        queries = [sql_compile(stmt)]
        borrow = session.scalars(stmt).first()
        if not borrow:
            return make_response(
                jsonify(error="Borrow record not found", queries=queries), HTTPStatus.NOT_FOUND
            )
        if borrow.is_returned:
            return make_response(
                jsonify(error="Book already returned", queries=queries), HTTPStatus.BAD_REQUEST
            )
        now = datetime.now()
        stmt = (
            update(md.Borrow)
            .where(md.Borrow.id == borrow_id)
            .values(is_returned=True, return_date=now, received_by_id=current_user.id)
        )
        queries.append(sql_compile(stmt))
        session.execute(stmt)
        stmt = (
            update(md.Book)
            .where(md.Book.id == borrow.book_id)
            .values(current_quantity=md.Book.current_quantity + 1)
        )
        queries.append(sql_compile(stmt))
        session.execute(stmt)
        if borrow.due_date.date() < now.date():
            fine = calculate_fine(date=borrow.due_date)
            stmt = insert(md.Fine).values(
                borrow_id=borrow_id,
                amount=fine,
                date_created=now,
            )
            queries.append(sql_compile(stmt))
            session.execute(stmt)
        session.commit()
        return make_response(
            jsonify(message="Book returned successfully", queries=queries), HTTPStatus.OK
        )
