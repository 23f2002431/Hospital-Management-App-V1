from flask_sqlalchemy import SQLAlchemy
from flask import Flask


app= Flask(__name__)

#database configuration
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

#initialize the database
db = SQLAlchemy(app)






#####---------------------- Models -----------------------#############
from datetime import datetime

class User(db.Model):
    __tablename__='users'
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(150),unique=True,nullable=False)
    email=db.Column(db.String(150),unique=True,nullable=False)
    password=db.Column(db.String(150),nullable=False)
    role=db.Column(db.String(50),nullable=False)#eg doctor admin patient
    created_at=db.Column(db.DateTime,default=datetime.utcnow)

    #connection esta.. bw dept and user many to one
    department_id=db.Column(db.Integer,db.ForeignKey('departments.id'),nullable=True)

    #reverse relationship
    department=db.relationship("Department",back_populates="doctors")



class Department(db.Model):
    __tablename__='departments'
    id=db.Column(db.Integer,primary_key=True)
    department_name=db.Column(db.String(100),unique=True,nullable=False)
    description=db.Column(db.Text,nullable=True)

    doctors=db.relationship("User",back_populates="department")


class Appointment(db.Model):
    __tablename__='appointment'

    id=db.Column(db.Integer,primary_key=True)
    date=db.Column(db.String(20))
    time=db.Column(db.String(20))
    status=db.Column(db.String(20),default='Booked')#pending approved or cancelled

    user_id=db.Column(db.Integer,db.ForeignKey("users.id"))
    treatment=db.Column(db.Integer,db.ForeignKey("treatment.id"),unique=True)


class Treatment(db.Model):
    __tablename__="treatment"

    id=db.Column(db.Integer,primary_key=True)
    treat_name=db.Column(db.String(100))
    description=db.Column(db.Text)



#run the app and create a database
if __name__=='__main__':
    with app.app_context():   ##needed for db operations

        db.create_all()      #create the database and the tables
        existing_admin=User.query.filter_by(username="admin").first()

        if not existing_admin:
            admin_db=User(
                username="admin",
                password="admin",
                email="rigveda26@gmail.com",
                role="admin"
            )
            db.session.add(admin_db)
            db.session.commit()
    app.run(debug=True)


