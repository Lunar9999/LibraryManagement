from datetime import datetime
from http import HTTPStatus
from uuid import uuid4

from flask import jsonify, make_response, request
from flask_jwt_extended import current_user, jwt_required
from flask_restx import Namespace, Resource, fields
from sqlalchemy import (and_, func, insert, select, text,  # ✅ Added insert
                        update)
from sqlalchemy.orm import aliased

import src.models as md
import src.p_models as pmd
from src.auth.oauth import admin_required
from src.utils import (PAYMENT_METHODS, atomic_transaction, calculate_due_date,
                       check_overdue_and_create_fine, session, sql_compile)

borrow_namespace = Namespace("Borrows", description="Borrow / Return operations", path="/")

borrow_book_input = borrow_namespace.model(
    "BorrowBookInput",
    {
        "book_id": fields.Integer(required=True, description="Book ID"),
        "borrower_id": fields.Integer(required=True, description="Borrower ID"),
    },
)


return_book_input = borrow_namespace.model(
    "ReturnBookInput",
    {
        "borrow_id": fields.Integer(required=True, description="Borrower ID"),
    },
)

pay_fine_input = borrow_namespace.model(
    "PayFineInput",
    {
        "method": fields.String(
            required=True,
            description="Payment method",
            enum=PAYMENT_METHODS,
        ),
    },
)

@borrow_namespace.route("/borrow-book")
class BorrowBook(Resource):
    @borrow_namespace.expect(borrow_book_input)
    @jwt_required()  # Change to @admin_required if needed
    @atomic_transaction
    def post(self):
        data = request.json
        book_id = data["book_id"]
        borrower_id = data["borrower_id"]

        # Ensure the borrower is the logged-in user
        if borrower_id != current_user.id:
            return make_response(
                jsonify(error="You can only borrow books for yourself"),
                HTTPStatus.FORBIDDEN,
            )

        # ✅ Check Borrow Limit
        stmt = select(func.count(md.Borrow.id)).where(
            md.Borrow.borrowed_by_id == borrower_id, md.Borrow.is_returned.is_(False)
        )
        queries = [sql_compile(stmt)]
        borrow_count = session.execute(stmt).scalar_one()

        if borrow_count and borrow_count >= 5:
            return make_response(
                jsonify(
                    error="You have already borrowed the maximum allowed 5 books. Return one before borrowing another.",
                    queries=queries,
                ),
                HTTPStatus.BAD_REQUEST,
            )

        # ✅ Fetch Book Details
        stmt = select(md.Book).where(md.Book.id == book_id)
        queries.append(sql_compile(stmt))
        book = session.execute(stmt).scalars().first()

        if not book or book.current_quantity == 0:
            return make_response(
                jsonify(error="Book is out of stock", queries=queries),
                HTTPStatus.BAD_REQUEST,
            )

        # ✅ Borrow the book
        due_date = calculate_due_date()
        borrow_stmt = insert(md.Borrow).values(
            book_id=book_id,
            borrowed_by_id=borrower_id,
            given_by_id=current_user.id,
            borrow_date=datetime.now(),
            due_date=due_date,
        )
        queries.append(sql_compile(borrow_stmt))
        session.execute(borrow_stmt)

        # ✅ Reduce book quantity properly
        stmt = update(md.Book).where(md.Book.id == book_id).values(
            current_quantity=md.Book.current_quantity - 1
        )
        queries.append(sql_compile(stmt))
        session.execute(stmt)

        # ✅ Create Notification
        notification_stmt = insert(md.Notification).values(
            user_id=borrower_id,
            message=f"You borrowed '{book.title if book.title else 'Unknown Book'}'. Return it by {due_date.strftime('%Y-%m-%d')}.",
            is_read=False,
            sent_date=datetime.now(),
        )
        queries.append(sql_compile(notification_stmt))
        session.execute(notification_stmt)

        session.commit()  # ✅ Ensure transaction is committed

        return make_response(
            jsonify(message="Book borrowed successfully", queries=queries),
            HTTPStatus.CREATED,
        )


@borrow_namespace.route("/return-book")
class ReturnBook(Resource):
    @borrow_namespace.expect(return_book_input)
    @admin_required
    @atomic_transaction
    def post(self):
        data = request.json
        borrow_id = data["borrow_id"]

        # ✅ Fetch Borrow record along with Book details
        stmt = (
            select(md.Borrow, md.Book)
           # no need for the join here since this is a simple to confirm existence of the borrow record
            # .where(and_(md.Borrow.id == borrow_id, md.Borrow.is_returned.is_(False)))
            .where(and_(md.Borrow.book_id == borrow_id, md.Borrow.is_returned.is_(False))) # search on book_id instead of borrow_id since receiving book_id from frontend
        )
        result = session.execute(stmt).first()
        

        if not result:
            return make_response(jsonify(error="Borrow record not found"), HTTPStatus.NOT_FOUND)

        borrow, book = result  # ✅ Extract Borrow and Book objects

        if borrow.is_returned:
            print(f"🚨 DEBUG: Book '{book.title}' has already been returned!")
            return make_response(
                jsonify(
                    error=f"The book '{book.title}' has already been returned on {borrow.return_date.strftime('%Y-%m-%d')}.",
                    queries=[sql_compile(stmt)]
                ),
                HTTPStatus.BAD_REQUEST
            )

        now = datetime.now()

        # ✅ Mark book as returned

        stmt = (
            update(md.Borrow)
            .where(and_(md.Borrow.book_id == borrow_id, md.Borrow.is_returned.is_(False))) # same here search on book_id instead of borrow_id
            .values(is_returned=True, return_date=datetime.now(), received_by_id=current_user.id)
        )
        result = session.execute(stmt)

        if result.rowcount == 0:  # 🚨 Means book was already returned
            return make_response(
                jsonify(message="Book not found or already returned"),
                HTTPStatus.BAD_REQUEST
            )

        # ✅ Increase book quantity
        session.execute(
            update(md.Book)
            .where(md.Book.id == borrow.book_id)
            .values(current_quantity=md.Book.current_quantity + 1)
        )

        # ✅ Create Notification for Book Return
        notification_stmt = insert(md.Notification).values(
            user_id=borrow.borrowed_by_id,
            message=f"You returned '{book.title}' on {now.strftime('%Y-%m-%d')}.",  # ✅ FIXED
            is_read=False,
            sent_date=datetime.now(),
        )
        session.execute(notification_stmt)

        session.commit()  # ✅ Commit transaction

        return make_response(jsonify(message="Book returned successfully"), HTTPStatus.OK)

@borrow_namespace.route("/borrows")
class Borrows(Resource):
    @jwt_required()
    def get(self):
        stmt = text("""
            SELECT 
                borrow.id AS borrow_id, 
                borrow.borrowed_by_id, 
                borrow.received_by_id, 
                borrow.given_by_id, 
                borrow.is_returned, 
                borrow.due_date, 
                borrow.borrow_date, 
                book.title AS book_title, 
                book.author, 
                book.is_available, 
                book.location, 
                user_account.first_name AS borrowed_by_first_name, 
                user_account.last_name AS borrowed_by_last_name, 
                given_by.first_name AS given_by_first_name, 
                given_by.last_name AS given_by_last_name, 
                received_by.first_name AS received_by_first_name, 
                received_by.last_name AS received_by_last_name
            FROM borrow
            JOIN user_account ON borrow.borrowed_by_id = user_account.id
            JOIN user_account AS given_by ON borrow.given_by_id = given_by.id
            LEFT JOIN user_account AS received_by ON borrow.received_by_id = received_by.id
            JOIN book ON borrow.book_id = book.id
            WHERE borrowed_by_id = :borrower_id
            AND borrow.is_returned = 0  -- ✅ FILTER ONLY UNRETURNED BOOKS
        """)

        queries = [sql_compile(stmt)]
        borrows = session.execute(stmt, {"borrower_id": current_user.id}).mappings().all()

        fines = tuple()
        if borrows:
            stmt_fines = text("""
                SELECT id, amount, paid, date_created, date_paid 
                FROM fine 
                WHERE borrow_id IN (SELECT id FROM borrow WHERE borrowed_by_id = :borrower_id)
            """)
            queries.append(stmt_fines)
            fines = session.execute(stmt_fines, {"borrower_id": current_user.id}).mappings().all()

        data = [
            {
                "id": borrow.borrow_id,
                "borrowed_book": borrow.book_title,
                "author": borrow.author,
                "location": borrow.location,
                "available": borrow.is_available,
                "borrow_date": datetime.fromisoformat(borrow.borrow_date).isoformat() if isinstance(borrow.borrow_date, str) else borrow.borrow_date.isoformat(),
                "due_date": datetime.fromisoformat(borrow.due_date).isoformat() if isinstance(borrow.due_date, str) else borrow.due_date.isoformat(),
                "is_returned": borrow.is_returned == 1,
                "borrowed_by": f"{borrow.borrowed_by_first_name} {borrow.borrowed_by_last_name}",
                "given_by": f"{borrow.given_by_first_name} {borrow.given_by_last_name}",
                "received_by": (
                    f"{borrow.received_by_first_name} {borrow.received_by_last_name}"
                    if borrow.received_by_first_name and borrow.received_by_last_name
                    else "Not Received"
                ),
                "fines": [
                    {
                        "id": fine.id,
                        "borrow": borrow.book_title,
                        "amount": fine.amount,
                        "paid": fine.paid == 1,
                        "date_created": fine.date_created.isoformat(),
                        "date_paid": fine.date_paid.isoformat() if fine.date_paid else None,
                    }
                    for fine in fines
                ],
            }
            for borrow in borrows
        ]

        return make_response(
            jsonify({"borrows": data, "queries": [str(q) for q in queries]})  # ✅ Convert to string
        )


@borrow_namespace.route("/borrows/<int:borrow_id>")
class Borrow(Resource):
    @jwt_required()
    def get(self, borrow_id):
        stmt = select(md.Borrow).where(
            and_(md.Borrow.id == borrow_id, md.Borrow.borrowed_by_id == current_user.id)
        )
        borrow = session.execute(stmt).scalars().first()
        if not borrow:
            return make_response(
                jsonify(error="Borrow record not found", queries=[sql_compile(stmt)]),
                HTTPStatus.NOT_FOUND,
            )

        borrow = pmd.DetailBorrowSchema.model_validate(borrow)
        return make_response(
            jsonify({"borrow": borrow.model_dump(), "queries": [sql_compile(stmt)]})
        )


@borrow_namespace.route("/borrows-admin/<int:user_id>")
class BorrowsAdmin(Resource):
    @admin_required
    @borrow_namespace.doc(params={"user_id": "User ID"})
    def get(self, user_id):
        stmt = select(md.Borrow).where(
            and_(md.Borrow.borrowed_by_id == user_id, md.Borrow.is_returned.is_(False))  # ✅ Only show unreturned books
        )
        borrows = session.execute(stmt).scalars().all()
        borrows = [pmd.ListBorrowSchema.model_validate(borrow) for borrow in borrows]
        return make_response(
            jsonify(
                {
                    "borrows": [borrow.model_dump() for borrow in borrows],
                    "queries": [sql_compile(stmt)],
                }
            )
        )


@borrow_namespace.route("/borrows-admin/<int:user_id>/<int:borrow_id>")
class BorrowAdmin(Resource):
    @admin_required
    def get(self, user_id, borrow_id):
        stmt = select(md.Borrow).where(
            and_(md.Borrow.id == borrow_id, md.Borrow.borrowed_by_id == user_id)
        )
        borrow = session.execute(stmt).scalars().first()
        if not borrow:
            return make_response(
                jsonify(error="Borrow record not found", queries=[sql_compile(stmt)]),
                HTTPStatus.NOT_FOUND,
            )

        borrow = pmd.DetailBorrowSchema.model_validate(borrow)
        return make_response(
            jsonify({"borrow": borrow.model_dump(), "queries": [sql_compile(stmt)]})
        )


@borrow_namespace.route("/fines")
@borrow_namespace.route("/fines")
class Fines(Resource):
    @jwt_required()
    def get(self):
        # ✅ Fetch fines with optional book titles using LEFT JOIN
        stmt = text(f"""
            SELECT fine.id, fine.amount, fine.paid, fine.date_created, fine.date_paid, COALESCE(book.title, NULL) AS book_title
            FROM fine
            JOIN borrow ON fine.borrow_id = borrow.id
            LEFT JOIN book ON borrow.book_id = book.id  -- ✅ Allow missing book titles
            WHERE borrow.borrowed_by_id = {current_user.id}
        """)

        queries = [sql_compile(stmt)]
        fines = session.execute(stmt).mappings().all()

        # ✅ Calculate total paid/unpaid fines
        total_query = text(f"""
            SELECT 
                SUM(CASE WHEN fine.paid = 1 THEN fine.amount ELSE 0 END) AS total_paid,
                SUM(CASE WHEN fine.paid = 0 THEN fine.amount ELSE 0 END) AS total_unpaid
            FROM fine
            JOIN borrow ON fine.borrow_id = borrow.id
            WHERE borrow.borrowed_by_id = {current_user.id}
        """)
        queries.append(sql_compile(total_query))
        total_fines = session.execute(total_query).mappings().first()

        data = {
            "fines": [
                {
                    "id": fine.id,
                    "book_title": fine.book_title if fine.book_title else None,  # ✅ Allow None
                    "amount": fine.amount,
                    "paid": fine.paid == 1,
                    "date_created": fine.date_created,
                    "date_paid": fine.date_paid if fine.date_paid else None,
                }
                for fine in fines
            ],
            "total": {
                "paid": total_fines.total_paid or 0,
                "unpaid": total_fines.total_unpaid or 0,
            },
            "queries": queries
        }

        return make_response(jsonify(data), HTTPStatus.OK)


@borrow_namespace.route("/fines/<int:fine_id>")
class Fine(Resource):
    @jwt_required()
    def get(self, fine_id):
        stmt = select(md.Fine).where(
            and_(
                md.Fine.id == fine_id,
                md.Fine.borrow.has(md.Borrow.borrowed_by_id == current_user.id),
            )
        )
        fine = session.execute(stmt).scalars().first()
        if not fine:
            return make_response(
                jsonify(error="Fine record not found", queries=[sql_compile(stmt)]),
                HTTPStatus.NOT_FOUND,
            )

        fine = pmd.FineListSchema.model_validate(fine)
        return make_response(jsonify({"fine": fine.model_dump(), "queries": [sql_compile(stmt)]}))


@borrow_namespace.route("/fines-admin/<int:user_id>")
class FinesAdmin(Resource):
    @admin_required
    def get(self, user_id):
        stmt = select(md.Fine).where(md.Fine.borrow.has(md.Borrow.borrowed_by_id == user_id))
        fines = session.execute(stmt).scalars().all()
        fines = [pmd.FineListSchema.model_validate(fine) for fine in fines]
        return make_response(
            jsonify(
                {
                    "fines": [fine.model_dump() for fine in fines],
                    "queries": [sql_compile(stmt)],
                }
            )
        )


@borrow_namespace.route("/fines-admin/<int:user_id>/<int:fine_id>")
class FineAdmin(Resource):
    @admin_required
    def get(self, user_id, fine_id):
        stmt = select(md.Fine).where(
            and_(
                md.Fine.id == fine_id,
                md.Fine.borrow.has(md.Borrow.borrowed_by_id == user_id),
            )
        )
        fine = session.execute(stmt).scalars().first()
        if not fine:
            return make_response(
                jsonify(error="Fine record not found", queries=[sql_compile(stmt)]),
                HTTPStatus.NOT_FOUND,
            )

        fine = pmd.FineListSchema.model_validate(fine)
        return make_response(jsonify({"fine": fine.model_dump(), "queries": [sql_compile(stmt)]}))


@borrow_namespace.route("/pay-fine/<int:fine_id>")
class PayFine(Resource):
    @jwt_required()
    @atomic_transaction
    def post(self, fine_id):
        method = request.json.get("method")
        if method not in PAYMENT_METHODS:
            return make_response(
                jsonify(error=f"Invalid payment method. Must be one of {PAYMENT_METHODS}"),
                HTTPStatus.BAD_REQUEST,
            )
        if method == "cash" and current_user.role != "admin":
            return make_response(
                jsonify(
                    error="Only admins can accept fines in cash in person at the library",
                    queries=[],
                ),
                HTTPStatus.FORBIDDEN,
            )
        stmt = (
            select(md.Fine.id, md.Fine.amount, md.Fine.paid, md.Borrow.borrowed_by_id)
            .where(and_(md.Fine.id == fine_id, md.Fine.paid.is_(False)))
            .join(md.Borrow)
        )
        queries = [sql_compile(stmt)]
        fine = session.execute(stmt).mappings().first()
        if not fine:
            return make_response(
                jsonify(error="Fine not found or is already paid", queries=queries),
                HTTPStatus.NOT_FOUND,
            )

        if method == "cash":
            stmt = (
                update(md.Fine)
                .where(md.Fine.id == fine_id)
                .values(
                    paid=True,
                    date_paid=datetime.now(),
                    payment_method="cash",
                    collected_by_id=current_user.id,
                )
            )
        else:
            if current_user.role != "admin" and fine.borrowed_by_id != current_user.id:
                return make_response(
                    jsonify(
                        error="You can only pay fines for your own borrowed books using online payment",
                        queries=queries,
                    ),
                    HTTPStatus.FORBIDDEN,
                )
            # do something to process online payment
            stmt = (
                update(md.Fine)
                .where(md.Fine.id == fine_id)
                .values(
                    paid=True,
                    date_paid=datetime.now(),
                    payment_method=method,
                    transaction_id=uuid4().hex,
                    collected_by_id=current_user.id if current_user.role == "admin" else None,
                )
            )
        queries.append(sql_compile(stmt))
        session.execute(stmt)
        return make_response(
            jsonify(message="Fine paid successfully", queries=queries), HTTPStatus.OK
        )
