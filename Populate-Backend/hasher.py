import bcrypt
import argparse


def encode_password(plain_password):
    """
    Encodes a password using BCrypt, similar to Java's BCryptPasswordEncoder.
    """
    # bcrypt requires the password to be bytes, so we encode it to utf-8
    password_bytes = plain_password.encode("utf-8")

    # Generate a salt and hash the password
    # This matches the default strength (log_rounds=12 is common in Java Spring defaults,
    # but Python's bcrypt defaults to 12 as well usually, or takes a salt)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)

    return hashed.decode("utf-8")


def check_password(plain_password, hashed_password):
    """
    Verifies a password against a hash.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")

    return bcrypt.checkpw(password_bytes, hashed_bytes)


def main():
    parser = argparse.ArgumentParser(description="BCrypt Password Encoder Tool")

    # Create mutually exclusive group so user either encodes or checks, not both
    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("-e", "--encode", help="The raw password to encode")
    group.add_argument(
        "-c",
        "--check",
        nargs=2,
        metavar=("PASSWORD", "HASH"),
        help="Check a raw password against a hash. Usage: -c 'mypassword' 'hashstring'",
    )

    args = parser.parse_args()

    if args.encode:
        print(f"--- BCrypt Encoder ---")
        print(f"Raw:    {args.encode}")
        print(f"Hashed: {encode_password(args.encode)}")

    elif args.check:
        raw_pw, hash_str = args.check
        result = check_password(raw_pw, hash_str)
        print(f"--- BCrypt Verifier ---")
        print(f"Match:  {result}")
        if result:
            print("✅ Password matches the hash.")
        else:
            print("❌ Password does not match.")


if __name__ == "__main__":
    main()
