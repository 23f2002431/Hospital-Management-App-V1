from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask import render_template,request,redirect,url_for,session


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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registration',methods=["POST","GET"])
def registration():
    if request.method=="POST":
        name=request.form['username']
        email=request.form['email']
        password=request.form['password']
        
        user=User.query.filter_by(username=name,email=email).first()
        if user:
            return redirect(url_for('login'))
        new_user=User(username=name,email=email,password=password,role="patient")
        db.session.add(new_user)
        db.session.commit()
 
        return redirect(url_for('login'))
    return render_template('registration.html')

@app.route('/login',methods=["POST","GET"])
def login():
    if request.method=="POST":
        name=request.form['frontend_name']
        password=request.form['frontend_password']

        user=User.query.filter_by(username=name,password=password).first()
        if user and user.role=="patient":
            return redirect(url_for('patient_dashboard'))
        
        elif user and user.role=="doctor":
            return redirect(url_for('doctor_dashboard'))
        
        elif user and user.role=="admin":
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html',error_message="You are new user please register first")
    return render_template('login.html')




@app.route('/patient_dashboard')
def patient_dashboard ():
    return render_template('patient_dashboard.html')


@app.route('/doctor_dashboard')
def doctor_dashboard():
    return render_template('doctor_dashboard.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')


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



