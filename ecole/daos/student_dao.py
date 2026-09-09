# -*- coding: utf-8 -*-

"""
Classe Dao[Student]
"""
from daos import course_dao, address_dao
from models.address import Address
from models.student import Student
from daos.dao import Dao
from dataclasses import dataclass
from typing import Optional


@dataclass
class StudentDao(Dao[Student]):
    def create(self, student: Student) -> int:
        """Crée en BD l'entité Student correspondant au cours student

        :param student: à créer sous forme d'entité Student en BD
        :return: l'id de l'entité insérée en BD (0 si la création a échoué)
        """
        with Dao.connection.cursor() as cursor:
            sql = """
                    INSERT INTO person(first_name, last_name, age, id_address)
                    VALUES (%s,%s,%s,%s);
                """
            cursor.execute(sql, (student.first_name, student.last_name, student.age, student.address.id))
            id_person = cursor.lastrowid

            sql = """
                    INSERT INTO student(student_nbr, id_person)
                    SELECT COALESCE(MAX(student_nbr), 0) + 1, %s
                    FROM student;
                   """
            cursor.execute(sql, (id_person,))

            for course in student.courses_taken:
                sql = "INSERT INTO takes(student_nbr, id_course) VALUES (%s,%s);"
                cursor.execute(sql, (student.student_nbr, course.id))

            sql = """
                    SELECT student_nbr FROM student
                    WHERE id_person = %s
                """
            cursor.execute(sql, (id_person,))
            record = cursor.fetchone()

            student.student_nbr = record["student_nbr"]

            return student.student_nbr

    def read(self, student_nbr: int) -> Optional[Student]:
        """Renvoit l'étudiant correspondant à l'entité dont l'id est student_nbr
           (ou None s'il n'a pu être trouvé)"""
        student: Optional[Student]

        with Dao.connection.cursor() as cursor:
            sql = """
                    SELECT * FROM student
                    JOIN person ON student.id_person = person.id_person
                    WHERE student.student_nbr = %s;
                """

            cursor.execute(sql, (student_nbr,))
            record = cursor.fetchone()

        if record is None:
            return None

        student = Student(
            record["first_name"],
            record["last_name"],
            record["age"]
        )

        student.student_nbr = record["student_nbr"]

        student.address = address_dao.AddressDao().read(
            record["id_address"]
        )

        with Dao.connection.cursor() as cursor:
            sql = """
                SELECT
                    GROUP_CONCAT(id_course SEPARATOR ',') AS id_courses
                FROM student
                JOIN takes ON takes.student_nbr = student.student_nbr
                WHERE student.student_nbr = %s;
                """

            cursor.execute(sql, (student_nbr,))
            record_id_courses = cursor.fetchone()["id_courses"]

            if record_id_courses is not None:
                for id_course in record_id_courses.split(','):
                    course = course_dao.CourseDao().read(id_course)
                    if course is not None:
                        student.add_course(course)

        return student

    def update(self, student: Student) -> bool:
        """Met à jour en BD l'entité Student correspondant à student, pour y correspondre

        :param student: cours déjà mis à jour en mémoire
        :return: True si la mise à jour a pu être réalisée
        """

        with Dao.connection.cursor() as cursor:
            sql = """
                    DELETE FROM takes
                    WHERE student_nbr = %s;
                """
            cursor.execute(sql, (student.student_nbr,))

            sql = """
                    UPDATE person
                    JOIN student ON student.id_person = person.id_person
                    SET person.first_name = %s, person.last_name = %s, person.age = %s
                    WHERE student.student_nbr = %s;
                """
            cursor.execute(sql, (student.first_name, student.last_name, student.age, student.student_nbr))
            if student.address is not None:
                if student.address.id is None:
                    address_dao.AddressDao().create(student.address)
                    sql = """
                            UPDATE person
                            JOIN student ON student.id_person = person.id_person
                            SET person.id_address = %s
                            WHERE student.student_nbr = %s;
                        """
                    cursor.execute(sql, (student.address.id, student.student_nbr))

                else:
                    address_dao.AddressDao().update(student.address)

            for course in student.courses_taken:
                sql = """
                        INSERT INTO takes(student_nbr, id_course)
                        VALUES (%s, %s)
                    """
                cursor.execute(sql, (student.student_nbr, course.id))

            return cursor.rowcount > 0

    def delete(self, student: Student) -> bool:
        """Supprime en BD l'entité Student correspondant à student

        :param student: cours dont l'entité Student correspondante est à supprimer
        :return: True si la suppression a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            for course in student.courses_taken:
                course.students_taking_it.remove(student)
            sql = """
                    DELETE FROM takes
                    WHERE student_nbr = %s;
                """
            cursor.execute(sql, (student.student_nbr,))

            sql = """
                    DELETE student, person FROM person
                    JOIN student ON student.id_person = person.id_person
                    WHERE student.student_nbr = %s;
                """
            cursor.execute(sql, (student.student_nbr,))

            return cursor.rowcount > 0
