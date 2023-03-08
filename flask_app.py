import io
import csv
import os
from flask import Flask, Response
from flask import jsonify
from flask_sqlalchemy import SQLAlchemy
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file, make_response
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from flask_login import LoginManager,login_user,logout_user
from flask_login import login_required, current_user
from datetime import timedelta
from werkzeug.wsgi import FileWrapper
import secrets       #generates a random hex key

#import auxiliary  functions
from aux_module import Password_verify
from aux_module import Check_profile_data
import countries

#send email
from send_email import send_email, code_generator
from send_email import create_timestamp
from datetime import datetime
import api_weather

#map
from map import GPS_location, DrawMap

#constants
MY_EMAIL_ADDRESS=os.getenv('SENDER_EMAIL')
MYSQL_DB=os.getenv('MYSQL_DB')
ACTIVATION_CODE_RETRIES=10
ACTIVATION_CODE_LIFETIME=86400#seconds

#basedir
basedir = os.path.abspath(os.path.dirname(__file__))

#Create Flask app function
app=Flask(__name__)

app.config['SECRET_KEY']=secrets.token_hex()
app.config['SQLALCHEMY_DATABASE_URI'] =MYSQL_DB

#loggin session lifetime
app.config['PERMANENT_SESSION_LIFETIME']=timedelta(minutes=10)
app.config['SESSION_REFRESH_EACH_REQUEST']=True


#Declare LoginManager
loginManager=LoginManager()
loginManager.login_view='main.login'
loginManager.init_app(app)


#Declare SQLAlchemy
db=SQLAlchemy(app)

class credentials(UserMixin,db.Model):
    id=db.Column(db.Integer, primary_key=True)
    email =db.Column(db.String(120), unique=True, nullable=False)
    password= db.Column(db.String(80), nullable=False)
    name=db.Column(db.String(120),unique=False)
    firstname=db.Column(db.String(120),unique=False)
    birthdate=db.Column(db.String(20),unique=False)
    country=db.Column(db.String(80),unique=False)
    city=db.Column(db.String(100),unique=False)
    address=db.Column(db.String(200),unique=False)
    latitude=db.Column(db.Float)
    longitude=db.Column(db.Float)
    active=db.Column(db.Boolean)
    activation_code=db.Column(db.String(8))
    code_timestamp=db.Column(db.DateTime)
    code_retries=db.Column(db.Integer)
    api_user=db.Column(db.String(80))
    api_key=db.Column(db.String(8))

    def __repr__(self):
        return '<credentials %r>' % self.email

class parameters(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    parameter_name=db.Column(db.String(80),unique=True,nullable=False)
    bool_value=db.Column(db.Boolean,nullable=True)
    int_value=db.Column(db.Integer, nullable=True)
    string_value=db.Column(db.String(80),nullable=True)
    float_value=db.Column(db.Float,nullable=True)

    def __repr__(self):
        return '<parameters %r>' % self.parameter_name


#Instanciate Check_profile_data class
cpd=Check_profile_data()


################################################## MAIN BLUEPRINT ########################################################
main_blueprint=Blueprint('main',__name__,template_folder='templates')

############################################# AUTHENTIFICATION BLUEPRINT #################################################
auth_blueprint=Blueprint('auth',__name__,template_folder='templates')
@loginManager.user_loader
def load_user(user_id):
    return credentials.query.get(int(user_id))



###########################################################################################################################
#################################################### INDEX ################################################################
###########################################################################################################################
@main_blueprint.route('/')
def index():
    return render_template('index.html')



###########################################################################################################################
##################################################### SIGNUP ##############################################################
###########################################################################################################################
@auth_blueprint.route('/signup')
def signup():
    return render_template('signup.html')

@auth_blueprint.route('/signup',methods=['POST'])
def signup_post():

    #check if "send email" is active by reading the database
    param_email_status=parameters.query.filter_by(parameter_name='disable_email_send').first()
    disable_email=param_email_status.bool_value

    #read input data from form
    email=request.form.get('email')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')
    user=credentials.query.filter_by(email=email.lower()).first()

    #password verify declaration
    pwv=Password_verify(password)

    if user:
        flash('Email already exits')
        return redirect(url_for('auth.signup'))
    if password!=confirm_password:
        flash('Password and confirm password not identical')
        return redirect(url_for("auth.signup"))
    if not(pwv.check_password_has_lower() and pwv.check_password_has_upper() \
        and pwv.check_password_has_special() and pwv.check_password_lenght()):
        flash('Password missing uppercase, lowercase, 1,2,.. !,#,$... or length lower then 9 chars')
        return redirect(url_for("auth.signup"))
    else:
        #generate activation code and send it by email
        try:
            if not disable_email:
                activation_code=send_email(recipient=email)     #send email
            else:
                activation_code=code_generator()                #generate code without sending email

        except:
            flash("Error sending email to new user!Please send internet connection!")
            return render_template("error_page.html")
        #generate timestamp for activation code
        activation_code_timestamp=create_timestamp()


        #generate username from the input email address by cutting @domain.com
        username=cpd.extract_email_user(email)

        #check if username exists in database
        filter_username=credentials.query.filter_by(api_user=username).first()
        if filter_username:
            new_username=username + "_" + cpd.extract_email_domain(email)#if exists append _domain
        else:
            new_username=username


        #write user to database
        new_user=credentials(email=email, password=generate_password_hash(password,method="sha256"),api_user=new_username,active=False,
        activation_code=activation_code,code_timestamp=activation_code_timestamp, code_retries=0)

        db.session.add(new_user)
        db.session.commit()

        if not disable_email:
            flash(f"An activation code was sent to your email with {int(ACTIVATION_CODE_LIFETIME/3600)} hours lifetime.\nActivate your profile! ")
        else:
            flash(f"Profile created succesfully! Emailing disabled so no activation code was sent!")

        return redirect(url_for('main.login'))


###########################################################################################################################
################################################### CHANGE PASSWORD #######################################################
###########################################################################################################################
@login_required
@auth_blueprint.route('/change-password', methods=['GET'])
def change_password():
    return render_template('/change-password.html',email=current_user.email)

@login_required
@auth_blueprint.route('/change-password',methods=['POST'])
def change_password_post():
    old_password=request.form.get('old_password')
    new_password=request.form.get('new_password')
    confirm_new_password=request.form.get('confirm_new_password')

    pwv=Password_verify(new_password)

    if not check_password_hash(current_user.password,old_password):
        flash('Old password is not correct')
        return redirect(url_for('auth.change_password'))

    if new_password!=confirm_new_password:
        flash('Password and confirm password not identical')
        return redirect(url_for("auth.change_password"))
    if not(pwv.check_password_has_lower() and pwv.check_password_has_upper() \
        and pwv.check_password_has_special() and pwv.check_password_lenght()):
        flash('Password missing uppercase, lowercase, 1,2,.. !,#,$... or length lower then 9 chars')
        return redirect(url_for("auth.change_password"))
    else:
        current_user.password=generate_password_hash(new_password,method="sha256")
        db.session.commit()
        flash('Password was successfully changed')
        logout_user()
        return redirect(url_for('main.login'))




###########################################################################################################################
################################################# PASSWORD RECOVERY #######################################################
###########################################################################################################################
@main_blueprint.route('/recovery', methods=['GET'])
def recovery():
    return render_template('/recovery.html')

@main_blueprint.route('/recovery', methods=['POST'])
def recovery_post():

    #check if "send email" is active by reading the database
    param_email_status=parameters.query.filter_by(parameter_name='disable_email_send').first()
    disable_email=param_email_status.bool_value

    #read variables from the html form
    email=request.form.get('email')
    code=request.form.get('code')
    password=request.form.get('password')
    confirm_password=request.form.get('confirm_password')

    user=credentials.query.filter_by(email=email).first()
    pwv=Password_verify(password)

    if request.form['action']=='send_code':
        if len(email)>5 and user:

            if not disable_email:
            #generate activation code and send it by email
                activation_code=send_email(recipient=user.email)
            else:
            #generate activation code without emailing
                activation_code=code_generator()

            #write activation code to db
            user.activation_code=activation_code
            db.session.commit()
            flash('A confirmation code was sent to you email!\nPlease fill it in in order to set a new password')
            return redirect(url_for('main.recovery',email=email))
        else:
            flash('Invalid email address or email not found')
            return redirect(url_for('main.recovery'))

    elif request.form['action']=='recover_password':

        if not user or len(email)<=5:
            flash('Invalid email address or email not found')
            return redirect(url_for('main.recovery'))
        elif code!=user.activation_code and len(code)!=8:
            flash('Invalid confirmation code')
            return redirect(url_for('main.recovery'))
        elif password!=confirm_password:
            flash('Password and confirm password not identical')
            return redirect(url_for('main.recovery'))
        elif not(pwv.check_password_has_lower() and pwv.check_password_has_upper() \
            and pwv.check_password_has_special() and pwv.check_password_lenght()):
            flash('Password missing uppercase, lowercase, 1,2,.. !,#,$... or length lower then 9 chars')
            return redirect(url_for("main.recovery"))
        else:
            user.password=generate_password_hash(password,method="sha256")
            user.activation_code=''
            db.session.commit()
            flash('Password recovered successfuly')
            return redirect(url_for("main.login"))
    else:
        flash('Invalid variable name in html')
        return redirect(url_for("main.recovery"))



###########################################################################################################################
##################################################### ACTIVATION ##########################################################
###########################################################################################################################
try:
    @auth_blueprint.route('/activation', methods=['GET'])
    def activation():
        if current_user.is_authenticated:
            return render_template('activation.html')
        else:
            return render_template('index.html')
except AttributeError:
    pass


@auth_blueprint.route('/activation', methods=['POST'])
def activation_post():

    #check if "send email" is active by reading the database
    param_email_status=parameters.query.filter_by(parameter_name='disable_email_send').first()
    disable_email=param_email_status.bool_value

    #read variables from the html form
    input_activation=request.form.get('activation-code')
    input_password=request.form.get('password')

    if check_password_hash(current_user.password,input_password):
        if  current_user.activation_code==input_activation:


            if current_user.code_retries<=ACTIVATION_CODE_RETRIES:
                datetime_now=datetime.now()
                #if activation code is not too old
                if int(datetime_now.timestamp())-int(current_user.code_timestamp.timestamp())<=ACTIVATION_CODE_LIFETIME:
                    current_user.active=True                    #activate user
                    current_user.activation_code=''             #delete activation code from database
                    current_user.code_timestamp=datetime_now    #write activation timestamp to db
                    current_user.code_retries=0                 #reset retries in db
                    current_user.api_key=api_weather.generate_api_key()
                    db.session.commit()
                    flash("Congratulationes!\nYour account is active")
                    return redirect(url_for('auth.profile'))
                else:
                    if not disable_email:
                    #generate activation code and send it by email
                        activation_code=send_email(recipient=current_user.email)
                    else:
                    #generate activation code without sending email
                        activation_code=code_generator()

                    #generate timestamp for activation code
                    activation_code_timestamp=create_timestamp()

                    #write to database
                    current_user.activation_code=activation_code
                    current_user.code_timestamp=activation_code_timestamp
                    current_user.code_retries=0
                    db.session.commit()
                    flash('Activation code expired!\nA new activation code was sent to your email address!')
                    return redirect(url_for('auth.activation'))

            else:
                #generate activation code and send it by email
                activation_code=send_email(recipient=current_user.email)
                #generate timestamp for activation code
                activation_code_timestamp=create_timestamp()
                current_user.activation_code=activation_code
                current_user.code_timestamp=activation_code_timestamp
                current_user.code_retries=0
                db.commit()
                flash('Too many activation code retries!\nA new activation code was sent to your email address!')
                return redirect(url_for('auth.activation'))


        else:
            current_user.code_retries+=1
            db.session.commit()
            flash(f'Invalid activation code.You still have {ACTIVATION_CODE_RETRIES-current_user.code_retries} retries left ')
            datetime_now=datetime.now()
            return redirect(url_for('auth.activation'))

    else:
        flash(f'Invalid password')
        return redirect(url_for('auth.activation'))


###########################################################################################################################
####################################################### LOGIN #############################################################
###########################################################################################################################
@main_blueprint.route('/login')
def login():
    return render_template('login.html')

@main_blueprint.route('/login',methods=['POST'])
def login_post():
    input_email=request.form.get('email')
    input_password=request.form.get('password')
    remember=True if request.form.get('remember') else False

    user=credentials.query.filter_by(email=input_email.lower()).first()

    if user and check_password_hash(user.password,input_password):
        login_user(user,remember=remember,duration=timedelta(hours=10)) #remember time if remember is checked
        if current_user.id==1:
            return redirect(url_for('main.index'))
        else:
            return redirect(url_for('auth.profile'))

    else:
        flash('Invalid credentials')
        return redirect(url_for('main.login'))


###########################################################################################################################
###################################################### LOGOUT #############################################################
###########################################################################################################################
@auth_blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


###########################################################################################################################
###################################################### PROFILE ############################################################
###########################################################################################################################
try:
    cpd=Check_profile_data()

    length=len([c for c in countries.countries])
    country_list=[c for c in countries.countries]

    @auth_blueprint.route('/profile', methods=['GET'])
    @login_required
    def profile():

        return render_template('profile.html', email=current_user.email, active='Yes' if current_user.active==True else 'No',\
        name=current_user.name,api_user=current_user.api_user,api_key=current_user.api_key,firstname=current_user.firstname,\
        birthdate=current_user.birthdate, country=current_user.country,country_list=country_list,city=current_user.city,\
        address=current_user.address,latitude=current_user.latitude, longitude=current_user.longitude,length=length )



    @auth_blueprint.route('/profile',methods=['POST'])
    @login_required
    def profile_post():

        #update database with data from the form
        if request.form['action']=='update':
            name=request.form.get('name')
            firstname=request.form.get('firstname')
            birthdate=request.form.get('birthdate')
            country=request.form.get('country')
            city=request.form.get('city')
            address=request.form.get('address')

            #calculate gps coordinates based on address
            if request.form.get('country')!='' and request.form.get('city')!='' and request.form.get('address')!='' and\
            request.form.get('country')!=None and request.form.get('city')!=None and request.form.get('address')!=None:
                gps_location=GPS_location(f"{request.form.get('country')}, {request.form.get('city')}, {request.form.get('address')}")
                if gps_location!=None:
                    current_user.latitude=round(gps_location[0],2)
                    current_user.longitude=round(gps_location[1],2)
                else:
                    flash('Gps location cannot be calculated! Check address!')
                    return redirect(url_for('auth.profile'))
            else:

                flash('Country,city or address field is empty!')
                return redirect(url_for('auth.profile'))

            if cpd.check_chars_in_name(name) and cpd.check_chars_in_name(firstname) :
                current_user.name=cpd.check_if_title(name)
                current_user.firstname=cpd.check_if_title(firstname)
                current_user.birthdate=birthdate
                current_user.country=country
                current_user.city=city
                current_user.address=address

                db.session.commit()

                flash('Profile updated sucessfully')
                return redirect(url_for('auth.profile'))
            else:
                flash('Name or firstname contains invalid characters!')
                return redirect(url_for('auth.profile'))

        if request.form['action']=='renew_api_key':
            current_user.api_key=api_weather.generate_api_key()
            db.session.commit()
            flash('API KEY was renewed!')
            return redirect(url_for('auth.profile'))

except Exception as exception:
    print(exception)



###########################################################################################################################
################################################## ADMINISTRATOR ##########################################################
###########################################################################################################################
@auth_blueprint.route('/administrator')
@login_required
def administrator():
    param=parameters.query.all()
    if param[0].parameter_name=="disable_email_send":
        email_disabled='checked' if param[0].bool_value else ''



    user_list=list()
    users=credentials.query.all()
    for user in users:
        user_list.append({'email':user.email,'status':user.active,'name':user.name,'firstname':user.firstname,
        'birthdate':user.birthdate,'country':user.country,'city':user.city, 'address':user.address,'activation_code':user.activation_code,'api_key':user.api_key})
    return render_template('administrator.html',user_list=user_list,length=len(user_list),email_disabled=email_disabled)


@auth_blueprint.route('/administrator',methods=['POST'])
def administrator_post():

    if request.form['action']=='email-change':
        email_disabled=request.form.get('disable-email')
        print(email_disabled)


    if request.form['action']=='download':
        user_list=list()
        users=credentials.query.all()

        for user in users:
            user_list.append([user.email,user.active,user.name,user.firstname,
            user.birthdate,user.country, user.city, user.address,user.api_key])

        csv_header=['Email','Active','Name','Firstname','Birthdate','Country','City','Address','Api_key']

        #Wrap csv file
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(csv_header)
        writer.writerows(user_list[1:])
        buff = io.BytesIO(buffer.getvalue().encode('utf-8'))
        w = FileWrapper(buff)
        return Response(w, mimetype="text/csv", direct_passthrough=True)

    else:
        selected_email=request.form['action']
        selected_user=credentials.query.filter_by(email=selected_email).first()
        db.session.delete(selected_user)
        db.session.commit()

        return redirect(url_for('auth.administrator'))


###########################################################################################################################
##################################################### MAP #################################################################
###########################################################################################################################
@auth_blueprint.route('/map')
def map():
    return render_template('map.html')

###########################################################################################################################
################################################### WEATHER ###############################################################
###########################################################################################################################
@auth_blueprint.route('/weather', methods=['GET'])
@login_required
def weather():
    if current_user.country!='' and current_user.city!='' and current_user.address!='' and current_user.name!='' and current_user.firstname!='':

        #Prepare weather to be displayed on weather.html
        actual_weather=api_weather.get_actual_weather(current_user.latitude,current_user.longitude)
        print(actual_weather)
        #Draw map.html
        actual_map=DrawMap(current_user.country,current_user.city,current_user.address, current_user.name,current_user.firstname, \
            actual_weather["weathercode"])

        #generate html code for the map
        html_string=actual_map.get_root().render()


        weather_message=api_weather.return_weather_message(current_user.city,current_user.country, current_user.latitude,\
                    current_user.longitude,actual_weather)

    return render_template('weather.html',weather=weather_message,map=html_string)


###########################################################################################################################
###################################################### API ################################################################
###########################################################################################################################
@app.route('/api/weather', methods=['GET'])
def return_weather():
    args=request.args
    headers=request.headers

    api_user=args.get('user',type=str)
    authorization=headers.get('Authorization',type=str)

    current_user=credentials.query.filter_by(api_user=api_user).first()

    if current_user:
        if current_user.api_key==authorization:
            if current_user.city!=None and current_user.country!=None and current_user.latitude!=None and current_user.longitude!=None:
                actual_weather=api_weather.get_actual_weather(current_user.latitude,current_user.longitude)
                weather_message=api_weather.return_weather_message(current_user.city,current_user.country, current_user.latitude,\
                    current_user.longitude,actual_weather)

                api_message={'weather':weather_message}
                return jsonify(api_message)
            else:
                msg={'error':'country or city  not filled in by user'}
                return msg
        else:
                msg={'error':'invalid key'}
                return msg
    else:
        msg={'error':'invalid user'}
        return jsonify(msg)

#########################################################################################################################
#########################################################################################################################
#########################################################################################################################




@app.route("/gps", methods=['POST'])
def gps():
    req=request.get_json()
    #read json values for country, city, address
    country=req['country']
    city=req['city']
    address=req['address']

    if country!='' and city!='' and address!='' and country!=None and city!=None and address!=None:
        gps_location=GPS_location(f"{country}, {city}, {address}")

        if gps_location!=None:
            coordinate={'latitude':round(gps_location[0],2),
                        'longitude':round(gps_location[1],2)}

            res=make_response(jsonify(coordinate,200))
            return res

        else:
            res=make_response(jsonify({'message':'error transforming gps location'},200))
            return res


#disable emailing at signup
@app.route("/admin_disable_email", methods=['POST'])
def change_status_send_email():
    req=request.get_json()
    #read send email status from browser
    status=req['email_status']
    param_email_status=parameters.query.filter_by(parameter_name='disable_email_send').first()
    param_email_status.bool_value=status
    db.session.commit()
    return make_response(jsonify({'message':'email status changed'},200))


#blueprint for auth routes
app.register_blueprint(auth_blueprint)

#blueprint for main routes
app.register_blueprint(main_blueprint)


# if(__name__)=="__main__":
#     app.run()





