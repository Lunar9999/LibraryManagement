from http import HTTPStatus

from flask import Response, jsonify, make_response, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    current_user,
    jwt_required,
)
from flask_restx import Namespace, Resource, fields
from sqlalchemy import and_, select, update

from src import models as md
from src import p_models as pmd
from src.auth.oauth import admin_required
from src.utils import check_password, session, sql_compile

auth_namespace = Namespace("Auth", description="Authentication operations", path="/")


register_input = auth_namespace.model(
    "RegisterInput",
    {
        "email": fields.String(required=True, description="Email"),
        "first_name": fields.String(required=True, description="First Name"),
        "last_name": fields.String(required=True, description="Last Name"),
        "password": fields.String(required=True, description="Password"),
    },
)

login_input = auth_namespace.model(
    "LoginInput",
    {
        "email": fields.String(required=True, description="Email"),
        "password": fields.String(required=True, description="Password"),
    },
)

make_admin_input = auth_namespace.model(
    "MakeAdminInput",
    {
        "email": fields.String(required=True, description="Email"),
    },
)


@auth_namespace.route("/register", methods=["POST"])
@auth_namespace.expect(register_input)
class Register(Resource):
    def post(self):
        data = request.json
        print(data)
        return Response(status=201)


@auth_namespace.route("/login", methods=["POST"])
@auth_namespace.expect(login_input)
class Login(Resource):
    def post(self):
        email = request.json.get("email", None)
        password = request.json.get("password", None)

        stmt = select(
            md.UserAccount.id,
            md.UserAccount.email,
            md.UserAccount.password,
            md.UserAccount.role,
            md.UserAccount.is_active,
        ).where(md.UserAccount.email == email)
        user = session.execute(stmt).mappings().first()
        if not user or not user.is_active or not check_password(password, user.password):
            return make_response(
                jsonify(message="Wrong username or password", query=str(stmt)),
                HTTPStatus.UNAUTHORIZED,
            )

        additional_claims = {"role": user.role}
        access_token = create_access_token(identity=user, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=user, additional_claims=additional_claims)
        return jsonify(access_token=access_token, refresh_token=refresh_token, query=str(stmt))


@auth_namespace.route("/refresh")
class Refresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """Create a new access token from a refresh token"""
        access_token = create_access_token(
            identity=current_user, additional_claims={"role": current_user.role}
        )
        return make_response(jsonify(access_token=access_token))


@auth_namespace.route("/make-admin")
class MakeAdmin(Resource):
    @admin_required
    @auth_namespace.expect(make_admin_input)
    def post(self):
        """Make a user an admin"""
        data = request.json
        email = data.get("email", None)
        stmt = select(md.UserAccount).where(
            md.UserAccount.email == email and md.UserAccount.role != "admin"
        )
        queries = [sql_compile(stmt)]
        user = session.execute(stmt).scalars().first()
        if not user:
            return make_response(
                jsonify(message="User not found or already an admin", queries=queries),
                HTTPStatus.NOT_FOUND,
            )

        update_stmt = (
            update(md.UserAccount).where(md.UserAccount.email == email).values(role="admin")
        )
        queries.append(sql_compile(update_stmt))
        try:
            session.execute(update_stmt)
            session.commit()
            return make_response(
                jsonify(message="User is now an admin", queries=queries), HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=queries), HTTPStatus.INTERNAL_SERVER_ERROR
            )


@auth_namespace.route("/users")
class ListUsers(Resource):
    @admin_required
    def get(self):
        stmt = select(md.UserAccount).order_by(md.UserAccount.first_name)
        users = session.execute(stmt).scalars().all()
        users = [pmd.ListUsersSchema.model_validate(user) for user in users]
        return {"users": [user.model_dump() for user in users], "queries": [sql_compile(stmt)]}


@auth_namespace.route("/users/<int:id>")
@auth_namespace.doc(params={"id": "User ID"})
class GetUser(Resource):
    @admin_required
    def get(self, id):
        stmt = select(md.UserAccount).where(md.UserAccount.id == id)
        user = session.execute(stmt).scalars().first()
        if not user:
            return make_response(
                jsonify(message="User not found", queries=[sql_compile(stmt)]),
                HTTPStatus.NOT_FOUND,
            )
        user = pmd.UserDetailSchema.model_validate(user)
        return {"user": user.model_dump(), "queries": [sql_compile(stmt)]}


@auth_namespace.route("/deactivate-user")
class DeactivateUser(Resource):
    @admin_required
    def post(self):
        data = request.json
        email = data.get("email", None)
        stmt = (
            update(md.UserAccount)
            .where(and_(md.UserAccount.email == email, md.UserAccount.is_active.is_(True)))
            .values(is_active=False)
        )
        queries = [sql_compile(stmt)]
        try:
            result = session.execute(stmt)
            if result.rowcount == 0:
                return make_response(
                    jsonify(message="User not found or already deactivated", queries=queries),
                    HTTPStatus.NOT_FOUND,
                )
            session.commit()
            return make_response(
                jsonify(message="User deactivated successfully", queries=queries), HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=queries), HTTPStatus.INTERNAL_SERVER_ERROR
            )


@auth_namespace.route("/activate-user")
class ActivateUser(Resource):
    @admin_required
    def post(self):
        data = request.json
        email = data.get("email", None)
        stmt = (
            update(md.UserAccount)
            .where(and_(md.UserAccount.email == email, md.UserAccount.is_active.is_(False)))
            .values(is_active=True)
        )
        queries = [sql_compile(stmt)]
        try:
            result = session.execute(stmt)
            if result.rowcount == 0:
                return make_response(
                    jsonify(message="User not found or already deactivated", queries=queries),
                    HTTPStatus.NOT_FOUND,
                )
            session.commit()
            return make_response(
                jsonify(message="User deactivated successfully", queries=queries), HTTPStatus.OK
            )
        except Exception as e:
            session.rollback()
            return make_response(
                jsonify(error=str(e), queries=queries), HTTPStatus.INTERNAL_SERVER_ERROR
            )
