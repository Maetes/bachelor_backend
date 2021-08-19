from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import mysql

db = SQLAlchemy()
class History(db.Model):
    __tablename__ = 'dbs_History'

    id = db.Column(mysql.INTEGER(), primary_key=True)
    Zeitstempel= db.Column(mysql.TIMESTAMP(), nullable=False)
    Algorithmus= db.Column(mysql.TINYTEXT(), nullable=False)
    Dataset= db.Column(mysql.TINYTEXT(), nullable=False)
    Support= db.Column(mysql.TINYTEXT(), nullable=False)
    Confidence= db.Column(mysql.TINYTEXT(), nullable=True)
    Association_Start_CPU= db.Column(mysql.TINYTEXT(), nullable=True)
    Association_Start_Memory= db.Column(mysql.TINYTEXT(), nullable=True)
    FrequentItems_Start_CPU= db.Column(mysql.TINYTEXT(), nullable=False)
    FrequentItems_Start_Memory= db.Column(mysql.TINYTEXT(), nullable=False)
    Association_Ende_CPU= db.Column(mysql.MEDIUMTEXT(), nullable=True)
    Association_Ende_Memory= db.Column(mysql.MEDIUMTEXT(), nullable=True)
    Association_Ende_Zeit= db.Column(mysql.TEXT(), nullable=True)
    Association_Ende_Association_rules= db.Column(mysql.LONGTEXT(), nullable=True)
    FrequentItems_Ende_CPU= db.Column(mysql.MEDIUMTEXT(), nullable=False)
    FrequentItems_Ende_Memory= db.Column(mysql.MEDIUMTEXT(), nullable=False)
    FrequentItems_Ende_Zeit= db.Column(mysql.TEXT(), nullable=False)
    FrequentItems_Ende_Frequent_items= db.Column(mysql.LONGTEXT(), nullable=False)

    def __repr__(self):
        return '<History %r>' % self.Zeitstempel