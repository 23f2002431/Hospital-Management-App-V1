from flask_sqlalchemy import SQLAlchemy
from flask import Flask, flash
from flask import render_template,request,redirect,url_for,session
from datetime import datetime,timedelta,date


app= Flask(__name__)

from flask import Flask
app = Flask(__name__)

app.secret_key = "123"    #thisnis for secerete key


#database configuration
app.config['SQLALCHEMY_DATABASE_URI']='postgresql://postgres:rigveda26@localhost:5432/hms_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False



#initialize the database
db = SQLAlchemy(app)



def next_n_dates():
    today=date.today()
    dates=[]
    for i in range(7):
        next_day=today+timedelta(i)
        date_str=next_day.strftime('%Y-%m-%d')
        dates.append(date_str)
    return (dates)


#####---------------------- Models -----------------------#############

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
    user_id = db.Column(db.Integer) 
    patient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    treatment_name=db.Column(db.String(250))

    patient = db.relationship('User', foreign_keys=[patient_id], backref='appointments_as_patient')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='appointments_as_doctor')
   


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
    
    patient_id = session['id']  
    patient_name = session['name']
    departments = Department.query.all()  
    appointments = Appointment.query.filter_by(patient_id=patient_id).all()
    return render_template('patient_dashboard.html',patient_name=patient_name, departments=departments,appointments=appointments)





## edit patient profile




@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    # check if patient is logged in
    if session.get('role') != 'patient':
        return redirect(url_for('login'))

    patient_id = session.get('id')
    patient = User.query.get(patient_id)

    if request.method == 'POST':
        updated_name = request.form.get('updated_name')
        updated_email = request.form.get('updated_email')

        # update changed values only
        patient.username = updated_name
        patient.email = updated_email

        db.session.commit()
        flash("Profile information updated successfully", "success")
        return redirect(url_for('patient_dashboard'))

    return render_template("edit_profile.html", patient=patient)



@app.route('/see_department/<int:dept_id>')
def see_department(dept_id):
    department = Department.query.get_or_404(dept_id)
    doctors = User.query.filter_by(department_id=dept_id, role='doctor').all()
    return render_template('patient_department_doctors.html', department=department, doctors=doctors)






@app.route('/doctor_dashboard')
def doctor_dashboard():
    
    doctor_id = session['id']
    doctor_name = session['name']

    # to give availability
    avail = DoctorAvailability.query.filter_by(doctor_id=doctor_id).all()

    # Fetch appointments for this doctor
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.date.desc()).all()

    treatments = Treatment.query.all()
    return render_template(
        'doctor_dashboard.html',doctor_name=doctor_name,availabilities=avail,appointments=appointments,treatments=treatments)

@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    search_query = request.args.get('search', '').strip()

    # to serach doctors,departments and patients 
    if search_query:
        departments = Department.query.filter(Department.department_name.ilike(f"%{search_query}%")).all()
        patients = User.query.filter(User.role=='patient', User.username.ilike(f"%{search_query}%")).all()
        doctors = User.query.filter(User.role=='doctor', User.username.ilike(f"%{search_query}%")).all()
    else:
        departments = Department.query.all()
        patients = User.query.filter_by(role='patient').all()
        doctors = User.query.filter_by(role='doctor').all()

    appointments = Appointment.query.order_by(Appointment.date.desc()).all()

    return render_template('admin_dashboard.html',departments=departments,patients=patients,doctors=doctors,appointments=appointments)


@app.route('/admin_dashboard/create_doctor',methods=['GET','POST'])
def create_doctor(): 
    departments=Department.query.all()
    if request.method=='POST':
        name=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')
        department_id=request.form.get('department_id')
        experience = request.form.get('experience')         
        qualifications = request.form.get('qualifications') 

        reg_dpt=User.query.filter_by(username=name).first()
        if reg_dpt:
            flash('Doctor already exists','error')
            return redirect(url_for('create_doctor'))
            
#flash is left to be added in the frontend
        new_dcot=User(username=name,password=password,email=email,role='doctor',department_id=department_id,experience=experience,qualifications=qualifications)
        db.session.add(new_dcot)
        db.session.commit()
        flash('You added a new doctor','success')
        return redirect(url_for('admin_dashboard'))
        

    return render_template('create_doctor.html',departments=departments)

@app.route('/admin_dashboard/view_doctor/<int:dept_id>')
def view_dct(dept_id):
    doctors=User.query.filter_by(department_id=dept_id)

    return render_template('view_doctor.html',doctors=doctors)

#to blacklist 
@app.route('/admin_dashboard/blacklist/<int:user_id>')
def blacklist(user_id):
    user=User.query.filter_by(id=user_id).first()
    user.blacklisted=True
    db.session.commit()
    flash("Patient has been blacklisted.", "danger")

    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/remove_blacklist/<int:user_id>')
def remove_blacklist(user_id):
    user=User.query.filter_by(id=user_id).first()
    user.blacklisted=False
    db.session.commit()
    flash("Patient removed from blacklist.", "success")

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
        flash('Doctor details updated successfully','success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('edit_doctor.html',doctor=doctor,departments=departments)




#3blacklist and delete doctor == okayyyyyyy
@app.route('/admin_dashboard/toggle_blacklist_doctor/<int:doctor_id>')
def toggle_blacklist_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)

    doctor.blacklisted = not doctor.blacklisted  # toggle
    db.session.commit()

    if doctor.blacklisted:
        flash("Doctor has been blacklisted.","danger")
    else:
        flash("Doctor removed from blacklist.","success")

    return redirect(url_for('admin_dashboard'))


@app.route('/admin_dashboard/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    doctor = User.query.get_or_404(doctor_id)

    appointments = Appointment.query.filter_by(doctor_id=doctor_id).first()
    if appointments:
        flash("Cannot delete doctor. Existing appointments found.", "error")
        return redirect(url_for('admin_dashboard'))
    
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
            flash('Department already exists')
            return redirect(url_for('add_department'))     
          
        new_dpt=Department(department_name=depar_name,description=dsc)
        db.session.add(new_dpt)
        db.session.commit()
        flash('New department added sucessfully.')
        return redirect(url_for('admin_dashboard'))
                        
    return render_template('add_department.html')


@app.route('/doctor_dashboard/availability', methods=['GET', 'POST'])
def doctor_availability():
    doctor_id = session['id']

    # Step 1: get next dates
    dates = next_n_dates()  # list of date objects

    # Step 2: fetch existing availability
    existing = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date.in_(dates)
    ).all()

    # Step 3: map existing rows
    existing_map = {a.date: a for a in existing}

    # Step 4: create missing rows
    created = False
    for d in dates:
        if d not in existing_map:
            new_row = DoctorAvailability(
                doctor_id=doctor_id,
                date=d,
                morning=False,
                evening=False
            )
            db.session.add(new_row)
            created = True

    if created:
        db.session.commit()

        #  fetch again after commit
        existing = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.date.in_(dates)
        ).all()

        existing_map = {a.date: a for a in existing}

    # Step 5: SAFE access (NO KeyError)
    availability_list = [existing_map.get(d) for d in dates]

    return render_template(
        "doctor_availability.html",
        availabilities=availability_list
    )

@app.route('/doctor_dashboard/toggle_availability',methods=['POST'])
def toggle_availability():

    doctor_id=session.get('id')
    date=request.form.get('id')
    slot=request.form.get('slot')
    availability=DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        date=date
    ).first()

    if availability:
        if slot=="morning":
            availability.morning=not availability.morning
        elif slot=="evening":
            availability.evening=not availability.evening

        db.session.commit()

    if not doctor_id:
        return redirect(url_for('registration'))
    
    return redirect(url_for('doctor_availability'))

@app.route('/book_appointment/<int:doctor_id>',methods=['GET'])
def book_appointment(doctor_id):
    patient_id=session.get("id")
    patient = User.query.get(patient_id)
    if patient.blacklisted:
        flash("You are restricted from booking appointments.", "danger")
        return redirect(url_for('patient_dashboard'))


    doctor=User.query.get(doctor_id)
    if doctor.blacklisted:
        flash("This doctor is currently unavailable for booking.", "danger")
        return redirect(url_for('patient_dashboard'))

    dates=next_n_dates()
    date_strings=[str(d) for d in dates]
    availability=DoctorAvailability.query.filter(DoctorAvailability.doctor_id==doctor_id,DoctorAvailability.date.in_(date_strings)).all()
    availability_map={a.date:a for a in availability}
    sorted_availability=[availability_map.get(str(d)) for d in dates]

    return render_template(
        "book_appointment.html",doctor=doctor,availabilities=sorted_availability
    )

@app.route('/confirm_booking',methods=['POST'])
def confirm_booking():
    patient_id=session.get("id")
    if not patient_id:
        return redirect(url_for('sign_in'))
    

    patient = User.query.get(patient_id)
    if patient.blacklisted:
        flash("Your account is restricted. Appointment booking is disabled.", "danger")
        return redirect(url_for('patient_dashboard'))

    doctor_id=request.form.get("doctor_id")
    date=request.form.get("date")
    slot=request.form.get("slot")

    doctor = User.query.get(doctor_id)

    if doctor.blacklisted:
        flash("This doctor is no longer accepting appointments.", "danger")
        return redirect(url_for('patient_dashboard'))


    #prevent double double booking
    existing=Appointment.query.filter_by(
        doctor_id=doctor_id,
        patient_id=patient_id,
        date=date,
        time=slot

    ).first()

    if existing:
        flash("You already booked this slot,","warning")
        return redirect(url_for('book_appointment',doctor_id=doctor_id))
    
    #make an appointment

    appt=Appointment(
        date=date,
        time=slot,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status="Booked"
    )

    db.session.add(appt)

    availability=DoctorAvailability.query.filter_by(
        doctor_id=doctor_id,
        date=date
    ).first()
    if availability:
        if slot == 'morning':
            availability.morning = False
        elif slot == 'evening':
            availability.evening = False

    db.session.commit()

    flash("Appointment booked sucessfully","success")
    return redirect(url_for('patient_dashboard'))

# @app.route('/cancel_appointment/<int:appointment_id>')
# def cancel_appointment(apppointment _id):
#     appointment=Appointment.query.get_or_404(appointment_id)
#     db.session.delete(appointment)
#     db.session.commit()
#     flash('Appointment cancelled sucessfully.','iinfo')
#     return redirect(url_for('patient_dashboard'))
@app.route('/cancel_appointment/<int:appt_id>', methods=['POST'])
def cancel_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "Cancelled"
    db.session.commit()
    flash("Appointment cancelled successfully", "success")
    return redirect(url_for('patient_dashboard'))



@app.route('/admin_dashboard/appointments')
def admin_appointments():
    
    # to fetch all appointments 
    appointments = Appointment.query.filter(Appointment.status != "Cancelled").order_by(Appointment.date.desc()).all()

    return render_template('admin_appointments.html', appointments=appointments)



# @app.route('/admin_dashboard/delete_appointment/<int:appt_id>', methods=['POST'])
# def delete_appointment(appt_id):
#     if 'id' not in session or session.get('role') != 'admin':
#         return redirect(url_for('login'))

#     appt = Appointment.query.get_or_404(appt_id)
#     db.session.delete(appt)
#     db.session.commit()
#     flash("Appointment deleted successfully", "success")
#     return redirect(url_for('admin_appointments'))

@app.route('/delete_appointment/<int:appt_id>', methods=['POST'])
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash("Appointment deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_dashboard/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    patient = User.query.filter_by(id=patient_id, role='patient').first_or_404()
    db.session.delete(patient)
    db.session.commit()
    flash("Patient deleted successfully", "success")
    return redirect(url_for('admin_dashboard'))


@app.route('/doctor_dashboard/appointments', methods=['GET', 'POST'])
def doctor_assign_treatment():
    if 'id' not in session or session.get('role') != 'doctor':
        return redirect(url_for('login'))

    doctor_id = session.get('id')

    # Fetch appointments that are booked or pending
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(Appointment.date.desc()).all()
    treatments = Treatment.query.all()

    if request.method == 'POST':
        appt_id = request.form.get('appointment_id')
        treatment_id = request.form.get('treatment_id')
        appointment = Appointment.query.get(appt_id)
        if appointment:
            appointment.treatment = treatment_id
            appointment.status = "Completed"
            db.session.commit()
            flash("Treatment assigned successfully.", "success")
        return redirect(url_for('doctor_assign_treatment'))

    return render_template('doctor_assign_treatment.html', appointments=appointments, treatments=treatments)


@app.route('/assign_treatment', methods=['POST'])
def assign_treatment():
    if 'id' not in session or session.get('role') != 'doctor':
        return redirect(url_for('login'))

    appointment_id = request.form.get('appointment_id')
    treatment_name = request.form.get('treatment_name')

    appointment = Appointment.query.get_or_404(appointment_id)

    # Assign the treatment text and mark as completed
    appointment.treatment_name = treatment_name
    appointment.status = "Completed"

    db.session.commit()
    flash("Treatment assigned and appointment marked as completed.", "success")
    return redirect(url_for('doctor_dashboard'))
from werkzeug.security import generate_password_hash
#run the app and create a database
if __name__=='__main__':
    with app.app_context():   ##needed for db operations

        db.create_all()      #create the database and the tables
        existing_admin=User.query.filter_by(role="admin").first()

        if not existing_admin:
            admin_db=User(
                username="admin",
                password=generate_password_hash("admin"),
                email="rigveda26@gmail.com",
                role="admin"
            )
            db.session.add(admin_db)
            db.session.commit()
    app.run(debug=False)


