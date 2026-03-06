from dataclasses import dataclass


@dataclass(frozen=True)
class Message:

    @dataclass(frozen=True)
    class Database:
        CONNECT_MYSQL_ERROR = "Error connecting to MySQL"
        CONNECT_MONGO_ERROR = "Error connecting to MongoDB"
        DATABASE_NAME_IS_MISSING_FOR_THE_USER = "Database name is missing for the user."

    @dataclass(frozen=True)
    class Company:
        NOT_FOUND = "Company not found"
        COMPANY_ALREADY_EXISTS = "Company already exists"
        COMPANY_NOT_FOUND = "Company does not exist"

    @dataclass(frozen=True)
    class Auth:
        INVALID_OR_MISSING_CREDENTIALS = "Invalid or missing credentials"
        # DATABASE_OB_NOT_EXIST = "会社情報が存在しないため、ログインできませんでした。"
        # CANNOT_LOGIN_BECASE_ALREADY = "既にログインしているオペレーターの為、ログイン出来ません。"
        # CANNOT_LOGIN_TWO_USER_WITH_ONE_BROWSER = "このブラウザでは他のオペレーターがログイン中のため、ログインできません。"
        # USER_DOES_NOT_HAVE_ACCESS_TO_THE_APPLICATION = "権限がありません。システム担当者へご相談ください。"
        TOKEN_EXPIRED = "Token expired!"