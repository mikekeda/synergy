from models import User, Course, UserCourse

# Create User table.
if not User.table_exists():
    User.create_table()

if not Course.table_exists():
    # Create Course table.
    Course.create_table()

    # Add test courses.
    test_courses = (
        ('P012345', 'Python-Base'),
        ('P234567', 'Python-Database'),
        ('H345678', 'HTML'),
        ('J456789', 'Java-Base'),
        ('JS543210', 'JavaScript-Base'),
    )

    for code, name in test_courses:
        Course(code=code, name=name).save()

# Create UserCourse table.
if not UserCourse.table_exists():
    UserCourse.create_table()
