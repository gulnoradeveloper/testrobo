"""Management commands.

    python -m app.cli create-admin --email admin@example.uz --first-name Admin --last-name User
(The password is read interactively, never from the command line.)
"""
import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password, password_problems
from app.models import User, UserRole


def create_admin(args) -> int:
    password = getpass.getpass("Parol: ")
    if password != getpass.getpass("Parolni tasdiqlang: "):
        print("Parollar mos emas", file=sys.stderr)
        return 1
    problems = password_problems(password, args.email)
    if problems:
        print("; ".join(problems), file=sys.stderr)
        return 1
    with SessionLocal() as db:
        user = db.scalars(select(User).where(User.email == args.email.lower())).first()
        if user:
            user.role = UserRole.ADMIN
            print("Mavjud foydalanuvchi administrator qilindi")
        else:
            db.add(User(first_name=args.first_name, last_name=args.last_name, email=args.email.lower(),
                        password_hash=hash_password(password), university="-", study_program="-",
                        role=UserRole.ADMIN))
            print("Administrator yaratildi")
        db.commit()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="communiai")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("create-admin")
    p.add_argument("--email", required=True)
    p.add_argument("--first-name", default="Admin")
    p.add_argument("--last-name", default="CommuniAI")
    args = parser.parse_args()
    return {"create-admin": create_admin}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
