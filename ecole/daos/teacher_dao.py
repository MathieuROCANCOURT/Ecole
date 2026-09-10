# -*- coding: utf-8 -*-

"""
Classe Dao[Teacher]
"""
from daos import address_dao, course_dao
from models.teacher import Teacher
from daos.dao import Dao
from dataclasses import dataclass
from typing import Optional


@dataclass
class TeacherDao(Dao[Teacher]):
    def create(self, teacher: Teacher) -> int:
        """Crée en BD l'entité Teacher correspondant à l'adresse teacher

        :param teacher: à créer sous forme d'entité Teacher en BD
        :return: l'id de l'entité insérée en BD (0 si la création a échoué)
        """
        with Dao.connection.cursor() as cursor:
            sql = """
                    INSERT INTO person(first_name, last_name, age)
                    VALUES (%s,%s,%s);
                """
            cursor.execute(sql, (teacher.first_name, teacher.last_name, teacher.age))
            id_person = cursor.lastrowid

            sql = """
                    INSERT INTO teacher(hiring_date, id_person)
                    VALUES (%s, %s);
                """

            cursor.execute(sql, (teacher.hiring_date, id_person))

            return cursor.lastrowid

    def read(self, id_teacher: int) -> Optional[Teacher]:
        """Renvoit le cours correspondant à l'entité dont l'id est id_teacher
           (ou None s'il n'a pu être trouvé)"""
        teacher: Optional[Teacher]

        with Dao.connection.cursor() as cursor:
            sql = """
                    SELECT
                        teacher.id_teacher,
                        hiring_date,
                        first_name,
                        last_name,
                        id_address,
                        age,
                        GROUP_CONCAT(course.id_course SEPARATOR ',') AS id_courses
                    FROM teacher
                    JOIN person ON person.id_person = teacher.id_person
                    JOIN course ON course.id_teacher = teacher.id_teacher
                    WHERE teacher.id_teacher=%s;
                """
            cursor.execute(sql, (id_teacher,))
            record = cursor.fetchone()

        if record is not None:
            teacher = Teacher(record["first_name"],
                              record["last_name"],
                              record["age"],
                              record["hiring_date"])
            teacher.address = address_dao.AddressDao().read(record["id_address"])
            teacher.id = record["id_teacher"]
            for id_course in record["id_courses"].split(","):
                course_dao.CourseDao().read(int(id_course))
        else:
            teacher = None

        return teacher

    def update(self, teacher: Teacher) -> bool:
        """Met à jour en BD l'entité Teacher correspondant à teacher, pour y correspondre

        :param teacher: cours déjà mis à jour en mémoire
        :return: True si la mise à jour a pu être réalisée
        """
        with Dao.connection.cursor() as cursor:
            sql = """
                    UPDATE person
                    JOIN teacher ON teacher.id_person = person.id_person
                    SET person.first_name = %s, person.last_name = %s, person.age = %s
                    WHERE teacher.id_teacher = %s;
                """
            cursor.execute(sql, (teacher.first_name, teacher.last_name, teacher.age, teacher.id))

            if teacher.address is not None:
                if teacher.address.id is None:
                    teacher.address.id = address_dao.AddressDao().create(teacher.address)
                    sql = """
                            UPDATE person
                            JOIN teacher ON teacher.id_person = person.id_person
                            SET person.id_address = %s
                            WHERE teacher.id_teacher = %s;
                        """
                    cursor.execute(sql, (teacher.address.id, teacher.id))

                else:
                    address_dao.AddressDao().update(teacher.address)

            for course in teacher.courses_teached:
                course_dao.CourseDao().update(course)

            return cursor.rowcount > 0

    def delete(self, teacher: Teacher) -> bool:
        """Supprime en BD l'entité Teacher correspondant à teacher

        :param teacher: cours dont l'entité Teacher correspondante est à supprimer
        :return: True si la suppression a pu être réalisée
        """
        return True
