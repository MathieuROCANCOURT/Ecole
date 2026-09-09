# -*- coding: utf-8 -*-

"""
Classe Dao[Student]
"""
from daos import course_dao, address_dao
from models.course import Course
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

            cursor.execute(
                "SELECT MAX(student_nbr) + 1 AS student_nbr FROM student"
            )
            record = cursor.fetchone()

            student.student_nbr = record.__getattribute__("student_nbr")

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
            record.__getattribute__("first_name"),
            record.__getattribute__("last_name"),
            record.__getattribute__("age")
        )

        student.student_nbr = record.__getattribute__("student_nbr")

        student.address = address_dao.AddressDao().read(
            record.__getattribute__("id_address")
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
            record = cursor.fetchone()

            list_courses: list[Course] = []
            for id_course in record.__getattribute__("id_courses").split(','):
                course = course_dao.CourseDao().read(id_course)
                if course is not None:
                    list_courses.append(course)

            student.courses_taken = list_courses
        return student

    def update(self, student: Student) -> bool:
        """Met à jour en BD l'entité Student correspondant à student, pour y correspondre

        :param student: cours déjà mis à jour en mémoire
        :return: True si la mise à jour a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            return cursor.rowcount > 0

    def delete(self, student: Student) -> bool:
        """Supprime en BD l'entité Student correspondant à student

        :param student: cours dont l'entité Student correspondante est à supprimer
        :return: True si la suppression a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            return cursor.rowcount > 0
