from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash
from flask import render_template,request,redirect,url_for,session
from datetime import datetime,timedelta,date


app= Flask(__name__)

from flask import Flask
app = Flask(__name__)

app.secret_key = "123"      # add this line


#database configuration
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False



#initialize the database
db = SQLAlchemy(app)


#####---------------------- Models -----------------------#############
def next_n_dates():
    today=date.today()
    dates=[]
    for i in range(7):
        next_day=today+timedelta(i)
        date_str=next_day.strftime('%Y-%m-%d')
        dates.append(date_str)
    return (dates)



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

    experience=db.Column(db.Integer,nullable=True)
    qualifications=db.Column(db.String(250),nullable=True)

    blacklisted=db.Column(db.Boolean, default=False)

    availabilities = db.relationship('DoctorAvailability', back_populates='doctor', cascade="all, delete-orphan")


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



class DoctorAvailability(db.Model):
    __tablename__='doctor_availability'
    id=db.Column(db.Integer,primary_key=True)
    doctor_id=db.Column(db.Integer,db.ForeignKey('users.id'),nullable=False)
    date=db.Column(db.String(20),nullable=False)
    morning=db.Column(db.Boolean,default=True)
    evening=db.Column(db.Boolean,default=True)
    doctor=db.relationship('User',back_populates='availabilities')
    




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
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
            return redirect(url_for('patient_dashboard'))
        
        elif user and user.role=="doctor":
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
            return redirect(url_for('doctor_dashboard'))
        
        elif user and user.role=="admin":
            session['name']=user.username
            session['id']=user.id
            session['role']=user.role
            return redirect(url_for('admin_dashboard'))
        return render_template('login.html',error_message="You are new user please register first")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('name',None)
    session.pop('id',None)
    session.pop('role',None)
    return redirect(url_for('index'))



@app.route('/patient_dashboard')
def patient_dashboard ():
    return render_template('patient_dashboard.html')


@app.route('/doctor_dashboard')
def doctor_dashboard():
    doctor_name=session['name']
    return render_template('doctor_dashboard.html',doctor_name=doctor_name)


@app.route('/admin_dashboard')
def admin_dashboard():
    patient=User.query.filter_by(role='patient').all()
    print(patient,'This is patient data')
    doctors=User.query.filter_by(role='doctor').all()
    departments=Department.query.all()
    return render_template('admin_dashboard.html',patient=patient,departments=departments,doctors=doctors)


@app.route('/admin_dashboard/create_doctor',methods=['GET','POST'])
def create_doctor(): 
    departments=Department.query.all()
    if request.method=='POST':
        name=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')
        department_id=request.form.get('department_id')
        experience = request.form.get('experience')          # NEW FIELD
        qualifications = request.form.get('qualifications') 

        reg_dpt=User.query.filter_by(username=name).first()
        if reg_dpt:
            flash('Doctor already exists','error')
            return render_template('admin_dashboard.html', departments=departments)
            
        
        new_dcot=User(username=name,password=password,email=email,role='doctor',department_id=department_id,experience=experience,qualifications=qualifications)
        db.session.add(new_dcot)
        db.session.commit()
        flash('You added a new doctor','success')
        return render_template('admin_dashboard.html', departments=departments)
        

    return render_template('create_doctor.html',departments=departments)

@app.route('/admin_dashboard/view_doctor/<int:dept_id>')
def view_dct(dept_id):
    doctors=User.query.filter_by(department_id=dept_id)

    return render_template('view_doctor.html',doctors=doctors)


@app.route('/admin_dashboard/blacklist/<int:user_id>')
def blacklist(user_id):
    user=User.query.filter_by(id=user_id).first()
    user.blacklisted=True
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/remove_blacklist/<int:user_id>')
def remove_blacklist(user_id):
    user=User.query.filter_by(id=user_id).first()
    user.blacklisted=False
    db.session.commit()
    return redirect(url_for('admin_dashboard'))


@app.route('/edit_doctor/<int:doctor_id>',methods=['GET','POST'])
def edit_doctor(doctor_id):
    doctor=User.query.filter_by(id=doctor_id,role='doctor').first_or_404()
    departments=Department.query.all()

    if request.method=='POST':
        doctor.username=request.form.get('username')
        doctor.email=request.form.get('email')
        doctor.department_id=request.form.get('department_id')
        doctor.experience = request.form.get('experience')
        doctor.qualifications = request.form.get('qualifications')
        db.session.commit()
        flash('Doctor details are updated sucessfully','success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_doctor.html',doctor=doctor,departments=departments)




#3blacklist and delete doctor ==chatgpt okayyyyyyy
@app.route('/admin_dashboard/toggle_blacklist_doctor/<int:doctor_id>')
def toggle_blacklist_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)

    doctor.blacklisted = not doctor.blacklisted  # toggle
    db.session.commit()

    if doctor.blacklisted:
        flash("Doctor has been blacklisted.")
    else:
        flash("Doctor removed from blacklist.")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin_dashboard/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)
    db.session.delete(doctor)
    db.session.commit()
    flash("Doctor deleted successfully.")
    return redirect(url_for('admin_dashboard'))



@app.route('/admin_dashboard/add_department',methods=['GET','POST'])
def add_department(): 
    if request.method=="POST":
        depar_name=request.form.get('department_name')
        dsc=request.form.get('description')
        reg_dpt=Department.query.filter_by(department_name=depar_name).first() 
        if reg_dpt:
            flash('department already exists')
            return redirect(url_for('add_department'))     
          
        new_dpt=Department(department_name=depar_name,description=dsc)
        db.session.add(new_dpt)
        db.session.commit()
        flash('hey you added a new department')
        return redirect(url_for('admin_dashboard'))
                        
    return render_template('add_department.html')


@app.route('/doctor_dashboard/availability',methods=['GET','POST'])
def doctor_availability():
    doctor_id=session['id']
    dates=next_n_dates()
    existing=DoctorAvailability.query.filter(DoctorAvailability.doctor_id==doctor_id,DoctorAvailability.date.in_(dates)).all()

    existing_map={a.date: a for a in existing}
    print(existing_map)

    created=False
    for d in dates:
        if d not in existing_map:
            new_row=DoctorAvailability(
                doctor_id=doctor_id,
                date=d,
                morning=False,
                evening=False
            )
            db.session.add(new_row)
            created=True
    if created:
        db.session.commit()

    availability_list=[existing_map[d] for d in dates]

    return render_template("doctor_availability.html",availabilities=availability_list)

    



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



