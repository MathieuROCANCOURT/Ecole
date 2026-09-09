#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Application de gestion d'une école
"""

from business.school import School


def main() -> None:
    """Programme principal."""
    print("""\
--------------------------
Bienvenue dans notre école
--------------------------""")

    school: School = School()

    # supprimer toutes les données dans les tables
    school.reset_database()

    # initialisation d'un ensemble de cours, enseignants et élèves composant l'école
    school.init_static()

    # affichage de la liste des cours, leur enseignant et leurs élèves
    school.display_courses_list()


if __name__ == '__main__':
    main()
