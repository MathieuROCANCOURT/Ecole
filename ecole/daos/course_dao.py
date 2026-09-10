# -*- coding: utf-8 -*-

"""
Classe Dao[Course]
"""
from models.course import Course
from daos.dao import Dao
from dataclasses import dataclass
from typing import Optional

from models.student import Student
from models.teacher import Teacher


@dataclass
class CourseDao(Dao[Course]):
    def create(self, course: Course) -> int:
        """Crée en BD l'entité Course correspondant au cours course

        :param course: à créer sous forme d'entité Course en BD
        :return: l'id de l'entité insérée en BD (0 si la création a échoué)
        """
        if course.teacher is None or course.teacher.id is None:
            print("Pas de professeur")
            return 0
        with Dao.connection.cursor() as cursor:
            sql = """
                    INSERT INTO course(name, start_date, end_date, id_teacher)
                    VALUES (%s,%s,%s,%s);
                """
            cursor.execute(sql, (course.name, course.start_date, course.end_date, course.teacher.id))

        return cursor.lastrowid

    def read(self, id_course: int) -> Optional[Course]:
        """Renvoit le cours correspondant à l'entité dont l'id est id_course
           (ou None s'il n'a pu être trouvé)"""
        course: Optional[Course]

        with Dao.connection.cursor() as cursor:
            sql = """
                    SELECT * FROM course
                    JOIN teacher ON course.id_teacher = teacher.id_teacher
                    JOIN person ON person.id_person = teacher.id_person
                    WHERE course.id_course=%s;
                """
            cursor.execute(sql, (id_course,))
            record = cursor.fetchone()
        if record is not None:
            course = Course(record["name"],
                            record["start_date"],
                            record["end_date"])
            course.id = record["id_course"]

            course.set_teacher(Teacher(record["first_name"],
                                       record["last_name"],
                                       record["age"],
                                       record["hiring_date"]))
            with Dao.connection.cursor() as cursor:
                sql = """
                        SELECT student.student_nbr, first_name, last_name, age FROM course
                        JOIN takes ON takes.id_course = course.id_course
                        JOIN student ON student.student_nbr = takes.student_nbr
                        JOIN person ON person.id_person = student.id_person
                        WHERE course.id_course=%s;
                    """
                cursor.execute(sql, (id_course,))
                record = cursor.fetchall()

                for student_coord in record:
                    student = Student(
                        student_coord["first_name"],
                        student_coord["last_name"],
                        student_coord["age"],
                    )
                    student.student_nbr = student_coord["student_nbr"]
                    student.students_nb -= 1
                    course.add_student(student)

        else:
            course = None

        return course

    def update(self, course: Course) -> bool:
        """Met à jour en BD l'entité Course correspondant à course, pour y correspondre

        :param course: cours déjà mis à jour en mémoire
        :return: True si la mise à jour a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            sql = """
                    UPDATE course
                    SET name=%s, start_date=%s, end_date=%s, id_teacher=%s
                    WHERE id_course=%s;
                """
            cursor.execute(sql, (course.name, course.start_date, course.end_date, course.teacher.id, course.id))
            return cursor.rowcount > 0

    def delete(self, course: Course) -> bool:
        """Supprime en BD l'entité Course correspondant à course

        :param course: cours dont l'entité Course correspondante est à supprimer
        :return: True si la suppression a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            sql = """
                    DELETE FROM takes
                    WHERE id_course = %s;
                """
            cursor.execute(sql, (course.id,))

            for student in course.students_taking_it:
                student.courses_taken.remove(course)

            sql = """
                    DELETE FROM course
                    WHERE id_course=%s;
                """
            cursor.execute(sql, (course.id,))

            return cursor.rowcount > 0
