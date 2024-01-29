import codecs
import datetime
import json
import os
from flask_sqlalchemy import SQLAlchemy  # Create DB with Flask
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_file  # Package for Routing
from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime, Float, or_, \
    BigInteger  # DB Column Datatype
from sqlalchemy.orm import relationship, backref  # Create DB Relationship
from sqlalchemy.orm.exc import DetachedInstanceError  # DB Session lock error
import math
import csv
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user  # Login Module
from functools import wraps
from flask import abort
from werkzeug.security import generate_password_hash, check_password_hash
from forms import *
import random
from functions import FR, N1, N2, N4, N5_in, N6_lbhr_psi_lbft3, N7_60_scfh_psi_F, N8_kghr_bar_K, N9_O_m3hr_kPa_C, REv, conver_FR_noise, full_format, getFlowCharacter, getValveType, meta_convert_P_T_FR_L, project_status_list, notes_dict_reorder, purpose_list, units_dict, actuator_data_dict, valve_force_dict
from gas_noise_formulae import lpae_1m
from gas_velocity_iec import getGasVelocities
from liquid_noise_formulae import Lpe1m
from sqlalchemy.sql.sqltypes import String, VARCHAR, FLOAT, INTEGER
from jinja2 import Environment, FileSystemLoader

from specsheet import createSpecSheet

# -----------^^^^^^^^^^^^^^----------------- IMPORT STATEMENTS -----------------^^^^^^^^^^^^^------------ #

# env = Environment(loader=FileSystemLoader('templates\\render_data.html'))
# env.globals['getattr'] = getattr


def getRowsFromCsvFile(file_path):
    filename = file_path
    fields_afr = []
    rows_afr = []

    # reading csv file
    with open(filename, 'r', encoding='utf-8-sig') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)

        # extracting field names through first row
        fields_afr = next(csvreader)

        # extracting each data row one by one
        for row in csvreader:
            dict_add = {}
            for i in range(len(fields_afr)):
                dict_add[fields_afr[i]] = row[i]
            rows_afr.append(dict_add)

    return rows_afr

### --------------------------------- APP CONFIGURATION -----------------------------------------------------###

# app configuration
app = Flask(__name__)

app.config['SECRET_KEY'] = "kkkkk"
Bootstrap(app)

# # CONNECT TO DB
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///fcc-db-v6-0.db"

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1", "sqlite:///fcc-db-v6-0.db")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# creating login manager
login_manager = LoginManager()
login_manager.init_app(app)


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        admin = userMaster.query.all()
        admin_id = []
        for i in admin:
            id_ = i.id
            admin_id.append(id_)

        if current_user.id not in admin_id:
            return abort(403)
        # Otherwise, continue with the route function
        return f(*args, **kwargs)

    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return userMaster.query.get(int(user_id))


### --------------------------------- CREATE TABLE IN DB -----------------------------------------------------###


# CREATE TABLES

#
class userMaster(UserMixin, db.Model):
    __tablename__ = "userMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'confirm_deleted_rows': False
    }

    id = Column(Integer, primary_key=True)
    name = Column(String(1000))
    password = Column(String(100))
    employeeId = Column(String(100))
    email = Column(String(100), unique=True)
    mobile = Column(String(100))
    fccUser = Column(Boolean)

    # relationships
    # TODO 1 - Project Master
    project = relationship("projectMaster", cascade="all,delete", back_populates="user")

    # relationship as child
    departmentId = Column(Integer, ForeignKey("departmentMaster.id"))
    department = relationship("departmentMaster", back_populates="user")

    designationId = Column(Integer, ForeignKey("designationMaster.id"))
    designation = relationship("designationMaster", back_populates="user")


class companyMaster(db.Model):
    __tablename__ = "companyMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'company',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    description = Column(String(300))

    # relationship as parent
    address = relationship('addressMaster', cascade="all,delete",  back_populates='company')


class departmentMaster(db.Model):
    __tablename__ = "departmentMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'department',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    user = relationship("userMaster", cascade="all,delete", back_populates="department")


class designationMaster(db.Model):
    __tablename__ = "designationMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'deisgnation',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    user = relationship("userMaster", cascade="all,delete", back_populates="designation")


# data upload done
class industryMaster(db.Model):
    __tablename__ = "industryMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'industry',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    # relationship as parent
    project = relationship("projectMaster", cascade="all,delete", back_populates="industry")


# data upload done
class regionMaster(db.Model):
    __tablename__ = "regionMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'region',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    # relationship as parent
    project = relationship("projectMaster", cascade="all,delete", back_populates="region")


class addressMaster(db.Model):
    __tablename__ = "addressMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'address',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    address = Column(String(300))
    customerCode = Column(String(15))  # to add as A001 to A999 and B001 to B999 and so on.
    isActive = Column(Boolean)

    # relationship as parent
    # projectCompany = relationship('projectMaster',uselist=False, backref='address_company')
    # projectEnduser = relationship('projectMaster',uselist=False, backref='address_enduser')
    address_project = relationship('addressProject', cascade="all,delete", back_populates='address')

    # relationship as child
    companyId = Column(Integer, ForeignKey("companyMaster.id"))
    company = relationship("companyMaster", back_populates="address")


class addressProject(db.Model):
    __tablename__ = "addressProject"

    __mapper_args__ = {
        'polymorphic_identity': 'addressP',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    isCompany = Column(Boolean)

    # child to address
    addressId = Column(Integer, ForeignKey("addressMaster.id"))
    address = relationship("addressMaster", back_populates="address_project")

    # child to project
    projectId = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="project_address")


class engineerProject(db.Model):
    __tablename__ = "engineerProject"

    __mapper_args__ = {
        'polymorphic_identity': 'engineerP',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    isApplication = Column(Boolean)

    # child to address
    engineerId = Column(Integer, ForeignKey("engineerMaster.id"))
    engineer = relationship("engineerMaster", back_populates="engineer_project")

    # child to project
    projectId = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="project_engineer")


class engineerMaster(db.Model):
    __tablename__ = "engineerMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'engineer',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    designation = Column(String(300))

    # relationship as parent
    engineer_project = relationship('engineerProject', cascade="all,delete", back_populates='engineer')
    # projectContract = relationship("projectMaster",uselist=False, backref="engineer_contract")
    # projectApplicaton = relationship("projectMaster",uselist=False, backref="engineer_application")


class projectMaster(db.Model):
    __tablename__ = "projectMaster"

    __mapper_args__ = {
        'polymorphic_identity': 'project',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    projectId = Column(String(100))
    projectRef = Column(String(100))
    enquiryRef = Column(String(100))
    enquiryReceivedDate = Column(DateTime)
    receiptDate = Column(DateTime)
    bidDueDate = Column(DateTime)
    purpose = Column(String(100))
    custPoNo = Column(String(100))
    workOderNo = Column(String(100))
    revisionNo = Column(Integer)
    status = Column(String(100))
    pressureUnit = Column(String(50))
    flowrateUnit = Column(String(50))
    temperatureUnit = Column(String(50))
    lengthUnit = Column(String(50))
    # relationship as parent
    item = relationship("itemMaster", cascade="all,delete", back_populates="project")
    projectnotes = relationship('projectNotes', cascade="all,delete", back_populates='project')
    project_address = relationship('addressProject', cascade="all,delete", back_populates='project')
    project_engineer = relationship('engineerProject', cascade="all,delete", back_populates='project')

    # relationship as child
    # TODO - User
    createdById = Column(Integer, ForeignKey("userMaster.id"))
    user = relationship("userMaster", back_populates="project")
    # TODO - Industry
    IndustryId = Column(Integer, ForeignKey("industryMaster.id"))
    industry = relationship("industryMaster", back_populates="project")
    # TODO - Engineer contract
    regionID = Column(Integer, ForeignKey("regionMaster.id"))
    region = relationship("regionMaster", back_populates="project")

    # TODO - Address

    # def update(self, **kwargs):
    #     for key, value in kwargs.items():
    #         print(key, value)
    #         setattr(self, key, value)
    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = projectMaster.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            print(key)
            print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()


class projectNotes(db.Model):
    __tablename__ = "projectNotes"
    __mapper_args__ = {
        'polymorphic_identity': 'projectNote',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    notesNumber = Column(String(300))
    notes = Column(String(300))
    date = Column(DateTime)

    # relationship as child
    projectId = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="projectnotes")


class itemNotesData(db.Model):
    __tablename__ = "itemNotesData"
    __mapper_args__ = {
        'polymorphic_identity': 'itemNote',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    content = Column(String(300))
    notesNumber = Column(String(300))

    # rel as child to item
    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship('itemMaster', back_populates='notes')


class notesMaster(db.Model):
    __tablename__ = "notesMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'note',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    notesNumber = Column(String(10))
    content = Column(String(300))


class itemMaster(db.Model):
    __tablename__ = "itemMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'item',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    itemNumber = Column(Integer)
    alternate = Column(String(50))

    # rel as parent
    case = relationship("caseMaster", cascade="all,delete", back_populates="item")

    # one-to-one relationship with valve, actuator and accessories, as parent
    valve = relationship("valveDetailsMaster", cascade="all,delete", back_populates="item")
    actuator = relationship("actuatorMaster", cascade="all,delete", back_populates="item")
    accessories = relationship("accessoriesData", cascade="all,delete", back_populates="item")
    notes = relationship("itemNotesData", cascade="all,delete", back_populates="item")

    # relationship as child
    projectID = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="item")


# data upload done
class fluidState(db.Model):
    __tablename__ = "fluidState"
    __mapper_args__ = {
        'polymorphic_identity': 'state',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', cascade="all,delete", back_populates='state')


# data upload done
class designStandard(db.Model):
    __tablename__ = "designStandard"
    __mapper_args__ = {
        'polymorphic_identity': 'standard',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', cascade="all,delete", back_populates='design')


# data upload done
class valveStyle(db.Model):
    __tablename__ = "valveStyle"
    __mapper_args__ = {
        'polymorphic_identity': 'style',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', cascade="all,delete", back_populates='style')
    cv = relationship('cvTable', cascade="all,delete", back_populates='style')
    shaft_ = relationship('shaft', cascade="all,delete", back_populates='style')
    disc_ = relationship('disc', cascade="all,delete", back_populates='style')
    seat_ = relationship('seat', cascade="all,delete", back_populates='style')
    packing_ = relationship('packing', cascade="all,delete", back_populates='style')
    trimtype_ = relationship('trimType', cascade="all,delete", back_populates='style')


# data upload done
class applicationMaster(db.Model):
    __tablename__ = "applicationMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'application',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


# data upload done
class ratingMaster(db.Model):
    __tablename__ = "ratingMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'rating',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', cascade="all,delete", back_populates='rating')
    pt = relationship('pressureTempRating', cascade="all,delete", back_populates='rating')
    cv = relationship('cvTable', cascade="all,delete", back_populates='rating_c')
    packingF = relationship('packingFriction', cascade="all,delete", back_populates='rating')
    torque = relationship("packingTorque", cascade="all,delete", back_populates='rating')


# data upload done
class materialMaster(db.Model):
    __tablename__ = "materialMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'material',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', cascade="all,delete", back_populates='material')
    pt = relationship('pressureTempRating', cascade="all,delete", back_populates='material')


# data upload done
class pressureTempRating(db.Model):
    __tablename__ = "pressureTempRating"
    __mapper_args__ = {
        'polymorphic_identity': 'pressureTemp',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    maxTemp = Column(Float)
    minTemp = Column(Float)
    pressure = Column(Float)

    # relationship as child
    materialId = Column(Integer, ForeignKey("materialMaster.id"))
    material = relationship("materialMaster", back_populates="pt")

    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship("ratingMaster", back_populates="pt")


# Multiple static dropdown


class endConnection(db.Model):
    __tablename__ = "endConnection"
    __mapper_args__ = {
        'polymorphic_identity': 'endC',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    endConnection_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='endConnection__')


# 19
class endFinish(db.Model):
    __tablename__ = "endFinish"
    __mapper_args__ = {
        'polymorphic_identity': 'endF',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    endFinish_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='endFinish__')


# 20
class bonnetType(db.Model):
    __tablename__ = "bonnetType"
    __mapper_args__ = {
        'polymorphic_identity': 'bonnetTyp',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    bonnetType_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='bonnetType__')


# 21
class packingType(db.Model):
    __tablename__ = "packingType"
    __mapper_args__ = {
        'polymorphic_identity': 'packingTyp',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    packingType_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='packingType__')


class trimType(db.Model):
    __tablename__ = "trimType"
    __mapper_args__ = {
        'polymorphic_identity': 'trim',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    trimType_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='trimType__')
    trimType_c = relationship('cvTable', cascade="all,delete", back_populates='trimType_')
    seatLoad = relationship('seatLoadForce', cascade="all,delete", back_populates='trimType_')
    kn = relationship("knValue", cascade="all,delete", back_populates="trimType_")

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='trimtype_')


class flowCharacter(db.Model):  # TODO - Paandi  ............Done
    __tablename__ = "flowCharacter"
    __mapper_args__ = {
        'polymorphic_identity': 'flowC',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    flowCharacter_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='flowCharacter__')
    flowCharacter_c = relationship('cvTable', cascade="all,delete", back_populates='flowCharacter_')
    kn = relationship('knValue', cascade="all,delete", back_populates='flowCharacter_')


# 23
class flowDirection(db.Model):  # TODO - Paandi  ............Done
    __tablename__ = "flowDirection"
    __mapper_args__ = {
        'polymorphic_identity': 'flowD',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    flowDirection_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='flowDirection__')
    flowDirection_c = relationship('cvTable', cascade="all,delete", back_populates='flowDirection_')
    kn = relationship('knValue', cascade="all,delete", back_populates='flowDirection_')


# 24
class seatLeakageClass(db.Model):  # TODO - Paandi    ..........Done
    __tablename__ = "seatLeakageClass"
    __mapper_args__ = {
        'polymorphic_identity': 'leakage',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    seatLeakageClass_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='seatLeakageClass__')
    seatLoad = relationship('seatLoadForce', cascade="all,delete", back_populates='leakage')


# 25
class bonnet(db.Model):
    __tablename__ = "bonnet"
    __mapper_args__ = {
        'polymorphic_identity': 'bonne',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    bonnet_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='bonnet__')


class nde1(db.Model):
    __tablename__ = "nde1"
    __mapper_args__ = {
        'polymorphic_identity': 'nde',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    nde1_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='nde1__')


class nde2(db.Model):
    __tablename__ = "nde2"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    nde2_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='nde2__')


class shaft(db.Model):  # Stem in globe
    __tablename__ = "shaft"
    __mapper_args__ = {
        'polymorphic_identity': 'shaf',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    yield_strength = Column(Float)

    shaft_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='shaft__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='shaft_')


class disc(db.Model):  # plug in globe
    __tablename__ = "disc"
    __mapper_args__ = {
        'polymorphic_identity': 'dis',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    disc_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='disc__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='disc_')


class seat(db.Model):  # both seat
    __tablename__ = "seat"
    __mapper_args__ = {
        'polymorphic_identity': 'sea',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    seat_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='seat__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='seat_')


class packing(db.Model):
    __tablename__ = "packing"
    __mapper_args__ = {
        'polymorphic_identity': 'pack',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    packing_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='packing__')
    packingF = relationship('packingFriction', cascade="all,delete", back_populates='packing_')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='packing_')


class balanceSeal(db.Model):  # NDE  # TODO - Paandi
    __tablename__ = "balanceSeal"
    __mapper_args__ = {
        'polymorphic_identity': 'balanceSel',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    balanceSeal_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='balanceSeal__')


class studNut(db.Model):  # NDE  # TODO - Paandi
    __tablename__ = "studNut"
    __mapper_args__ = {
        'polymorphic_identity': 'stud',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    studNut_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='studNut__')


class gasket(db.Model):
    __tablename__ = "gasket"
    __mapper_args__ = {
        'polymorphic_identity': 'gas',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    gasket_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='gasket__')


class cageClamp(db.Model):
    __tablename__ = "cageClamp"
    __mapper_args__ = {
        'polymorphic_identity': 'cage',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    cage_ = relationship('valveDetailsMaster', cascade="all,delete", back_populates='cage__')


# To cv table
class balancing(db.Model):
    __tablename__ = "balancing"
    __mapper_args__ = {
        'polymorphic_identity': 'balance',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    balancing_c = relationship('cvTable', cascade="all,delete", back_populates='balancing_')


# TODO dropdowns end

class valveDetailsMaster(db.Model):
    __tablename__ = "valveDetailsMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'valveData',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    quantity = Column(Integer)
    tagNumber = Column(String(50))
    serialNumber = Column(String(50))
    shutOffDelP = Column(Float)
    maxPressure = Column(Float)
    maxTemp = Column(Float)
    minTemp = Column(Float)
    shutOffDelPUnit = Column(String(50))
    maxPressureUnit = Column(String(50))
    maxTempUnit = Column(String(50))
    minTempUnit = Column(String(50))
    bonnetExtDimension = Column(Float)
    application = Column(String(150))

    # one-to-one relationship with itemMaser
    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship("itemMaster", back_populates="valve")

    # rel as child individual
    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship("ratingMaster", back_populates="valve")

    materialId = Column(Integer, ForeignKey("materialMaster.id"))
    material = relationship("materialMaster", back_populates="valve")

    designStandardId = Column(Integer, ForeignKey("designStandard.id"))
    design = relationship("designStandard", back_populates="valve")

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship("valveStyle", back_populates="valve")

    fluidStateId = Column(Integer, ForeignKey("fluidState.id"))
    state = relationship("fluidState", back_populates="valve")

    # rel as child dropdown
    endConnectionId = Column(Integer, ForeignKey("endConnection.id"))
    endConnection__ = relationship('endConnection', back_populates='endConnection_')

    endFinishId = Column(Integer, ForeignKey("endFinish.id"))
    endFinish__ = relationship('endFinish', back_populates='endFinish_')

    bonnetTypeId = Column(Integer, ForeignKey("bonnetType.id"))
    bonnetType__ = relationship('bonnetType', back_populates='bonnetType_')

    packingTypeId = Column(Integer, ForeignKey("packingType.id"))
    packingType__ = relationship('packingType', back_populates='packingType_')

    trimTypeId = Column(Integer, ForeignKey("trimType.id"))
    trimType__ = relationship('trimType', back_populates='trimType_')

    flowCharacterId = Column(Integer, ForeignKey("flowCharacter.id"))
    flowCharacter__ = relationship('flowCharacter', back_populates='flowCharacter_')

    flowDirectionId = Column(Integer, ForeignKey("flowDirection.id"))
    flowDirection__ = relationship('flowDirection', back_populates='flowDirection_')

    seatLeakageClassId = Column(Integer, ForeignKey("seatLeakageClass.id"))
    seatLeakageClass__ = relationship('seatLeakageClass', back_populates='seatLeakageClass_')

    bonnetId = Column(Integer, ForeignKey("bonnet.id"))
    bonnet__ = relationship('bonnet', back_populates='bonnet_')

    nde1Id = Column(Integer, ForeignKey("nde1.id"))
    nde1__ = relationship('nde1', back_populates='nde1_')

    nde2Id = Column(Integer, ForeignKey("nde2.id"))
    nde2__ = relationship('nde2', back_populates='nde2_')

    shaftId = Column(Integer, ForeignKey("shaft.id"))
    shaft__ = relationship('shaft', back_populates='shaft_')

    discId = Column(Integer, ForeignKey("disc.id"))
    disc__ = relationship('disc', back_populates='disc_')

    seatId = Column(Integer, ForeignKey("seat.id"))
    seat__ = relationship('seat', back_populates='seat_')

    packingId = Column(Integer, ForeignKey("packing.id"))
    packing__ = relationship('packing', back_populates='packing_')

    balanceSealId = Column(Integer, ForeignKey("balanceSeal.id"))
    balanceSeal__ = relationship('balanceSeal', back_populates='balanceSeal_')

    studNutId = Column(Integer, ForeignKey("studNut.id"))
    studNut__ = relationship('studNut', back_populates='studNut_')

    gasketId = Column(Integer, ForeignKey("gasket.id"))
    gasket__ = relationship('gasket', back_populates='gasket_')

    cageId = Column(Integer, ForeignKey("cageClamp.id"))
    cage__ = relationship('cageClamp', back_populates='cage_')

    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = valveDetailsMaster.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            # print(key)
            # print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()


class pipeArea(db.Model):
    __tablename__ = "pipeArea"
    __mapper_args__ = {
        'polymorphic_identity': 'pipeAre',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    nominalDia = Column(Float)
    nominalPipeSize = Column(Float)
    outerDia = Column(Float)
    thickness = Column(Float)
    area = Column(Float)
    schedule = Column(String(50))

    # rel as parent
    caseI = relationship("caseMaster", cascade="all,delete", back_populates="iPipe")
    # caseO = relationship("caseMaster", back_populates="oPipe")


class cvTable(db.Model):
    __tablename__ = "cvTable"
    __mapper_args__ = {
        'polymorphic_identity': 'cvT',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    # valveStyleId = Column(Integer)
    valveSize = Column(Float)
    series = Column(String(50))

    # rel as parent
    value = relationship("cvValues", cascade="all,delete", back_populates="cv")
    case = relationship("caseMaster", cascade="all,delete", back_populates="cv")
    torque = relationship("packingTorque", cascade="all,delete", back_populates="cv")

    # rel as child

    trimTypeId = Column(Integer, ForeignKey("trimType.id"))
    trimType_ = relationship('trimType', back_populates='trimType_c')

    flowCharacId = Column(Integer, ForeignKey("flowCharacter.id"))
    flowCharacter_ = relationship('flowCharacter', back_populates='flowCharacter_c')

    flowDirId = Column(Integer, ForeignKey("flowDirection.id"))
    flowDirection_ = relationship('flowDirection', back_populates='flowDirection_c')

    balancingId = Column(Integer, ForeignKey("balancing.id"))
    balancing_ = relationship('balancing', back_populates='balancing_c')

    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating_c = relationship('ratingMaster', back_populates='cv')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='cv')


class cvValues(db.Model):
    __tablename__ = "cvValues"
    __mapper_args__ = {
        'polymorphic_identity': 'cvV',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    coeff = Column(String(50))
    one = Column(Float)
    two = Column(Float)
    three = Column(Float)
    four = Column(Float)
    five = Column(Float)
    six = Column(Float)
    seven = Column(Float)
    eight = Column(Float)
    nine = Column(Float)
    ten = Column(Float)

    seatBore = Column(Float)  # taken as discDia for butterfly
    travel = Column(Float)  # taken as rotation for butterfly

    # rel as child
    cvId = Column(Integer, ForeignKey("cvTable.id"))
    cv = relationship('cvTable', back_populates='value')


class fluidProperties(db.Model):
    __tablename__ = "fluidProperties"
    __mapper_args__ = {
        'polymorphic_identity': 'fluidP',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    fluidState = Column(String(100))
    fluidName = Column(String(100))
    specificGravity = Column(Float)
    vaporPressure = Column(Float)
    viscosity = Column(Float)
    criticalPressure = Column(Float)
    molecularWeight = Column(Float)
    specificHeatRatio = Column(Float)
    compressibilityFactor = Column(Float)

    # rel as parent
    case = relationship("caseMaster", cascade="all,delete", back_populates="fluid")


class caseMaster(db.Model):
    __tablename__ = "caseMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'case',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    flowrate = Column(Float)
    inletPressure = Column(Float)
    outletPressure = Column(Float)
    inletTemp = Column(Float)
    vaporPressure = Column(Float)
    specificGravity = Column(Float)
    kinematicViscosity = Column(Float)
    fl = Column(Float)
    calculatedCv = Column(Float)
    openingPercentage = Column(Float)
    chokedDrop = Column(Float)
    Ff = Column(Float)
    Fp = Column(Float)
    Flp = Column(Float)
    kc = Column(Float)
    ar = Column(Float)
    spl = Column(Float)
    reNumber = Column(Float)
    pipeInVel = Column(Float)
    pipeOutVel = Column(Float)
    valveVel = Column(Float)
    tex = Column(Float)
    powerLevel = Column(Float)
    requiredStages = Column(Float)
    specificHeatRatio = Column(Float)
    mw_sg = Column(String(50))
    molecularWeight = Column(Float)
    compressibility = Column(Float)
    x_delp = Column(Float)
    fk = Column(Float)
    y_expansion = Column(Float)
    xt = Column(Float)
    xtp = Column(Float)
    fd = Column(Float)
    machNoUp = Column(Float)
    machNoDown = Column(Float)
    machNoValve = Column(Float)
    sonicVelUp = Column(Float)
    sonicVelDown = Column(Float)
    sonicVelValve = Column(Float)
    outletDensity = Column(Float)
    criticalPressure = Column(Float)
    inletPipeSize = Column(Float)
    outletPipeSize = Column(Float)
    valveSize = Column(Float)
    seatDia = Column(Float)
    ratedCv = Column(Float)

    # rel as child
    inletPipeSchId = Column(Integer, ForeignKey("pipeArea.id"))
    iPipe = relationship('pipeArea', back_populates='caseI', foreign_keys="[caseMaster.inletPipeSchId]")

    # outletPipeSchId = Column(Integer, ForeignKey("pipeArea.id"))
    # oPipe = relationship('pipeArea', back_populates='caseO', foreign_keys="[caseMaster.outletPipeSchId]")

    valveDiaId = Column(Integer, ForeignKey("cvTable.id"))
    cv = relationship('cvTable', back_populates='case')

    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship('itemMaster', back_populates='case')

    fluidId = Column(Integer, ForeignKey("fluidProperties.id"))
    fluid = relationship('fluidProperties', back_populates='case')


class actuatorMaster(db.Model):
    __tablename__ = "actuatorMaster"
    __mapper_args__ = {
        'polymorphic_identity': 'actuator',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    actuatorType = Column(String(100))
    springAction = Column(String(100))  # Fail Action
    handWheel = Column(String(100))
    adjustableTravelStop = Column(String(100))
    orientation = Column(String(100))
    availableAirSupplyMin = Column(Float)
    availableAirSupplyMax = Column(Float)
    travelStops = Column(String(100))

    # rel as parent
    actCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='actuator_')

    # rel as child to item
    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship('itemMaster', back_populates='actuator')

    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = actuatorMaster.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            print(key)
            print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()



class slidingActuatorData(db.Model):
    __mapper_args__ = {
        'polymorphic_identity': 'slidingAct',
        'confirm_deleted_rows': False
    }
    __tablename__ = "slidingActuatorData"
    id = Column(Integer, primary_key=True)
    actType = Column(String(100))
    failAction = Column(String(100))
    stemDia = Column(Float)
    yokeBossDia = Column(Float)
    actSize = Column(String(100))
    effectiveArea = Column(Float)
    travel = Column(Float)
    sMin = Column(Float)
    sMax = Column(Float)
    springRate = Column(Float)
    VO = Column(Float)
    VM = Column(Float)

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='slidingActuator')


class rotaryActuatorData(db.Model):
    __tablename__ = "rotaryActuatorData"
    __mapper_args__ = {
        'polymorphic_identity': 'rotAct',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    actType = Column(String(100))
    failAction = Column(String(100))
    valveInterface = Column(String(100))
    actSize_ = Column(String(100))
    actSize = Column(Float)
    springSet = Column(Integer)
    torqueType = Column(String(100))
    setPressure = Column(String(100))
    start = Column(Float)
    mid = Column(Float)
    end = Column(Float)

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='rotaryActuator')


class actuatorCaseData(db.Model):
    __tablename__ = "actuatorCaseData"
    __mapper_args__ = {
        'polymorphic_identity': 'actCase',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    # sliding
    balancing = Column(String(100))
    unbalanceArea = Column(Float)
    stemDia = Column(Float)
    plugDia = Column(Float)
    unbalanceForce = Column(Float)
    fluidNeg = Column(Float)
    valveThrustClose = Column(Float)
    valveThrustOpen = Column(Float)
    shutOffForce = Column(Float)
    stemArea = Column(Float)
    springWindUp = Column(Float)
    maxSpringLoad = Column(Float)
    setPressure = Column(Float)
    actThrustClose = Column(Float)
    actThrustOpen = Column(Float)
    frictionBand = Column(Float)
    reqHandwheelThrust = Column(Float)
    thrust = Column(Float)

    # rotary
    bushingCoeff = Column(Float)
    packingFrictionCoeff = Column(Float)
    aFactor = Column(Float)
    bFactor = Column(Float)
    packingRadialAxialStress = Column(Float)
    packingSection = Column(Float)
    seatingTorqueCalc = Column(Float)
    packingTorqueCalc = Column(Float)
    frictionTorqueCalc = Column(Float)
    bto = Column(Float)
    rto = Column(Float)
    eto = Column(Float)
    btc = Column(Float)
    rtc = Column(Float)
    etc = Column(Float)
    mast = Column(Float)
    setPressureR = Column(Float)
    reqHandTorque = Column(Float)

    # rel as child
    actuatorMasterId = Column(Integer, ForeignKey('actuatorMaster.id'))
    actuator_ = relationship('actuatorMaster', back_populates='actCase')

    packingFrictionId = Column(Integer, ForeignKey("packingFriction.id"))
    packingF = relationship('packingFriction', back_populates='actuatorCase')

    packingTorqueId = Column(Integer, ForeignKey("packingTorque.id"))
    packingT = relationship('packingTorque', back_populates='actuatorCase')

    seatLoadId = Column(Integer, ForeignKey("seatLoadForce.id"))
    seatLoad = relationship('seatLoadForce', back_populates='actuatorCase')

    seatingTorqueId = Column(Integer, ForeignKey("seatingTorque.id"))
    seatT = relationship('seatingTorque', back_populates='actuatorCase')

    slidingActuatorId = Column(Integer, ForeignKey("slidingActuatorData.id"))
    slidingActuator = relationship('slidingActuatorData', back_populates='actuatorCase')

    rotaryActuatorId = Column(Integer, ForeignKey("rotaryActuatorData.id"))
    rotaryActuator = relationship('rotaryActuatorData', back_populates='actuatorCase')

    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = actuatorCaseData.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            print(key)
            print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()


class packingFriction(db.Model):
    __tablename__ = "packingFriction"
    __mapper_args__ = {
        'polymorphic_identity': 'packingF',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    stemDia = Column(Float)
    value = Column(Float)

    # rel as child
    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship('ratingMaster', back_populates='packingF')

    packingMaterialId = Column(Integer, ForeignKey("packing.id"))
    packing_ = relationship('packing', back_populates='packingF')

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='packingF')


class packingTorque(db.Model):
    __tablename__ = "packingTorque"
    __mapper_args__ = {
        'polymorphic_identity': 'packingT',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    shaftDia = Column(Float)

    # rel as child
    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship('ratingMaster', back_populates='torque')

    cvId = Column(Integer, ForeignKey("cvTable.id"))
    cv = relationship('cvTable', back_populates='torque')

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='packingT')


class seatLoadForce(db.Model):
    __tablename__ = "seatLoadForce"
    __mapper_args__ = {
        'polymorphic_identity': 'seatLoad',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    seatBore = Column(Float)
    value = Column(Float)

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='seatLoad')

    # rel as child
    trimTypeId = Column(Integer, ForeignKey("trimType.id"))
    trimType_ = relationship('trimType', back_populates='seatLoad')

    leakageClassId = Column(Integer, ForeignKey('seatLeakageClass.id'))
    leakage = relationship('seatLeakageClass', back_populates='seatLoad')


class seatingTorque(db.Model):
    __tablename__ = "seatingTorque"
    __mapper_args__ = {
        'polymorphic_identity': 'seatTorq',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    discDia = Column(Float)
    valveSize = Column(Float)
    cusc = Column(Float)
    cusp = Column(Float)

    actuatorCase = relationship('actuatorCaseData', cascade="all,delete", back_populates='seatT')


class positioner(db.Model):
    __tablename__ = "positioner"
    __mapper_args__ = {
        'polymorphic_identity': 'pos',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    std = Column(String(200))
    manufacturer = Column(String(200))
    series = Column(String(200))
    moc = Column(String(200))
    enclosure = Column(String(200))
    spool_valve = Column(String(200))
    type = Column(String(200))
    technology = Column(String(200))
    communication = Column(String(200))
    action = Column(String(200))
    actions = Column(String(200))
    certificate = Column(String(200))
    model_no = Column(String(200))
    haz_class = Column(String(200))


class afr(db.Model):
    __tablename__ = "afr"
    __mapper_args__ = {
        'polymorphic_identity': 'afr_',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    manufacturer = Column(String(200))
    series = Column(String(200))
    moc = Column(String(200))
    size = Column(String(200))
    drain = Column(String(200))
    filter_size = Column(String(200))
    relive = Column(String(200))
    pressure_range = Column(String(200))
    fluid = Column(String(200))
    model = Column(String(200))
    remarks = Column(String(300))

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class limitSwitch(db.Model):
    __tablename__ = "limitSwitch"
    __mapper_args__ = {
        'polymorphic_identity': 'limitS',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    make = Column(String(200))
    explosion = Column(String(200))
    moc = Column(String(200))
    sensor = Column(String(200))
    display = Column(String(200))
    model = Column(String(200))
    remark = Column(String(200))
    pressure_range = Column(String(200))

    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = limitSwitch.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            print(key)
            print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()


class solenoid(db.Model):
    __tablename__ = "solenoid"
    __mapper_args__ = {
        'polymorphic_identity': 'solen',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    standard = Column(String(200))
    make = Column(String(200))
    series = Column(String(200))
    size = Column(String(200))
    type = Column(String(200))
    orifice = Column(String(200))
    cv = Column(String(200))
    model = Column(String(200))


class cleaning(db.Model):
    __tablename__ = "cleaning"
    __mapper_args__ = {
        'polymorphic_identity': 'clean',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class paintCerts(db.Model):
    __tablename__ = "paintCerts"
    __mapper_args__ = {
        'polymorphic_identity': 'paintC',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class paintFinish(db.Model):
    __tablename__ = "paintFinish"
    __mapper_args__ = {
        'polymorphic_identity': 'paintF',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class certification(db.Model):
    __tablename__ = "certification"
    
    __mapper_args__ = {
        'polymorphic_identity': 'cert',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class positionerSignal(db.Model):
    __tablename__ = "positionerSignal"
    __mapper_args__ = {
        'polymorphic_identity': 'posSignal',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class accessoriesData(db.Model):
    __tablename__ = "accessoriesData"
    __mapper_args__ = {
        'polymorphic_identity': 'accData',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)

    manufacturer = Column(String(200))
    model = Column(String(200))
    action = Column(String(200))
    afr = Column(String(200))
    transmitter = Column(String(200))
    limit = Column(String(200))
    proximity = Column(String(200))
    booster = Column(String(200))
    pilot_valve = Column(String(200))
    air_lock = Column(String(200))
    ip_make = Column(String(200))
    ip_model = Column(String(200))
    solenoid_make = Column(String(200))
    solenoid_model = Column(String(200))
    solenoid_action = Column(String(200))
    volume_tank = Column(String(200))
    ip_converter = Column(String(200))
    air_receiver = Column(String(200))
    tubing = Column(String(200))
    fittings = Column(String(200))
    cleaning = Column(String(200))
    certification = Column(String(200))
    paint_finish = Column(String(200))
    paint_cert = Column(String(200))
    sp1 = Column(String(200))
    sp2 = Column(String(200))
    sp3 = Column(String(200))
    rm = Column(String(200))
    hydro = Column(String(200))
    final = Column(String(200))
    paint_inspect = Column(String(200))
    packing_inspect = Column(String(200))
    vt1 = Column(String(200))
    vt2 = Column(String(200))

    # rel as child
    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship('itemMaster', back_populates='accessories')

    @staticmethod
    def update(new_data, id):
        # note that this method is static and
        # you have to pass id of the object you want to update
        keys = new_data.keys()  # new_data in your case is filenames
        files = accessoriesData.query.filter_by(id=id).first()  # files is the record
        # you want to update
        for key in keys:
            print(key)
            print(new_data[key])
            exec("files.{0} = new_data['{0}'][0]".format(key))
        db.session.commit()


class valveArea(db.Model):
    __tablename__ = "valveArea"
    __mapper_args__ = {
        'polymorphic_identity': 'vArea',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    rating = Column(String(300))
    nominalPipeSize = Column(String(300))
    inMM = Column(String(300))
    inInch = Column(String(300))
    area = Column(String(300))


class portArea(db.Model):
    __tablename__ = "portArea"
    __mapper_args__ = {
        'polymorphic_identity': 'pArea',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    model = Column(String(20))
    v_size = Column(String(20))
    seat_bore = Column(String(20))
    travel = Column(String(20))
    trim_type = Column(String(20))
    flow_char = Column(String(20))
    area = Column(String(20))


class hwThrust(db.Model):
    __tablename__ = "hwThrust"
    __mapper_args__ = {
        'polymorphic_identity': 'hw',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    failAction = Column(String(20))
    mount = Column(String(20))
    ac_size = Column(String(20))
    max_thrust = Column(String(20))
    dia = Column(String(20))


class knValue(db.Model):
    __tablename__ = "knValue"
    __mapper_args__ = {
        'polymorphic_identity': 'kn',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    portDia = Column(Float)
    value = Column(Float)

    # rel as child
    trimTypeId = Column(Integer, ForeignKey("trimType.id"))
    trimType_ = relationship('trimType', back_populates='kn')

    flowCharacId = Column(Integer, ForeignKey("flowCharacter.id"))
    flowCharacter_ = relationship('flowCharacter', back_populates='kn')

    flowDirId = Column(Integer, ForeignKey("flowDirection.id"))
    flowDirection_ = relationship('flowDirection', back_populates='kn')


class OTP(db.Model):
    __tablename__ = "OTP"
    __mapper_args__ = {
        'polymorphic_identity': 'otp',
        'confirm_deleted_rows': False
    }
    id = Column(Integer, primary_key=True)
    username = Column(String(100))
    otp = Column(BigInteger)
    time = Column(DateTime)


# with app.app_context():
#     db.create_all()

# TODO Other DAta
table_data_render = [
    {'name': 'Project Data', 'db': projectMaster, 'id': 1},
    {'name': 'Industry Data', 'db': industryMaster, 'id': 2},
    {'name': 'Region Data', 'db': regionMaster, 'id': 3},
    {'name': 'Engineer', 'db': engineerMaster, 'id': 4},
    {'name': 'Item', 'db': itemMaster, 'id': 5},
    {'name': 'Valve Style', 'db': valveStyle, 'id': 6},
    {'name': 'Rating', 'db': ratingMaster, 'id': 7},
    {'name': 'Material', 'db': materialMaster, 'id': 8},
    {'name': 'Standard Master', 'db': designStandard, 'id': 9},
    {'name': 'Fluid Type', 'db': fluidState, 'id': 10},
    {'name': 'Application', 'db': applicationMaster, 'id': 11},
    {'name': 'End Connection', 'db': endConnection, 'id': 12},
    {'name': 'End Finish', 'db': endFinish, 'id': 13},
    {'name': 'Bonnet Type', 'db': bonnetType, 'id': 14},
    {'name': 'PackingT ype', 'db': packingType, 'id': 15},
    {'name': 'Trim Type', 'db': trimType, 'id': 16},
    {'name': 'Flow Direction', 'db': flowDirection, 'id': 17},
    {'name': 'Leakage Class', 'db': seatLeakageClass, 'id': 18},
    {'name': 'Cleaning', 'db': cleaning, 'id': 19},
    {'name': 'Certification', 'db': certification, 'id': 20},
    {'name': 'Paint Finish', 'db': paintFinish, 'id': 21},
    {'name': 'Paint Certs', 'db': paintCerts, 'id': 22},
    {'name': 'Pipe Area', 'db': pipeArea, 'id': 23},
    {'name': 'Valve Area', 'db': valveArea, 'id': 24},
    {'name': 'Pressure Temperature', 'db': pressureTempRating, 'id': 25},
    {'name': 'Design Standard', 'db': designStandard, 'id': 26},
    {'name': 'Balance Seal', 'db': balanceSeal, 'id': 27},
    {'name': 'Balancing', 'db': balancing, 'id': 28},
    {'name': 'Bonnet', 'db': bonnet, 'id': 29},
    {'name': 'End Connection', 'db': endConnection, 'id': 30},
    {'name': 'End Finish', 'db': endFinish, 'id': 31},
    {'name': 'Flow Character', 'db': flowCharacter, 'id': 32},
    {'name': 'Fluid State', 'db': fluidState, 'id': 33},
    {'name': 'Gasket', 'db': gasket, 'id': 34},
    {'name': 'Packing Type', 'db': packingType, 'id': 35},
    {'name': 'Paint Certificates', 'db': paintCerts, 'id': 36},
    {'name': 'Paint Finish', 'db': paintFinish, 'id': 37},
    {'name': 'Limit Switch', 'db': limitSwitch, 'id': 38},
    {'name': 'AFR', 'db': afr, 'id': 39},
    {'name': 'Engineer Master', 'db': engineerMaster, 'id': 40},
    {'name': 'Fluid Properties', 'db': fluidProperties, 'id': 41},
    {'name': 'Positioner', 'db': positioner, 'id': 42},
    {'name': 'Positioner Signal', 'db': positionerSignal, 'id': 43},
    {'name': 'Packing Friction', 'db': packingFriction, 'id': 44},
    {'name': 'Packing Torque', 'db': packingTorque, 'id': 45},
    {'name': 'Port Area', 'db': portArea, 'id': 46},
    {'name': 'Seat', 'db': seat, 'id': 47},
    {'name': 'Seat Load Force', 'db': seatLoadForce, 'id': 48},
    {'name': 'Seating Torque', 'db': seatingTorque, 'id': 49},
    {'name': 'Shaft', 'db': shaft, 'id': 50},
    {'name': 'Packing', 'db': packing, 'id': 51},
    {'name': 'Kn Values', 'db': knValue, 'id': 52},
    {'name': 'HW Thrust', 'db': hwThrust, 'id': 53},
    {'name': 'Solenoid', 'db': solenoid, 'id': 54},
]


### ----------------------------------------- Actuator Functions --------------------------------#
def valveForces(p1_, p2_, d1, d2, d3, ua, rating, material, leakageClass, trimtype, balance, flow,
                case, shutoffDelP):
    print('Valve forces inputs:')
    print(p1_, p2_, d1, d2, d3, ua, rating, material, leakageClass, trimtype, balance, flow,
          case, shutoffDelP)
    num = 0
    if trimtype == 'contour':
        flow = 'under'
        balance = 'unbalanced'
    if d1 in [1, 3, 8, 11, 4]:
        d1 = round(d1)
    p1 = p1_
    p2 = p2_
    a1 = 0.785 * d1 * d1  # seat bore - seat dia
    a2 = 0.785 * d2 * d2  # plug dia
    a3 = 0.785 * d3 * d3  # stem dia
    shutoffDelP = shutoffDelP
    with app.app_context():
        friction_element = db.session.query(packingFriction).filter_by(stemDia=d3, pressure=rating).first()
        print(trimtype, d1)
        a_ = {'ptfe1': friction_element.ptfe1, 'ptfe2': friction_element.ptfe2, 'ptfer': friction_element.ptfer,
              'graphite': friction_element.graphite}
        print(trimtype, d1)
        sf_element = db.session.query(seatLoadForce).filter_by(trimtype=trimtype, seatBore=d1).first()
        # print(trimtype, d1)
        try:
            b_ = {'six': sf_element.six, 'two': sf_element.two, 'three': sf_element.three, 'four': sf_element.four,
                'five': sf_element.five}
            B = float(a_[material])
            C = math.pi * d1 * float(b_[leakageClass])
        except AttributeError:
            b_ = {'six': None, 'two': None, 'three': None, 'four': None,
                'five': None}
            B = 0
            C = 0
        # print(f"Packing friction: {B}, Seat Load Force: {C}")
    print((trimtype, balance, flow, case))
    for i in valve_force_dict:
        if i['key'] == (trimtype, balance, flow.lower(), case):
            num = int(i['formula'])
    print(f'num: {num}')
    if num == 1:
        a_ = shutoffDelP * a1
        UA = a1
    elif num == 2:
        a_ = shutoffDelP * a1
        UA = a1
    elif num == 3:
        a_ = shutoffDelP * (a3 - a1)
        UA = a3 - a1
    elif num == 4:
        a_ = shutoffDelP * (a3 - ua)
        UA = ua
    elif num == 5:
        a_ = shutoffDelP * ua
        UA = ua
    elif num == 6:
        a_ = (shutoffDelP * a1) + B + C
        UA = a1
        # print(a_, p1, a1)
    elif num == 7:
        a_ = (shutoffDelP * a1) + B + C
        UA = a1
        # print(a_, p1, a1)
    elif num == 8:
        a_ = (shutoffDelP * (a3 - a1)) + B + C
        UA = a3 - a1
    elif num == 9:
        a_ = shutoffDelP * (a3 - ua) + B + C
        UA = ua
        print(f"inputs for equation 9: {a3, ua, shutoffDelP, B, C}")
    elif num == 10:
        a_ = (shutoffDelP * ua) + B + C
        UA = ua
    elif num in [11, 12]:
        a_ = (p1 * a1) + (p2 * (a2 - a1)) - (p2 * (a2 - a3))
        print(f"eq 11 or 12 inputs: {p1}, {p2}, {a1}, {a2}, {a3}")
        UA = a2 - a1
    elif num == 13:
        a_ = p1 * (a2 - a1) + p2 * a1 - p1 * (a2 - a3)
        UA = a2 - a1
    elif num == 14:
        a_ = p1 * a1 + p2 * (a2 - a1) - p1 * (a2 - a3)
        UA = a2 - a1
    elif num == 15:
        a_ = p1 * (a2 - a1) + p2 * a1 - p2 * (a2 - a3)
        UA = a2 - a1
    elif num in [16, 17, 19]:
        a_ = (p1 * a2) - (p2 * (a2 - a3))
        print(f"eq 16 inputs: {p1}, {p2}, {a2}, {a3}")
        UA = a2 - a1
    elif num in [18, 20]:
        a_ = p2 * a2 - p1 * (a2 - a3)
        UA = a2 - a1
    else:
        a_ = 1
        UA = a2 - a1

    return_list = [round(a_, 3), UA, B, b_[leakageClass]]

    return return_list




### --------------------------------- Major Functions -----------------------------------------------------###

# Delete completed data in db table
def data_delete(table_name):
    # with app.app_context():
    data_list = table_name.query.all()
    for data_ in data_list:
        db.session.delete(data_)
        db.session.commit()


def next_alpha(s):
    return chr((ord(s.upper()) + 1 - 65) % 26 + 65)


# Data upload function   lllll
def data_upload(data_list, table_name):
    # with app.app_context():
    print(f"data delete starts: {table_name.__tablename__}")
    # data_delete(table_name)
    # print("data delete ends")
    print('dataupload starts')
    all_data = table_name.query.all()
    old_del_count = 0
    for dd in all_data:
        if dd.name not in data_list:
            db.session.delete(dd)
            db.session.commit()
            old_del_count += 1
            
    new_count = 0
    for data_ in data_list:
        data_element = db.session.query(table_name).filter_by(name=data_).all()
        if len(data_element) == 0:
            new_data = table_name(name=data_)
            db.session.add(new_data)
            db.session.commit()
            new_count += 1
    
    print(new_count, old_del_count)
    print('data upload ends')


def pressure_temp_upload(data_set):
    # with app.app_context():
    data_d_list = pressureTempRating.query.all()
    data_delete(pressureTempRating)
    for data_ in data_set:
        material_element = db.session.query(materialMaster).filter_by(name=data_['material']).first()
        rating_element = db.session.query(ratingMaster).filter_by(name=data_['rating']).first()
        new_data = pressureTempRating(maxTemp=data_['maxTemp'], minTemp=data_['minTemp'],
                                        pressure=data_['pressure'], material=material_element, rating=rating_element)
        db.session.add(new_data)
        db.session.commit()


def add_many(list_many, table_name):

    data_delete(table_name)
    for i in list_many:
        new_object = table_name()
        db.session.add(new_object)
        db.session.commit()
        # print(i)
        keys = i.keys()
        for key in keys:
            exec("new_object.{0} = i['{0}']".format(key))
        db.session.commit()
    # db.session.add_all(list_many)
    # db.session.commit()


def cv_upload(data_list):
    with app.app_context():
        print("delete begin")
        # data_delete(cvValues)
        data_delete(cvTable)
        print("delete done")
        new_data_list = data_list[::4]  # Get every fourth element from the list
        len_data = len(new_data_list)

        for data_index in range(len_data):
            # Get DB Element
            trim_type_element = db.session.query(trimType).filter_by(
                name=new_data_list[data_index]['trimType_']).first()
            flow_charac_element = db.session.query(flowCharacter).filter_by(
                name=new_data_list[data_index]['flowCharacter_']).first()
            flow_direction_element = db.session.query(flowDirection).filter_by(
                name=new_data_list[data_index]['flowDirection_']).first()
            balancing_element = db.session.query(balancing).filter_by(
                name=new_data_list[data_index]['balancing_']).first()
            rating_element = db.session.query(ratingMaster).filter_by(
                name=new_data_list[data_index]['rating_c']).first()
            v_style_element = db.session.query(valveStyle).filter_by(name=new_data_list[data_index]['style']).first()
            valve_size = float(new_data_list[data_index]['valveSize'])
            series = new_data_list[data_index]['series']

            # Add CV Table Data
            # print(new_data_list[data_index]['no'], trim_type_element.name, flow_charac_element.name, flow_direction_element.name, balancing_element.name, rating_element.name, v_style_element.name)
            new_cv_table_entry = cvTable(
                valveSize=valve_size,
                series=series,
                trimType_=trim_type_element,
                flowCharacter_=flow_charac_element,
                flowDirection_=flow_direction_element,
                balancing_=balancing_element,
                rating_c=rating_element,
                style=v_style_element
            )
            db.session.add(new_cv_table_entry)
            db.session.commit()

        # Once data added, input all cv values
        all_cvs = cvTable.query.all()
        for cv_index in range(len(all_cvs)):
            # CV value from excel
            new_cv_values_cv = cvValues(
                coeff=data_list[cv_index * 4]['coeff'],
                seatBore=float(data_list[cv_index * 4]['seatBore']),
                travel=float(data_list[cv_index * 4]['travel']),
                cv=all_cvs[cv_index],
                one=float(data_list[cv_index * 4]['one']),
                two=float(data_list[cv_index * 4]['two']),
                three=float(data_list[cv_index * 4]['three']),
                four=float(data_list[cv_index * 4]['four']),
                five=float(data_list[cv_index * 4]['five']),
                six=float(data_list[cv_index * 4]['six']),
                seven=float(data_list[cv_index * 4]['seven']),
                eight=float(data_list[cv_index * 4]['eight']),
                nine=float(data_list[cv_index * 4]['nine']),
                ten=float(data_list[cv_index * 4]['ten'])
            )

            # Fl Value from excel
            new_cv_values_fl = cvValues(
                coeff=data_list[cv_index * 4 + 1]['coeff'],
                seatBore=float(data_list[cv_index * 4 + 1]['seatBore']),
                travel=float(data_list[cv_index * 4 + 1]['travel']),
                cv=all_cvs[cv_index],
                one=float(data_list[cv_index * 4 + 1]['one']),
                two=float(data_list[cv_index * 4 + 1]['two']),
                three=float(data_list[cv_index * 4 + 1]['three']),
                four=float(data_list[cv_index * 4 + 1]['four']),
                five=float(data_list[cv_index * 4 + 1]['five']),
                six=float(data_list[cv_index * 4 + 1]['six']),
                seven=float(data_list[cv_index * 4 + 1]['seven']),
                eight=float(data_list[cv_index * 4 + 1]['eight']),
                nine=float(data_list[cv_index * 4 + 1]['nine']),
                ten=float(data_list[cv_index * 4 + 1]['ten'])
            )

            # Xt value from excel
            new_cv_values_xt = cvValues(
                coeff=data_list[cv_index * 4 + 2]['coeff'],
                seatBore=float(data_list[cv_index * 4 + 2]['seatBore']),
                travel=float(data_list[cv_index * 4 + 2]['travel']),
                cv=all_cvs[cv_index],
                one=float(data_list[cv_index * 4 + 2]['one']),
                two=float(data_list[cv_index * 4 + 2]['two']),
                three=float(data_list[cv_index * 4 + 2]['three']),
                four=float(data_list[cv_index * 4 + 2]['four']),
                five=float(data_list[cv_index * 4 + 2]['five']),
                six=float(data_list[cv_index * 4 + 2]['six']),
                seven=float(data_list[cv_index * 4 + 2]['seven']),
                eight=float(data_list[cv_index * 4 + 2]['eight']),
                nine=float(data_list[cv_index * 4 + 2]['nine']),
                ten=float(data_list[cv_index * 4 + 2]['ten'])
            )

            # Fd value from excel
            new_cv_values_fd = cvValues(
                coeff=data_list[cv_index * 4 + 3]['coeff'],
                seatBore=float(data_list[cv_index * 4 + 3]['seatBore']),
                travel=float(data_list[cv_index * 4 + 3]['travel']),
                cv=all_cvs[cv_index],
                one=float(data_list[cv_index * 4 + 3]['one']),
                two=float(data_list[cv_index * 4 + 3]['two']),
                three=float(data_list[cv_index * 4 + 3]['three']),
                four=float(data_list[cv_index * 4 + 3]['four']),
                five=float(data_list[cv_index * 4 + 3]['five']),
                six=float(data_list[cv_index * 4 + 3]['six']),
                seven=float(data_list[cv_index * 4 + 3]['seven']),
                eight=float(data_list[cv_index * 4 + 3]['eight']),
                nine=float(data_list[cv_index * 4 + 3]['nine']),
                ten=float(data_list[cv_index * 4 + 3]['ten'])
            )

            # Add object in a single session
            objects_list = [new_cv_values_cv, new_cv_values_fl, new_cv_values_xt, new_cv_values_fd]
            db.session.add_all(objects_list)
            db.session.commit()


def data_upload_disc_seat_packing(data_list, valve_style, table_name):
   
    data_delete(table_name)
    for style_index in range(len(valve_style)):
        for data in data_list[style_index]:
            new_data = table_name(name=data, style=valve_style[style_index])
            db.session.add(new_data)
            db.session.commit()


def data_upload_shaft(data_list, v_style_list):

    data_delete(shaft)
    all_elements = []
    for style_ in v_style_list:
        for data_ in data_list:
            new_shaft = shaft(name=data_['name'], yield_strength=data_['yield_strength'], style=style_)
            all_elements.append(new_shaft)

    db.session.add_all(all_elements)
    db.session.commit()


def addProjectRels(cname, cnameE, address, addressE, aEng, cEng, project, operation):
    # with app.app_context():
    company_element = db.session.query(companyMaster).filter_by(name=cname).first()
    company_element_E = db.session.query(companyMaster).filter_by(name=cnameE).first()
    company_address_element = db.session.query(addressMaster).filter_by(address=address,
                                                                        company=company_element).first()
    company_address_element_E = db.session.query(addressMaster).filter_by(address=addressE,
                                                                            company=company_element_E).first()
    aEng_ = engineerMaster.query.get(int(aEng))
    cEng_ = engineerMaster.query.get(int(cEng))
    if operation == 'create':
        # Add Engineers
        new_addr_project_company = addressProject(isCompany=True, address=company_address_element, project=project)
        new_addr_project_enduser = addressProject(isCompany=False, address=company_address_element_E, project=project)
        # Add Addresses
        new_er_project_application = engineerProject(isApplication=True, engineer=aEng_, project=project)
        new_er_project_contract = engineerProject(isApplication=False, engineer=cEng_, project=project)

        db.session.add_all(
            [new_addr_project_company, new_addr_project_enduser, new_er_project_application, new_er_project_contract])
        db.session.commit()
    elif operation == 'update':
        address_element_c = db.session.query(addressProject).filter_by(isCompany=True, project=project).first()
        address_element_e = db.session.query(addressProject).filter_by(isCompany=False, project=project).first()
        er_app = db.session.query(engineerProject).filter_by(isApplication=True, project=project).first()
        er_contr = db.session.query(engineerProject).filter_by(isApplication=False, project=project).first()

        if address_element_c and address_element_e and er_app and er_contr:
            address_element_c.address = company_address_element
            address_element_e.address = company_address_element_E
            er_app.engineer = aEng_
            er_contr.engineer = cEng_
            print(address_element_c.address, address_element_e.address, er_app.engineer, er_contr.engineer)
            db.session.commit()
        else:
            # Add Engineers
            new_addr_project_company = addressProject(isCompany=True, address=company_address_element, project=project)
            new_addr_project_enduser = addressProject(isCompany=False, address=company_address_element_E,
                                                        project=project)
            # Add Addresses
            new_er_project_application = engineerProject(isApplication=True, engineer=aEng_, project=project)
            new_er_project_contract = engineerProject(isApplication=False, engineer=cEng_, project=project)

            db.session.add_all([new_addr_project_company, new_addr_project_enduser, new_er_project_application,
                                new_er_project_contract])
            db.session.commit()


def addUserAsEng(name, designation):
    # with app.app_context():
    new_engineer = engineerMaster(name=name, designation=designation)
    db.session.add(new_engineer)
    db.session.commit()


def newUserProjectItem(user):
# with app.app_context():
    fluid_state = getDBElementWithId(fluidState, 1)
    new_project = projectMaster(user=user,
                                projectId=f"Q{date_today[2:4]}0000",
                                enquiryReceivedDate=datetime.datetime.today(),
                                receiptDate=datetime.datetime.today(),
                                bidDueDate=datetime.datetime.today())
    new_item = itemMaster(project=new_project, itemNumber=1, alternate='A')
    new_valve = valveDetailsMaster(item=new_item, state=fluid_state)
    new_actuator = actuatorMaster(item=new_item)
    new_accessories = accessoriesData(item=new_item)
    db.session.add_all([new_project, new_item, new_valve, new_actuator, new_accessories])
    db.session.commit()


def newProjectItem(project):
    fluid_state = getDBElementWithId(fluidState, 1)
    new_item = itemMaster(project=project, itemNumber=1, alternate='A')
    db.session.add(new_item)
    db.session.commit()
    new_valve_det = valveDetailsMaster(item=new_item, state=fluid_state)
    db.session.add(new_valve_det)
    db.session.commit()
    new_actuator = actuatorMaster(item=new_item)
    db.session.add(new_actuator)
    db.session.commit()
    new_accessories = accessoriesData(item=new_item)
    db.session.add(new_accessories)
    db.session.commit()
    return new_item


def addNewItem(project, itemNumber, alternate):
    # with app.app_context():
    fluid_state = getDBElementWithId(fluidState, 1)
    new_item = itemMaster(project=project, itemNumber=itemNumber, alternate=alternate)
    db.session.add(new_item)
    db.session.commit()
    new_valve_det = valveDetailsMaster(item=new_item, state=fluid_state)
    db.session.add(new_valve_det)
    db.session.commit()
    new_actuator = actuatorMaster(item=new_item)
    db.session.add(new_actuator)
    db.session.commit()
    new_accessories = accessoriesData(item=new_item)
    db.session.add(new_accessories)
    db.session.commit()
    return new_item


# TODO Functional Module
def sendOTP(username):
    # Generate Random INT
    random_decimal = random.random()
    random_int = round(random_decimal * 10 ** 6)
    with app.app_context():
        new_otp = OTP(otp=random_int, username=username, time=datetime.datetime.now())
        db.session.add(new_otp)
        db.session.commit()


def getEngAddrList(all_projects):
    address_ = []
    eng_ = []
    for project in all_projects:
        address_c = db.session.query(addressProject).filter_by(project=project, isCompany=True).first()
        eng_a = db.session.query(engineerProject).filter_by(project=project, isApplication=False).first()
        address_.append(address_c)
        eng_.append(eng_a)
    return address_, eng_


def getEngAddrProject(project):
    address_c = db.session.query(addressProject).filter_by(project=project, isCompany=True).first()
    address_e = db.session.query(addressProject).filter_by(project=project, isCompany=False).first()
    eng_a = db.session.query(engineerProject).filter_by(project=project, isApplication=True).first()
    eng_c = db.session.query(engineerProject).filter_by(project=project, isApplication=False).first()
    return address_c, address_e, eng_a, eng_c


def getDBElementWithId(table_name, id):
    # with app.app_context():
    output_element = db.session.query(table_name).filter_by(id=id).first()
    return output_element


date_today = datetime.datetime.now().strftime("%Y-%m-%d")


def metadata():
    companies = companyMaster.query.all()
    industries = industryMaster.query.all()
    regions = regionMaster.query.all()
    engineers = engineerMaster.query.all()
    ratings = ratingMaster.query.all()
    bodyMaterial = materialMaster.query.all()
    standard_ = designStandard.query.all()
    valveStyles = valveStyle.query.all()
    endconnection = endConnection.query.all()
    endfinish = endFinish.query.all()
    bonnettype = bonnetType.query.all()
    packingtype = packingType.query.all()
    trimtype = trimType.query.all()
    flowcharacter = flowCharacter.query.all()
    flowdirection = flowDirection.query.all()
    flowCharacter_ = flowCharacter.query.all()
    seatleakageclass = seatLeakageClass.query.all()
    bonnet_ = bonnet.query.all()
    shaft_ = shaft.query.all()
    disc_ = disc.query.all()
    seat_ = seat.query.all()
    packing_ = packing.query.all()
    balanceseal = balanceSeal.query.all()
    studnut = studNut.query.all()
    gasket_ = gasket.query.all()
    cageclamp = cageClamp.query.all()
    application_ = applicationMaster.query.all()
    fluids = fluidProperties.query.all()
    fluid_state = fluidState.query.all()
    valveSeries = []
    for notes_ in db.session.query(cvTable.series).distinct():
        valveSeries.append(notes_.series)

    notes_dict = {}
    for nnn in companies:
        contents = db.session.query(addressMaster).filter_by(company=nnn).all()
        content_list = [cont.address for cont in contents]
        notes_dict[nnn.name] = content_list

    data_dict = {
        "companies": companies,
        "industries": industries,
        "regions": regions,
        "engineers": engineers,
        "notes_dict": json.dumps(notes_dict),
        "notes_dict_": notes_dict,
        "status": project_status_list,
        "date": date_today,
        "purpose": purpose_list,
        "ratings": ratings,
        "bodyMaterial": bodyMaterial,
        "standard": standard_,
        "valveStyle": valveStyles,
        "valveSeries": valveSeries,
        "endconnection": endconnection,
        "endfinish": endfinish,
        "bonnettype": bonnettype,
        "packingtype": packingtype,
        "trimtype": trimtype,
        "flowcharacter": flowcharacter,
        "flowdirection": flowdirection,
        "seatleakageclass": seatleakageclass,
        "bonnet": bonnet_,
        "shaft": shaft_,
        "disc": disc_,
        "seat": seat_,
        "packing": packing_,
        "balanceseal": balanceseal,
        "studnut": studnut,
        "gasket": gasket_,
        "cageclamp": cageclamp,
        "application": application_,
        "units_dict": units_dict,
        "fluids": fluids,
        "fluidState": fluid_state,
        "flowCharacter": flowCharacter_,
        "actuatorData": actuator_data_dict
    }

    positioner_manufacturer = []
    for notes_ in db.session.query(positioner.manufacturer).distinct():
        positioner_manufacturer.append(notes_.manufacturer)

    positioner_model = []
    for notes_ in db.session.query(positioner.series).distinct():
        positioner_model.append(notes_.series)

    positioner_action = []
    for notes_ in db.session.query(positioner.action).distinct():
        positioner_action.append(notes_.action)
    
    solenoid_make = []
    for notes_ in db.session.query(solenoid.make).distinct():
        solenoid_make.append(notes_.make)

    solenoid_model = []
    for notes_ in db.session.query(solenoid.model).distinct():
        solenoid_model.append(notes_.model)

    solenoid_type = []
    for notes_ in db.session.query(solenoid.type).distinct():
        solenoid_type.append(notes_.type)

    all_afr = afr.query.all()
    afr_ = [f"{pos.manufacturer}/{pos.model}" for pos in all_afr]

    all_limit_switch = limitSwitch.query.all()
    limit_switch_ = [l.model for l in all_limit_switch]
    
    data_dict['positioner_manufacturer'] = positioner_manufacturer
    data_dict['positioner_model'] = positioner_model
    data_dict['positioner_action'] = positioner_action
    data_dict['afr_'] = afr_
    data_dict['limit_switch_'] = limit_switch_
    data_dict['solenoid_make'] = solenoid_make
    data_dict['solenoid_model'] = solenoid_model
    data_dict['solenoid_type'] = solenoid_type
    data_dict['boosters'] = ['I-BP1A', 'W20359']
    return data_dict


# TODO ------------------------------------------ SIZING PYTHON CODE --------------------------------------- #


# Cv1 = Cv_butterfly_6
# FL1 = Fl_butterfly_6


# TODO - Liquid Sizing - fisher
def etaB(valveDia, pipeDia):
    return 1 - ((valveDia / pipeDia) ** 4)


def eta1(valveDia, pipeDia):
    return 0.5 * ((1 - ((valveDia / pipeDia) ** 2)) ** 2)


def eta2(valveDia, pipeDia):
    return 1 * ((1 - ((valveDia / pipeDia) ** 2)) ** 2)


def sigmaEta(valveDia, inletDia, outletDia):
    a_ = eta1(valveDia, inletDia) + eta2(valveDia, outletDia) + etaB(valveDia, inletDia) - etaB(valveDia, outletDia)
    # print(
    #     f"sigma eta inputs: {eta1(valveDia, inletDia)}, {eta2(valveDia, outletDia)}, {etaB(valveDia, inletDia)}, {valveDia}, {outletDia}")
    return a_


def FF(vaporPressure, criticalPressure):
    a = 0.96 - 0.28 * math.sqrt(vaporPressure / criticalPressure)
    return a


def fP(C, valveDia, inletDia, outletDia, N2_value):
    a = (sigmaEta(valveDia, inletDia, outletDia) / N2_value) * ((C / valveDia ** 2) ** 2)
    # print(
    #     f"fp numerator: {a}, n2 value: {N2_value}, valveDia: {valveDia}, sigmaeta: {sigmaEta(valveDia, inletDia, outletDia)}, CV: {C}")
    # print(f"Sigma eta: {sigmaEta(valveDia, inletDia, outletDia)}")
    b_ = 1 / math.sqrt(1 + a)
    # return 0.71
    return b_


def flP(C, valveDia, inletDia, N2_value, Fl):
    K1 = eta1(valveDia, inletDia) + etaB(valveDia, inletDia)
    # print(f"k1, valvedia, inlet, C: {K1}, {valveDia}, {inletDia}, {N2_value}, {Fl}, {C}")
    a = (K1 / N2_value) * ((C / valveDia ** 2) ** 2)
    # print(f"a for flp: {a}")
    try:
        b_ = 1 / math.sqrt((1 / (Fl * Fl)) + a)
    except:
        b_ = 0.9
    return b_


def delPMax(Fl, Ff, inletPressure, vaporPressure):
    a_ = Fl * Fl * (inletPressure - (Ff * vaporPressure))
    # print(f"delpmax: {Fl}, {inletPressure}, {Ff}, {vaporPressure}")
    return round(a_, 3)


def selectDelP(Fl, criticalPressure, inletPressure, vaporPressure, outletPressure):
    Ff = FF(vaporPressure, criticalPressure)
    a_ = delPMax(Fl, Ff, inletPressure, vaporPressure)
    b_ = inletPressure - outletPressure
    return min(a_, b_)


def Cvt(flowrate, N1_value, inletPressure, outletPressure, sGravity):
    a_ = N1_value * math.sqrt((inletPressure - outletPressure) / sGravity)
    b_ = flowrate / a_
    # print(f"CVt: {b_}")
    return round(b_, 3)


def reynoldsNumber(N4_value, Fd, flowrate, viscosity, Fl, N2_value, pipeDia, N1_value, inletPressure, outletPressure,
                   sGravity):
    Cv_1 = Cvt(flowrate, N1_value, inletPressure, outletPressure, sGravity)
    # print(Cv_1)
    a_ = (N4_value * Fd * flowrate) / (viscosity * math.sqrt(Fl * Cv_1))
    # print(a_)
    b_ = ((Fl * Cv_1) ** 2) / (N2_value * (pipeDia ** 4))
    c_ = (1 + b_) ** (1 / 4)
    d_ = a_ * c_
    return round(d_, 3)


def getFR(N4_value, Fd, flowrate, viscosity, Fl, N2_value, pipeDia, N1_value, inletPressure, outletPressure, sGravity):
    RE = reynoldsNumber(N4_value, Fd, flowrate, viscosity, Fl, N2_value, pipeDia, N1_value, inletPressure,
                        outletPressure, sGravity)
    # print(RE)
    if 56 <= RE <= 40000:
        a = 0
        while True:
            # print(f"Cv1, C: {Cv1[a], C}")
            if REv[a] == RE:
                return FR[a]
            elif REv[a] > RE:
                break
            else:
                a += 1

        fr = FR[a - 1] - (((REv[a - 1] - RE) / (REv[a - 1] - REv[a])) * (FR[a - 1] - FR[a]))

        return round(fr, 3)
    elif RE < 56:
        a = 0.019 * (RE ** 0.67)
        return a
    else:
        return 1


# print(7600, 1, 300, 8000, 0.68, 0.00214, 80, 0.865, 8.01, 6.01, 0.908)


def CV(flowrate, C, valveDia, inletDia, outletDia, N2_value, inletPressure, outletPressure, sGravity, N1_value, Fd,
       vaporPressure, Fl, criticalPressure, N4_value, viscosity, thickness):
    if valveDia != inletDia:
        FLP = flP(C, valveDia, inletDia + 2 * thickness, N2_value, Fl)
        FP = fP(C, valveDia, inletDia + 2 * thickness, outletDia + 2 * thickness, N2_value)
        # print(f"FP: {FP}")
        FL = FLP / FP
    else:
        FL = Fl
    delP = selectDelP(FL, criticalPressure, inletPressure, vaporPressure, outletPressure)
    Fr = getFR(N4_value, Fd, flowrate, viscosity, FL, N2_value, inletDia + 2 * thickness, N1_value, inletPressure,
               outletPressure,
               sGravity)
    # print(Fr)
    fp_val = fP(C, valveDia, inletDia + 2 * thickness, outletDia + 2 * thickness, N2_value)
    a_ = N1_value * fp_val * Fr * math.sqrt(delP / sGravity)
    b_ = flowrate / a_
    # print(f"FR: {Fr}")
    return round(b_, 3)

### --------------------------------- Routes -----------------------------------------------------###

def getUniqueValues(table_name):
    empty_list = []
    for notes_ in db.session.query(table_name.name).distinct():
        empty_list.append({"id": notes_.id, "name": notes_.name})
    return empty_list


# TODO Login Module

@app.route('/admin-register', methods=["GET", "POST"])
def register():
    designations_ = designationMaster.query.all()
    
    departments_ = departmentMaster.query.all()
    if request.method == "POST":

        if userMaster.query.filter_by(email=request.form['email']).first():
            # user already exists
            flash("Email-ID already exists")
            return redirect(url_for('register'))
        else:
            department_element = departmentMaster.query.get(int(request.form['department']))
            designation_element = designationMaster.query.get(int(request.form['designation']))
            new_user = userMaster(email=request.form['email'],
                                  password=generate_password_hash(request.form['password'], method='pbkdf2:sha256',
                                                                  salt_length=8),
                                  name=request.form['name'],
                                  employeeId=request.form['employeeId'],
                                  mobile=request.form['mobile'],
                                  designation=designation_element,
                                  department=department_element,
                                  fccUser=True
                                  )
            db.session.add(new_user)
            db.session.commit()

            if department_element.name == "Application Engineering, Sales & Contracts":
                addUserAsEng(request.form['name'], designation_element.name)

            # Add Project and Item
            newUserProjectItem(user=new_user)
            # login_user(new_user)
            # flash('Logged in successfully.')
            return redirect(url_for('login'))

    return render_template("admin-registration.html", designations=designations_, departments=departments_)


@app.route('/', methods=["GET", "POST"])
def login():
    # form = LoginForm()
    if request.method == "POST":

        user = userMaster.query.filter_by(email=request.form['email']).first()

        # email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))

        # Password incorrect
        elif not check_password_hash(user.password, request.form['password']):
            flash("Password incorrect, please try again.")
            return redirect(url_for('login'))

        # email exists and password correct
        else:
            login_user(user)
            project_element = db.session.query(projectMaster).filter_by(user=user).first()
            item_element = db.session.query(itemMaster).filter_by(project=project_element).first()
            return redirect(url_for('home', proj_id=project_element.id, item_id=item_element.id))

    return render_template("login.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# TODO Dashboard Module

@app.route('/home/proj-<proj_id>/item-<item_id>', methods=['GET'])
def home(proj_id, item_id):
    item_element = itemMaster.query.get(int(item_id))
    all_projects = db.session.query(projectMaster).filter_by(user=current_user).all()
    address_, eng_ = getEngAddrList(all_projects)
    items_list = db.session.query(itemMaster).filter_by(project=projectMaster.query.get(int(proj_id))).order_by(
        itemMaster.itemNumber.asc()).all()
    valve_list = [db.session.query(valveDetailsMaster).filter_by(item=item_).first() for item_ in items_list]
    return render_template('dashboard.html', user=current_user, projects=all_projects, address=address_, eng=eng_,
                            item=item_element, items=valve_list, page='home')


@app.route('/getItems/proj-<proj_id>', methods=['GET'])
def getItems(proj_id):
    items_list = db.session.query(itemMaster).filter_by(project=projectMaster.query.get(int(proj_id))).all()
    print(len(items_list))
    return redirect(url_for('home', proj_id=proj_id, item_id=items_list[0].id))


@app.route('/selectItem/item-<item_id>', methods=['GET'])
def selectItem(item_id):
    item_ = itemMaster.query.get(int(item_id))
    return redirect(url_for('home', proj_id=item_.project.id, item_id=item_.id))


@app.route('/add-item/proj-<proj_id>/item-<item_id>', methods=['GET'])
def addItem(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, item_id)
    project_element = getDBElementWithId(projectMaster, item_element.project.id)
    all_items = db.session.query(itemMaster).filter_by(project=project_element).all()
    last_item = all_items[-1]
    itemNumberCurrent = int(last_item.itemNumber) + 1
    addNewItem(project=project_element, itemNumber=itemNumberCurrent, alternate='A')
    return redirect(url_for('home', proj_id=proj_id, item_id=item_id))


@app.route('/add-alternate/proj-<proj_id>/item-<item_id>', methods=['GET'])
def addAlternate(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, item_id)
    project_element = getDBElementWithId(projectMaster, item_element.project.id)
    n_items = db.session.query(itemMaster).filter_by(project=project_element, itemNumber=item_element.itemNumber).all()
    itemNumberCurrent = int(item_element.itemNumber)
    alternateCurrent = next_alpha(n_items[-1].alternate)
    addNewItem(project=project_element, itemNumber=itemNumberCurrent, alternate=alternateCurrent)
    return redirect(url_for('home', proj_id=proj_id, item_id=item_id))


@app.route('/preferences/proj-<proj_id>/item-<item_id>/<page>', methods=['GET', 'POST'])
def preferences(proj_id, item_id, page):
    metadata_ = metadata()
    with app.app_context():
        return render_template('preferences.html', user=current_user, metadata=metadata_, item=getDBElementWithId(itemMaster, item_id), page=page)


@app.route('/updatePreferences/proj-<proj_id>/item-<item_id>/<page>', methods=['POST'])
def updatePreferences(proj_id, item_id, page):
    with app.app_context():
        project_element = getDBElementWithId(projectMaster, proj_id)
        project_element.pressureUnit = request.form['pressureUnit']
        project_element.temperatureUnit = request.form['temperatureUnit']
        project_element.flowrateUnit = request.form['flowrateUnit']
        project_element.lengthUnit = request.form['lengthUnit']
        db.session.commit()
        return redirect(url_for(page, proj_id=proj_id, item_id=item_id))


# TODO Company Module

@app.route('/company-master/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def addCompany(proj_id, item_id):
    all_company = companyMaster.query.all()
    company_names = [company.name for company in all_company]
    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        if name in company_names:
            flash('Company already exists')
            return redirect(url_for('addCompany'))
        else:
            new_company = companyMaster(name=name, description=description)
            db.session.add(new_company)
            db.session.commit()

            flash(f"Company: {name} added successfully.")
            return redirect(url_for('companyEdit', company_id=new_company.id, item_id=item_id, proj_id=proj_id))
    return render_template('customer_master.html', companies=all_company, user=current_user,
                           item=getDBElementWithId(itemMaster, item_id), page='addCompany')


@app.route('/company-edit/proj-<proj_id>/item-<item_id>/<company_id>', methods=['GET', 'POST'])
def companyEdit(company_id, proj_id, item_id):
    company_element = companyMaster.query.get(company_id)
    addresses = db.session.query(addressMaster).filter_by(company=company_element).all()
    all_addresses = addressMaster.query.all()
    len_all_addr = len(all_addresses)
    len_addr = len(addresses)
    if request.method == 'POST':
        company_element.name = request.form.get('name')
        company_element.description == request.form.get('description')
        new_address = addressMaster(address=request.form.get('address'), company=company_element,
                                    customerCode=full_format(len_all_addr), isActive=True)
        db.session.add(new_address)
        db.session.commit()
        flash('Address added successfully')
        return redirect(url_for('companyEdit', company_id=company_element.id, item_id=item_id, proj_id=proj_id))
    return render_template('customer_master_edit.html', user=current_user, company=company_element, addresses=addresses,
                           addresses_len=range(len_addr), item=getDBElementWithId(itemMaster, item_id), page='companyEdit')


@app.route('/del-address/<address_id>/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def delAddress(address_id, item_id, proj_id):
    addresss_element = addressMaster.query.get(address_id)
    company_id = addresss_element.company.id
    if addresss_element.isActive:
        addresss_element.isActive = False
    else:
        addresss_element.isActive = True
    db.session.commit()
    # db.session.delete(addresss_element)
    # db.session.commit()
    return redirect(url_for('companyEdit', company_id=company_id, item_id=item_id, proj_id=proj_id))


# TODO Project Module

@app.route('/add-project/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def addProject(proj_id, item_id):
    with app.app_context():
        metadata_ = metadata()
        if request.method == "POST":
            len_project = len(projectMaster.query.all())

            data = request.form.to_dict(flat=False)
            quote_no = f"Q{date_today[2:4]}0000{len_project}"
            a = jsonify(data).json

            new_project = projectMaster(
                projectId=quote_no,
                projectRef=a['projectRef'][0],
                enquiryRef=a['enquiryRef'][0],
                enquiryReceivedDate=datetime.datetime.strptime(a['enquiryReceivedDate'][0], '%Y-%m-%d'),
                receiptDate=datetime.datetime.strptime(a['receiptDate'][0], '%Y-%m-%d'),
                bidDueDate=datetime.datetime.strptime(a['bidDueDate'][0], '%Y-%m-%d'),
                purpose=a['purpose'][0],
                custPoNo=a['custPoNo'][0],
                workOderNo=a['workOderNo'][0],
                status=a['status'][0],
                user=current_user,
                industry=getDBElementWithId(industryMaster, a['industry'][0]),
                region=getDBElementWithId(regionMaster, a['region'][0]),
            )
            db.session.add(new_project)
            db.session.commit()

            # add dummy Item 
            add_item = newProjectItem(new_project)

            project_element = db.session.query(projectMaster).filter_by(projectId=quote_no).first()

            addProjectRels(a['cname'][0], a['cnameE'][0], a['address'][0], a['addressE'][0], a['aEng'][0], a['cEng'][0],
                           project_element, 'create')

            flash('Project Added Successfully')
            print(a)
            return redirect(url_for('home', proj_id=add_item.project.id, item_id=add_item.id))

        # return render_template('projectdetails.html', dropdown=json.dumps(metadata_['notes_dict']), industries=metadata_['industries'], regions=metadata_['regions'], engineers=metadata_['engineers'], user=current_user, status=project_status_list, date=date_today, item=getDBElementWithId(itemMaster, item_id))
        return render_template('projectdetails.html', metadata=metadata_, user=current_user,
                               item=getDBElementWithId(itemMaster, item_id), page='addProject')


@app.route('/edit-project/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def editProject(proj_id, item_id):
    metadata_ = metadata()
    notes_dict = metadata_['notes_dict_']
    project_element = projectMaster.query.get(int(proj_id))
    address_c, address_e, eng_a, eng_c = getEngAddrProject(project_element)
    if address_c != None:
        output_notes_dict = notes_dict_reorder(notes_dict, address_c.address.company.name, address_c.address.address)
        output_notes_dict_e = notes_dict_reorder(notes_dict, address_e.address.company.name, address_e.address.address)
        eng_a_id = eng_a.engineer.id
        eng_c_id = eng_c.engineer.id
    else:
        output_notes_dict = notes_dict
        output_notes_dict_e = notes_dict
        eng_a_id = None
        eng_c_id = None
    if request.method == "POST":
        data = request.form.to_dict(flat=False)
        a = jsonify(data).json
        a_eng = a.pop('aEng')
        c_eng = a.pop('cEng')
        c_name_c = a.pop('cname')
        c_name_e = a.pop('cnameE')
        address_c_ = a.pop('address')
        address_e_ = a.pop('addressE')
        industry = a.pop('industry')
        region = a.pop('region')
        # Convert date to datetime
        a['bidDueDate'][0] = datetime.datetime.strptime(a['bidDueDate'][0], '%Y-%m-%d')
        a['enquiryReceivedDate'][0] = datetime.datetime.strptime(a['enquiryReceivedDate'][0], '%Y-%m-%d')
        a['receiptDate'][0] = datetime.datetime.strptime(a['receiptDate'][0], '%Y-%m-%d')
        a['industry'] = [getDBElementWithId(industryMaster, industry[0])]
        a['region'] = [getDBElementWithId(regionMaster, region[0])]
        update_dict = a
        project_element.update(update_dict, project_element.id)
        industr_ = getDBElementWithId(industryMaster, industry[0])
        region_ = getDBElementWithId(regionMaster, region[0])
        # project_element.industry = industr_
        # project_element.region = region_
        # db.session.commit()
        addProjectRels(c_name_c[0], c_name_e[0], address_c_[0], address_e_[0], a_eng[0], c_eng[0], project_element,
                       'update')
        return redirect(url_for('editProject', proj_id=proj_id, item_id=item_id))
    return render_template('editproject.html', dropdown=json.dumps(output_notes_dict),
                           dropdown2=json.dumps(output_notes_dict_e), metadata=metadata_, user=current_user,
                           item=getDBElementWithId(itemMaster, item_id), project=project_element, eng_a=eng_a_id,
                           eng_c=eng_c_id, page='editProject')


# Valve Details Module
@app.route('/valve-data/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def valveData(proj_id, item_id):
    metadata_ = metadata()
    valve_element = db.session.query(valveDetailsMaster).filter_by(
        item=getDBElementWithId(itemMaster, int(item_id))).first()
    if request.method == "POST":
        data = request.form.to_dict(flat=False)
        a = jsonify(data).json
        # Changing string to db element to input into update method into db table
        balanceSeal_ = a['balanceseal'][0]
        a['balanceSeal__'] = [getDBElementWithId(balanceSeal, balanceSeal_)]
        bonnetType__ = a['bonnetType__'][0]
        a['bonnetType__'] = [getDBElementWithId(bonnetType, bonnetType__)]
        bonnet__ = a['bonnet__'][0]
        a['bonnet__'] = [getDBElementWithId(bonnet, bonnet__)]
        design = a['design'][0]
        a['design'] = [getDBElementWithId(designStandard, design)]
        endConnection__ = a['endConnection__'][0]
        a['endConnection__'] = [getDBElementWithId(endConnection, endConnection__)]
        endFinish__ = a['endFinish__'][0]
        a['endFinish__'] = [getDBElementWithId(endFinish, endFinish__)]
        flowCharacter__ = a['flowCharacter__'][0]
        a['flowCharacter__'] = [getDBElementWithId(flowCharacter, flowCharacter__)]
        flowDirection__ = a['flowDirection__'][0]
        a['flowDirection__'] = [getDBElementWithId(flowDirection, flowDirection__)]
        gasket__ = a['gasket__'][0]
        a['gasket__'] = [getDBElementWithId(gasket, gasket__)]
        packing__ = a['packing__'][0]
        a['packing__'] = [getDBElementWithId(packing, packing__)]
        studNut__ = a['studNut__'][0]
        a['studNut__'] = [getDBElementWithId(studNut, studNut__)]
        cage__ = a['cage__'][0]
        a['cage__'] = [getDBElementWithId(cageClamp, cage__)]
        packingType__ = a['packingType__'][0]
        a['packingType__'] = [getDBElementWithId(packingType, packingType__)]
        rating = a['rating'][0]
        a['rating'] = [getDBElementWithId(ratingMaster, rating)]
        seatLeakageClass__ = a['seatLeakageClass__'][0]
        a['seatLeakageClass__'] = [getDBElementWithId(seatLeakageClass, seatLeakageClass__)]
        material = a['material'][0]
        a['material'] = [getDBElementWithId(materialMaster, material)]
        a['state'] = [db.session.query(fluidState).filter_by(name='Liquid').first()]

        # Data Type conversion
        try:
            a['maxPressure'][0] = float(a['maxPressure'][0])
            a['maxTemp'][0] = float(a['maxTemp'][0])
            a['minTemp'][0] = float(a['minTemp'][0])
            a['shutOffDelP'][0] = float(a['shutOffDelP'][0])
            a['bonnetExtDimension'][0] = float(a['bonnetExtDimension'][0])
            a['quantity'][0] = int(a['quantity'][0])
        except Exception as e:
            flash(f'Error: {e}')
            pass

        # Adding Data based on Valve style
        style = a['valvestyle'][0]
        a['style'] = [getDBElementWithId(valveStyle, style)]
        if a['style'][0].name in ['Globe Straight', 'Globe Angle']:
            # stem [Shaft], plug [Disc], seat [Seat], trimTypeG [trimType__]
            shaft__ = a['shaft'][0]
            a['shaft__'] = [getDBElementWithId(shaft, shaft__)]
            disc__ = a['plug'][0]
            a['disc__'] = [getDBElementWithId(disc, disc__)]
            seat__ = a['seat'][0]
            a['seat__'] = [getDBElementWithId(seat, seat__)]
            trimType__ = a['trimtypeG'][0]
            a['trimType__'] = [getDBElementWithId(trimType, trimType__)]

            print(shaft__)
        elif a['style'][0].name in ['Butterfly Lugged Wafer', 'Butterfly Double Flanged']:
            # shaft [Shaft], disc [Disc], seal [Seat], trimTypeB [trimType__]
            shaft__ = a['stem'][0]
            a['shaft__'] = [getDBElementWithId(shaft, shaft__)]
            disc__ = a['disc'][0]
            a['disc__'] = [getDBElementWithId(disc, disc__)]
            seat__ = a['seal'][0]
            a['seat__'] = [getDBElementWithId(seat, seat__)]
            trimType__ = a['trimtypeB'][0]
            a['trimType__'] = [getDBElementWithId(trimType, trimType__)]
            print(shaft__)
        else:
            pass

        # remove unwanted keys from a dict
        a.pop('valvestyle')
        a.pop('shaft')
        a.pop('plug')
        a.pop('seat')
        a.pop('trimtypeG')
        a.pop('stem')
        a.pop('disc')
        a.pop('seal')
        a.pop('trimtypeB')
        a.pop('balanceseal')
        # a.pop('shaft')
        print(a['shaft__'][0].name)
        update_dict = a
        valve_element.update(update_dict, valve_element.id)

        return redirect(url_for('valveData', proj_id=proj_id, item_id=item_id))
    return render_template('valvedata.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, valve=valve_element, page='valveData')



# Valve Sizing Module

def power_level_liquid(inletPressure, outletPressure, sGravity, Cv):
    a_ = ((inletPressure - outletPressure) ** 1.5) * Cv
    b_ = sGravity * 2300
    c_ = a_ / b_
    return round(c_, 3)


# TODO - Trim exit velocities and other velocities
def getMultipliers(trimType, numberOfTurns):
    trimDict = {"microspline": 0.7, "Trickle": 0.92, "Contoured": 3.4167, "Cage": 3.2, "MLT": 0.53, "other": 0.7, "1cc": 3, "2cc": 1.8641, "3cc": 1.2548, "4cc": 0.9615, "do": 2.5, "to": 2.5}
    turnsDict = {2: 0.88, 4: 0.9, 6: 0.91, 8: 0.92, 10: 0.93, 12: 0.96, "other": 1}
    try:
        K1 = trimDict[trimType]
        K2 = turnsDict[numberOfTurns]
    except:
        K1 = 1
        K2 = 1

    return K1, K2


def trimExitVelocity(inletPressure, outletPressure, density, trimType, numberOfTurns):
    a_ = math.sqrt(((inletPressure - outletPressure)) / density)
    K1, K2 = getMultipliers(trimType, numberOfTurns)
    print(f"tex values: {inletPressure}, {outletPressure}, {K1}, {density}, {a_}")
    return a_ * K1


# TODO - New Trim Exit velocity formulae
def inletDensity(iPres, MW, R, iTemp):
    a_ = iPres * MW / (R * iTemp)
    return round(a_, 2)

def outletDensity(iPres, oPres, MW, R, iTemp):
    Pi = inletDensity(iPres, MW, R, iTemp)
    a = Pi * (oPres / iPres)
    return round(a, 2)

def tex_new(calculatedCV, ratedCV, port_area, flowrate, iPres, oPres, MW, R, iTemp, fluid_state):
    # density in kg/m3, fl in m3/hr, area in m2
    port_area = port_area * 0.000645
    tex_area = (calculatedCV / ratedCV) * port_area
    tex_vel = flowrate / tex_area
    oDensity = outletDensity(iPres, oPres, MW, R, iTemp)
    ke = (oDensity * tex_vel ** 2) / 19.62
    print(
        f"tex_new inputs: {calculatedCV}, {ratedCV}, {port_area}, {flowrate}, {iPres}, {oPres}, {MW}, {R}, {iTemp}, {fluid_state}, {tex_vel}, {oDensity}, {tex_area}")
    if fluid_state == 'Liquid':
        return round(tex_vel, 3)
    else:
        return round(ke * 0.001422, 3)
    

# getting kc value
def getKCValue(size__, t_type, pressure, v_type, fl):
    with app.app_context():
        kc_dict_1 = [{'v_tye': 'globe', 'size': (1, 4), 'material': '316 SST', 'trim': 'contour', 'pressure': (0, 75),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '316 SST', 'trim': 'contour', 'pressure': (75, 100),
                      'kc_formula': '5'}, {'v_tye': 'globe', 'size': (1, 4), 'material': '316 SST', 'trim': 'contour',
                                           'pressure': (100, 9000), 'kc_formula': '4'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '416 SST', 'trim': 'contour', 'pressure': (0, 75),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '416 SST', 'trim': 'contour', 'pressure': (75, 100),
                      'kc_formula': '5'}, {'v_tye': 'globe', 'size': (1, 4), 'material': '416 SST', 'trim': 'contour',
                                           'pressure': (100, 9000), 'kc_formula': '4'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '440C', 'trim': 'contour', 'pressure': (0, 75),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '440C', 'trim': 'contour', 'pressure': (75, 100),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '440C', 'trim': 'contour', 'pressure': (100, 9000),
                      'kc_formula': '4'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '316 / Alloy', 'trim': 'contour',
                      'pressure': (0, 75), 'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '316 / Alloy', 'trim': 'contour',
                      'pressure': (75, 100), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 4), 'material': '316 / Alloy', 'trim': 'contour',
                      'pressure': (100, 9000), 'kc_formula': '4'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '416 SST', 'trim': 'ported', 'pressure': (0, 300),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (1, 2), 'material': '416 SST', 'trim': 'ported',
                                           'pressure': (300, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '440C', 'trim': 'ported', 'pressure': (0, 300),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '440C', 'trim': 'ported', 'pressure': (300, 9000),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '440C', 'trim': 'ported', 'pressure': (0, 200),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '316 / Alloy 6', 'trim': 'ported',
                      'pressure': (0, 300), 'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '317 / Alloy 6', 'trim': 'ported',
                      'pressure': (300, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '318 / Alloy 6', 'trim': 'ported',
                      'pressure': (0, 200), 'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '319 / Alloy 6', 'trim': 'ported',
                      'pressure': (200, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 12), 'material': '316 SST', 'trim': 'ported', 'pressure': (0, 100),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (1, 12), 'material': '316 SST', 'trim': 'ported',
                                           'pressure': (100, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (3, 4), 'material': '416 SST', 'trim': 'ported', 'pressure': (0, 200),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (3, 4), 'material': '416 SST', 'trim': 'ported',
                                           'pressure': (200, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (3, 4), 'material': '440C', 'trim': 'ported', 'pressure': (200, 9000),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (6, 12), 'material': '416 SST', 'trim': 'ported', 'pressure': (0, 100),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (6, 12), 'material': '416 SST', 'trim': 'ported',
                                           'pressure': (100, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (6, 12), 'material': '440C', 'trim': 'ported', 'pressure': (0, 100),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (6, 12), 'material': '440C', 'trim': 'ported', 'pressure': (100, 9000),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (6, 12), 'material': '320 / Alloy 6', 'trim': 'ported',
                      'pressure': (0, 100), 'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (6, 12), 'material': '321 / Alloy 6', 'trim': 'ported',
                      'pressure': (100, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (16, 24), 'material': '416 SST', 'trim': 'ported', 'pressure': (0, 50),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (16, 24), 'material': '416 SST', 'trim': 'ported',
                                           'pressure': (50, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (16, 24), 'material': '440C', 'trim': 'ported', 'pressure': (0, 50),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (16, 24), 'material': '440C', 'trim': 'ported', 'pressure': (50, 9000),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (16, 24), 'material': '322 / Alloy 6', 'trim': 'ported',
                      'pressure': (0, 50), 'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (16, 24), 'material': '323 / Alloy 6', 'trim': 'ported',
                      'pressure': (50, 9000), 'kc_formula': '5'},
                     {'v_tye': 'butterfly', 'size': (2, 4), 'material': '-', 'trim': 'do', 'pressure': (0, 50),
                      'kc_formula': '2'},
                     {'v_tye': 'butterfly', 'size': (2, 4), 'material': '-', 'trim': 'do', 'pressure': (50, 9000),
                      'kc_formula': '3'},
                     {'v_tye': 'butterfly', 'size': (6, 36), 'material': '-', 'trim': 'do', 'pressure': (0, 9000),
                      'kc_formula': '3'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (0, 600),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (600, 9000),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (0, 500),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (500, 1440),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (0, 400),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_1', 'pressure': (400, 1440),
                      'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 2), 'material': '', 'trim': 'cavitrol_3_2', 'pressure': (0, 2160),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (3, 6), 'material': '', 'trim': 'cavitrol_3_2', 'pressure': (0, 1800),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (3, 6), 'material': '', 'trim': 'cavitrol_3_2',
                                           'pressure': (1800, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (8, 24), 'material': '', 'trim': 'cavitrol_3_2', 'pressure': (0, 1200),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (8, 24), 'material': '', 'trim': 'cavitrol_3_2',
                                           'pressure': (1200, 9000), 'kc_formula': '5'},
                     {'v_tye': 'globe', 'size': (1, 24), 'material': '', 'trim': 'cavitrol_3_3', 'pressure': (0, 3000),
                      'kc_formula': '2'},
                     {'v_tye': 'globe', 'size': (1, 12), 'material': '', 'trim': 'cavitrol_3_4', 'pressure': (0, 3000),
                      'kc_formula': '2'}, {'v_tye': 'globe', 'size': (1, 12), 'material': '', 'trim': 'cavitrol_3_4',
                                           'pressure': (3000, 4000), 'kc_formula': '1'}]

        # kc = db.session.query(kcTable).filter(kcTable.min_size <= int(size__), kcTable.max_size >= int(size__),
        #                                       kcTable.trim_type == t_type,
        #                                       kcTable.min_pres <= float(pressure), kcTable.max_pres >= float(pressure),
        #                                       kcTable.valve_style == v_type).first()

        output_list_kc = []
        for kc in kc_dict_1:
            if kc['v_tye'] == v_type and (kc['size'][0] <= size__ <= kc['size'][1]) and (
                    kc['pressure'][0] <= pressure <= kc['pressure'][1]) and kc['trim'] == t_type:
                output_list_kc.append(kc)

        formula_dict = {1: 0.99, 2: 1, 3: 0.5 * fl * fl, 4: 0.85 * fl * fl, 5: fl * fl}
        print(f"output kc list: {output_list_kc}")
        print(v_type, size__, pressure, t_type)

        # print(formula_dict[int(kc.kc_formula)])
        if len(output_list_kc) >= 1:
            a__ = formula_dict[int(output_list_kc[0]['kc_formula'])]
            print(f"kc forumual: {a__}")
        else:
            print("Didn't get KC value")
            a__ = 1

        return round(a__, 3)

def getOutputs(flowrate_form, fl_unit_form, inletPressure_form, iPresUnit_form, outletPressure_form, oPresUnit_form,
               inletTemp_form,
               iTempUnit_form, vaporPressure, vPresUnit_form, specificGravity, viscosity, xt_fl, criticalPressure_form,
               cPresUnit_form,
               inletPipeDia_form, iPipeUnit_form, iSch, outletPipeDia_form, oPipeUnit_form, oSch, densityPipe, sosPipe,
               valveSize_form, vSizeUnit_form,
               seatDia, seatDiaUnit, ratedCV, rw_noise, item_selected, fluidName, valve_element):
    # change into float/ num
    flowrate_form, fl_unit_form, inletPressure_form, iPresUnit_form, outletPressure_form, oPresUnit_form, inletTemp_form, iTempUnit_form, vaporPressure, vPresUnit_form, specificGravity, viscosity, xt_fl, criticalPressure_form, cPresUnit_form, inletPipeDia_form, iPipeUnit_form, iSch, outletPipeDia_form, oPipeUnit_form, oSch, densityPipe, sosPipe, valveSize_form, vSizeUnit_form, seatDia, seatDiaUnit, ratedCV, rw_noise, item_selected = float(
        flowrate_form), fl_unit_form, float(inletPressure_form), iPresUnit_form, float(
        outletPressure_form), oPresUnit_form, float(inletTemp_form), iTempUnit_form, float(
        vaporPressure), vPresUnit_form, float(specificGravity), float(viscosity), float(xt_fl), float(
        criticalPressure_form), cPresUnit_form, float(inletPipeDia_form), iPipeUnit_form, iSch, float(
        outletPipeDia_form), oPipeUnit_form, oSch, float(densityPipe), float(sosPipe), float(
        valveSize_form), vSizeUnit_form, float(seatDia), seatDiaUnit, float(ratedCV), float(rw_noise), item_selected

    # check whether flowrate, pres and l are in correct units
    # 1. flowrate
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    
    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v)).first()

    thickness_pipe = float(i_pipearea_element.thickness)
    print(f"thickness: {thickness_pipe}")
    if fl_unit_form not in ['m3/hr', 'gpm']:
        flowrate_liq = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form,
                                             'm3/hr',
                                             specificGravity * 1000)
        fr_unit = 'm3/hr'
    else:
        fr_unit = fl_unit_form
        flowrate_liq = flowrate_form

    # 2. Pressure
    # A. inletPressure
    if iPresUnit_form not in ['kpa', 'bar', 'psia']:
        inletPressure_liq = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                  'bar', specificGravity * 1000)
        iPres_unit = 'bar'
    else:
        iPres_unit = iPresUnit_form
        inletPressure_liq = inletPressure_form

    # B. outletPressure
    if oPresUnit_form not in ['kpa', 'bar', 'psia']:
        outletPressure_liq = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                   'bar', specificGravity * 1000)
        oPres_unit = 'bar'
    else:
        oPres_unit = oPresUnit_form
        outletPressure_liq = outletPressure_form

    # C. vaporPressure
    if vPresUnit_form not in ['kpa', 'bar', 'psia']:
        vaporPressure = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'bar',
                                              specificGravity * 1000)
        vPres_unit = 'bar'
    else:
        vPres_unit = vPresUnit_form

    # D. Critical Pressure
    if cPresUnit_form not in ['kpa', 'bar', 'psia']:
        criticalPressure_liq = meta_convert_P_T_FR_L('P', criticalPressure_form,
                                                     cPresUnit_form, 'bar',
                                                     specificGravity * 1000)
        cPres_unit = 'bar'
    else:
        cPres_unit = cPresUnit_form
        criticalPressure_liq = criticalPressure_form

    # 3. Length
    if iPipeUnit_form not in ['mm']:
        inletPipeDia_liq = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form,
                                                 'mm',
                                                 specificGravity * 1000) - 2 * thickness_pipe
        iPipe_unit = 'mm'
    else:
        iPipe_unit = iPipeUnit_form
        inletPipeDia_liq = inletPipeDia_form - 2 * thickness_pipe

    if oPipeUnit_form not in ['mm']:
        outletPipeDia_liq = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                                  'mm', specificGravity * 1000) - 2 * thickness_pipe
        oPipe_unit = 'mm'
    else:
        oPipe_unit = oPipeUnit_form
        outletPipeDia_liq = outletPipeDia_form - 2 * thickness_pipe

    if vSizeUnit_form not in ['mm']:
        vSize_liq = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                          'mm', specificGravity * 1000)
        vSize_unit = 'mm'
    else:
        vSize_unit = vSizeUnit_form
        vSize_liq = valveSize_form

    print(f"dia of pipe: {outletPipeDia_liq}, {inletPipeDia_liq}")

    service_conditions_sf = {'flowrate': flowrate_liq, 'flowrate_unit': fr_unit,
                             'iPres': inletPressure_liq, 'oPres': outletPressure_liq,
                             'iPresUnit': iPres_unit,
                             'oPresUnit': oPres_unit, 'temp': inletTemp_form,
                             'temp_unit': iTempUnit_form, 'sGravity': specificGravity,
                             'iPipeDia': inletPipeDia_liq,
                             'oPipeDia': outletPipeDia_liq,
                             'valveDia': vSize_liq, 'iPipeDiaUnit': iPipe_unit,
                             'oPipeDiaUnit': oPipe_unit, 'valveDiaUnit': vSize_unit,
                             'C': 0.075 * vSize_liq * vSize_liq, 'FR': 1, 'vPres': vaporPressure, 'Fl': xt_fl,
                             'Ff': 0.90,
                             'cPres': criticalPressure_liq,
                             'FD': 1, 'viscosity': viscosity}
    print(service_conditions_sf)

    service_conditions_1 = service_conditions_sf
    N1_val = N1[(service_conditions_1['flowrate_unit'], service_conditions_1['iPresUnit'])]
    N2_val = N2[service_conditions_1['valveDiaUnit']]
    N4_val = N4[(service_conditions_1['flowrate_unit'], service_conditions_1['valveDiaUnit'])]

    result_1 = CV(service_conditions_1['flowrate'], service_conditions_1['C'],
                  service_conditions_1['valveDia'],
                  service_conditions_1['iPipeDia'],
                  service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                  service_conditions_1['oPres'],
                  service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                  service_conditions_1['vPres'],
                  service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                  service_conditions_1['viscosity'], thickness_pipe)

    result = CV(service_conditions_1['flowrate'], result_1,
                service_conditions_1['valveDia'],
                service_conditions_1['iPipeDia'],
                service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                service_conditions_1['oPres'],
                service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                service_conditions_1['vPres'],
                service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                service_conditions_1['viscosity'], thickness_pipe)
    ff_liq = FF(service_conditions_1['vPres'], service_conditions_1['cPres'])
    chokedP = delPMax(service_conditions_1['Fl'], ff_liq, service_conditions_1['iPres'],
                      service_conditions_1['vPres'])
    # chokedP = selectDelP(service_conditions_1['Fl'], service_conditions_1['cPres'],
    #                      service_conditions_1['iPres'],
    #                      service_conditions_1['vPres'], service_conditions_1['oPres'])

    # noise and velocities
    # Liquid Noise - need flowrate in kg/s, valves in m, density in kg/m3, pressure in pa
    # convert form data in units of noise formulae
    valveDia_lnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'm', 1000)
    iPipeDia_lnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                            1000)
    oPipeDia_lnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'm',
                                            1000)
    seat_dia_lnoise = meta_convert_P_T_FR_L('L', seatDia, seatDiaUnit, 'm',
                                            1000)
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    
    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                            schedule=iSch).first()

    iPipeSch_lnoise = meta_convert_P_T_FR_L('L', float(i_pipearea_element.thickness),
                                    'mm', 'm', 1000)
    


    
    flowrate_lnoise = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                            specificGravity * 1000) / 3600
    outletPressure_lnoise = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                  'pa', 1000)
    inletPressure_lnoise = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                 'pa', 1000)
    vPres_lnoise = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'pa', 1000)
    # print(f"3 press: {outletPressure_lnoise, inletPressure_lnoise, vPres_lnoise}")
    # service conditions for 4 inch vale with 8 as line size. CVs need to be changed
    sc_liq_sizing = {'valveDia': valveDia_lnoise, 'ratedCV': ratedCV, 'reqCV': result, 'FL': xt_fl,
                     'FD': 0.42,
                     'iPipeDia': iPipeDia_lnoise, 'iPipeUnit': 'm', 'oPipeDia': oPipeDia_lnoise,
                     'oPipeUnit': 'm',
                     'internalPipeDia': oPipeDia_lnoise,
                     'inPipeDiaUnit': 'm', 'pipeWallThickness': iPipeSch_lnoise, 'speedSoundPipe': sosPipe,
                     'speedSoundPipeUnit': 'm/s',
                     'densityPipe': densityPipe, 'densityPipeUnit': 'kg/m3', 'speedSoundAir': 343,
                     'densityAir': 1293,
                     'massFlowRate': flowrate_lnoise, 'massFlowRateUnit': 'kg/s',
                     'iPressure': inletPressure_lnoise,
                     'iPresUnit': 'pa',
                     'oPressure': outletPressure_lnoise,
                     'oPresUnit': 'pa', 'vPressure': vPres_lnoise, 'densityLiq': specificGravity * 1000,
                     'speedSoundLiq': 1400,
                     'rw': rw_noise,
                     'seatDia': seat_dia_lnoise,
                     'fi': 8000}

    sc_1 = sc_liq_sizing
    try:
        summation = Lpe1m(sc_1['fi'], sc_1['FD'], sc_1['reqCV'], sc_1['iPressure'], sc_1['oPressure'],
                          sc_1['vPressure'],
                          sc_1['densityLiq'], sc_1['speedSoundLiq'], sc_1['massFlowRate'], sc_1['rw'],
                          sc_1['FL'],
                          sc_1['seatDia'], sc_1['valveDia'], sc_1['densityPipe'], sc_1['pipeWallThickness'],
                          sc_1['speedSoundPipe'],
                          sc_1['densityAir'], sc_1['internalPipeDia'], sc_1['speedSoundAir'],
                          sc_1['speedSoundPipe'])
    except:
        summation = 56
    # summation = 56

    # Power Level
    outletPressure_p = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                             'psia', specificGravity * 1000)
    inletPressure_p = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                            'psia', specificGravity * 1000)
    pLevel = power_level_liquid(inletPressure_p, outletPressure_p, specificGravity, result)

    # convert flowrate and dias for velocities
    flowrate_v = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                       1000)
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    outletPipeDia_v = round(meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'inch',
                                                  1000))
    vSize_v = round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                          'inch', specificGravity * 1000))

    # convert pressure for tex, p in bar, l in in
    inletPressure_v = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'psia',
                                            1000)
    outletPressure_v = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'psia',
                                             1000)
    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    trimtype = v_det_element.trimType__.name
    if trimtype == 'contour':
        t_caps = 'Contoured'
    elif trimtype == 'ported':
        t_caps = 'Cage'
    else:
        t_caps = trimtype

    # try:
    tEX = trimExitVelocity(inletPressure_v, outletPressure_v, specificGravity, t_caps,
                        'other')
    print("kkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk tex done")
    # except:
    #     tEX = 0
    flow_character = v_det_element.flowCharacter__.name.lower()
    # new trim exit velocity
    # for port area, travel filter not implemented
    try:
        port_area_ = db.session.query(portArea).filter_by(v_size=vSize_v, seat_bore=seatDia, trim_type=trimtype,
                                                      flow_char=flow_character).first()
    except:
        port_area_ = None

    if port_area_:
        port_area = float(port_area_.area)
    else:
        port_area = 1
    tex_ = tex_new(result, ratedCV, port_area, flowrate_v / 3600, inletPressure_form, inletPressure_form, 1, 8314,
                   inletTemp_form, 'Liquid')

    # ipipeSch_v = meta_convert_P_T_FR_L('L', float(iPipeSch_form), iPipeSchUnit_form,
    #                                    'inch',
    #                                    1000)
    # opipeSch_v = meta_convert_P_T_FR_L('L', float(oPipeSch_form), oPipeSchUnit_form,
    #                                    'inch',
    #                                    1000)
    # iVelocity, oVelocity, pVelocity = getVelocity(flowrate_v, inletPipeDia_v,
    #                                               outletPipeDia_v,
    #                                               vSize_v)
    # print(flowrate_v, (inletPipeDia_v - ipipeSch_v),
    #       (outletPipeDia_v - opipeSch_v),
    #       vSize_v)
    try:
        i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                                    schedule=iSch).first()
    except:
        i_pipearea_elements = pipeArea.query.all()
        i_pipearea_element = i_pipearea_elements[0]
    area_in2 = float(i_pipearea_element.area)
    a_i = 0.00064516 * area_in2
    iVelocity = flowrate_v / (3600 * a_i)

    o_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(outletPipeDia_v),
                                                            schedule=oSch).first()
    print(f"oPipedia: {outletPipeDia_v}, sch: {oSch}")
    area_in22 = float(o_pipearea_element.area)
    a_o = 0.00064516 * area_in22
    oVelocity = flowrate_v / (3600 * a_o)
    

    valve_element_current = valve_element
    rating_current = valve_element_current.rating
    valvearea_element = db.session.query(valveArea).filter_by(rating=rating_current.name[5:],
                                                              nominalPipeSize=vSize_v).first()
    if valvearea_element:
        v_area_in = float(valvearea_element.area)
        v_area = 0.00064516 * v_area_in
    else:
        v_area = 0.00064516 * 1
    pVelocity = flowrate_v / (3600 * v_area)

    data = {'cv': round(result, 3),
            'percent': 80,
            'spl': round(summation, 3),
            'iVelocity': iVelocity,
            'oVelocity': round(oVelocity, 3), 'pVelocity': round(pVelocity, 3), 'choked': round(chokedP, 3),
            'texVelocity': round(tEX, 3)}

    units_string = f"{seatDia}+{seatDiaUnit}+{sosPipe}+{densityPipe}+{rw_noise}+{fl_unit_form}+{iPresUnit_form}+{oPresUnit_form}+{vPresUnit_form}+{cPresUnit_form}+{iPipeUnit_form}+{oPipeUnit_form}+{vSizeUnit_form}+mm+mm+{iTempUnit_form}+sg"
    # update valve size in item
    size_in_in = int(round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'inch', 1000)))
    size_id = db.session.query(cvTable).filter_by(valveSize=size_in_in).first()
    print(size_id)
    item_selected.size = size_id
    # load case data with item ID
    # get valvetype - kc requirements
    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    valve_type_ = v_det_element.style.name
    trimtype = v_det_element.trimType__.name
    outletPressure_psia = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                'psia', 1000)
    inletPressure_psia = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                               'psia', 1000)
    dp_kc = inletPressure_psia - outletPressure_psia

    print(f"kc inputs: {size_in_in}, {trimtype}, {dp_kc}, {valve_type_.lower()}, {xt_fl},")
    Kc = getKCValue(size_in_in, trimtype, dp_kc, valve_type_.lower(), xt_fl)
    print(f"kc inputs: {size_in_in}, {trimtype}, {dp_kc}, {valve_type_.lower()}, {xt_fl}, {Kc}")

    # get other req values - Ff, Kc, Fd, Flp, Reynolds Number
    Ff_liq = round(FF(service_conditions_1['vPres'], service_conditions_1['cPres']), 2)
    Fd_liq = service_conditions_1['FD']
    FLP_liq = flP(result_1, service_conditions_1['valveDia'],
                  service_conditions_1['iPipeDia'], N2_val,
                  service_conditions_1['Fl'])
    RE_number = reynoldsNumber(N4_val, service_conditions_1['FD'], service_conditions_1['flowrate'],
                               service_conditions_1['viscosity'], service_conditions_1['Fl'], N2_val,
                               service_conditions_1['iPipeDia'], N1_val, service_conditions_1['iPres'],
                               service_conditions_1['oPres'],
                               service_conditions_1['sGravity'])
    fp_liq = fP(result_1, service_conditions_1['valveDia'],
                service_conditions_1['iPipeDia'], service_conditions_1['oPipeDia'], N2_val)
    if chokedP == (service_conditions_1['iPres'] - service_conditions_1['oPres']):
        ff = 0.96
    else:
        ff = round(ff_liq, 3)

    vp_ar = meta_convert_P_T_FR_L('P', vaporPressure, vPres_unit, iPresUnit_form, 1000)
    application_ratio = (inletPressure_form - outletPressure_form) / (inletPressure_form - vp_ar)
    print(
        f"AR facts: {inletPressure_form}, {outletPressure_form}, {inletPressure_form}, {vp_ar}, {vaporPressure}, {vPres_unit}")
    other_factors_string = f"{ff}+{Kc}+{Fd_liq}+{FLP_liq}+{RE_number}+{fp_liq}+{round(application_ratio, 3)}+{ratedCV}"

    result_list = [flowrate_form, inletPressure_form, outletPressure_form, inletTemp_form, specificGravity,
                   vaporPressure, viscosity, None,
                   valveSize_form, other_factors_string, round(result, 3), data['percent'],
                   round(summation, 3), round(iVelocity, 3),
                   round(oVelocity, 3), round(pVelocity, 3),
                   round(chokedP, 4), xt_fl, 1, tex_, pLevel, units_string, fluidName, "Liquid",
                   criticalPressure_form, inletPipeDia_form,
                   outletPipeDia_form, iSch, oSch,
                   item_selected]
    
    result_dict = {
        'flowrate': flowrate_form,
        'inletPressure':inletPressure_form,
        'outletPressure': outletPressure_form,
        'inletTemp': inletTemp_form,
        'specificGravity': specificGravity,
        'vaporPressure': vaporPressure,
        'kinematicViscosity': viscosity,
        'valveSize': valveSize_form,
        'fd': Fd_liq,
        'Ff': ff,
        'Fp': fp_liq,
        'Flp': FLP_liq,
        'ratedCv': ratedCV,
        'ar': round(application_ratio, 3),
        'kc': Kc,
        'reNumber': RE_number,
        'calculatedCv': round(result, 3),
        'openingPercentage': data['percent'],
        'spl': round(summation, 3),
        'pipeInVel': round(iVelocity, 3),
        'pipeOutVel': round(oVelocity, 3),
        'valveVel': round(pVelocity, 3),
        'chokedDrop': round(chokedP, 4),
        'fl': xt_fl,
        'tex': tex_,
        'powerLevel': pLevel,
        'seatDia': seatDia,
        'criticalPressure': criticalPressure_form,
        'inletPipeSize': inletPipeDia_form,
        'outletPipeSize': outletPipeDia_form,
        }

    return result_dict


# TODO - GAS SIZING


def x_gas(inletPressure, outletPressure):
    result = (inletPressure - outletPressure) / inletPressure
    # print(f"x value is: {round(result, 2)}")
    return round(result, 3)


def etaB_gas(valveDia, pipeDia):
    result = 1 - ((valveDia / pipeDia) ** 4)
    return round(result, 3)


def eta1_gas(valveDia, pipeDia):
    result = 0.5 * ((1 - ((valveDia / pipeDia) ** 2)) ** 2)
    return round(result, 3)


def eta2_gas(valveDia, pipeDia):
    result = 1 * ((1 - ((valveDia / pipeDia) ** 2)) ** 2)
    return round(result, 3)


def sigmaEta_gas(valveDia, inletDia, outletDia):
    result = eta1_gas(valveDia, inletDia) + eta2_gas(valveDia, outletDia) + etaB_gas(valveDia, inletDia) - etaB_gas(
        valveDia, outletDia)
    return round(result, 3)


def fP_gas(C, valveDia, inletDia, outletDia, N2_value):
    a = (sigmaEta_gas(valveDia, inletDia, outletDia) / N2_value) * ((C / valveDia ** 2) ** 2)
    # print(f"N2: {N2_value}, sigmaeta: {sigmaEta_gas(valveDia, inletDia, outletDia)}")
    result = 1 / math.sqrt(1 + a)
    # print(f"FP value is: {round(result, 2)}")
    return round(result, 2)


# specific heat ratio - gamma
def F_Gamma_gas(gamma):
    result = gamma / 1.4
    # print(f"F-Gamma: {round(result, 5)}")
    return round(result, 5)


def xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value):
    f_gamma = F_Gamma_gas(gamma)
    if valveDia != inletDia:
        fp = fP_gas(C, valveDia, inletDia, outletDia, N2_value)
        etaI = eta1_gas(valveDia, inletDia) + etaB_gas(valveDia, inletDia)
        # print(f"etaI: {round(etaI, 2)}")
        a_ = xT / fp ** 2
        b_ = (xT * etaI * C * C) / (N5_in * (valveDia ** 4))
        xTP = a_ / (1 + b_)
        result = f_gamma * xTP
        # print(f"xChoked1: {round(result, 2)}")
    else:
        result = f_gamma * xT
        # print(f"xChoked2: {round(result, 3)}")
    return round(result, 4)


def xSizing_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value):
    result = min(xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value),
                 x_gas(inletPressure, outletPressure))
    # print(f"xSizing: {round(result, 3)}")
    return round(result, 3)


def xTP_gas(xT, C, valveDia, inletDia, outletDia, N2_value):
    etaI = eta1_gas(valveDia, inletDia) + etaB_gas(valveDia, inletDia)
    fp = fP_gas(C, valveDia, inletDia, outletDia, N2_value)
    a_ = xT / fp ** 2
    b_ = xT * etaI * C * C / (N5_in * (valveDia ** 4))
    result = a_ / (1 + b_)
    return round(result, 3)


Cv_globe_4 = [17, 24, 34, 47, 65, 88, 134, 166, 187, 201, 20000000]
Fl_globle_4 = [0.93, 0.9275, 0.92, 0.91, 0.905, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9]

Cv_butterfly_6 = [56, 126, 204, 306, 425, 556, 671, 717, 698, 200000]
Fl_butterfly_6 = [0.97, 0.95, 0.92, 0.9, 0.88, 0.83, 0.79, 0.72, 0.7, 0.67]

Opening = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 100]

Cv1 = Cv_butterfly_6
FL1 = Fl_butterfly_6

def getFL(C):
    a = 0
    while True:
        # print(f"Cv1, C: {Cv1[a], C}")
        if Cv1[a] == C:
            return FL1[a]
        elif Cv1[a] > C:
            break
        else:
            a += 1

    Fllll = FL1[a - 1] - (((Cv1[a - 1] - C) / (Cv1[a - 1] - Cv1[a])) * (FL1[a - 1] - FL1[a]))

    return round(Fllll, 3)

def fLP(C, valveDia, inletDia):
    FL_input = getFL(C)
    a = (FL_input * FL_input / 0.00214) * (eta1(valveDia, inletDia) + etaB(valveDia, inletDia)) * (
            (C / (valveDia * valveDia)) ** 2)
    try:
        output = FL_input / (math.sqrt(1 + a))
    except:
        output = 1
    return output

# Expansion factor
def Y_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value):
    f_gamma = F_Gamma_gas(gamma)
    a = 1 - ((xSizing_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value) / (
            3 * xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value))))
    # print(
    #     f"rhs for y: {(xSizing_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value) / (3 * xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value)))}")
    result_ch = min(xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value),
                    x_gas(inletPressure, outletPressure))
    if result_ch == xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value):
        result = (2 / 3)
    else:
        result = a
    # result = a

    # print(f"Y value is: {round(result, 3)}")

    return round(result, 7)




def Cv_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, temp, compressibilityFactor,
           flowRate, sg, sg_, N2_value):
    # sg_ = int(input("Which value do you want to give? \nVolumetric Flow - Specific Gravity (1) \nVolumetric Flow - "
    #                 "Molecular Weight (2)\nMass Flow - Specific Weight (3)\nMass Flow - Molecular Weight (4)\nSelect "
    #                 "1 0r 2 0r 3 or 4: "))

    sg_ = sg_

    # if sg_ == 1:
    #     Gg = int(input("Give value of Gg: "))
    #     sg = 0.6
    # elif sg_ == 2:
    #     M = int(input("Give value of M: "))
    #     sg = M
    # elif sg_ == 3:
    #     gamma_1 = int(input("Give value of Gamma1: "))
    #     sg = gamma_1
    # else:
    #     M = int(input("Give value of M: "))
    #     sg = M

    # sg = 1.0434
    sg = sg

    a_ = inletPressure * fP_gas(C, valveDia, inletDia, outletDia, N2_value) * Y_gas(inletPressure, outletPressure,
                                                                                    gamma, C,
                                                                                    valveDia,
                                                                                    inletDia, outletDia, xT, N2_value)
    b_ = temp * compressibilityFactor
    x_ = x_gas(inletPressure, outletPressure)
    x__ = xSizing_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value)
    print(f'sg_ value: {sg_}')
    if sg_ == 1:
        A = flowRate / (
                N7_60_scfh_psi_F * inletPressure * fP_gas(C, valveDia, inletDia, outletDia, N2_value) * Y_gas(
            inletPressure,
            outletPressure,
            gamma, C,
            valveDia,
            inletDia,
            outletDia,
            xT, N2_value) * math.sqrt(
            x__ / (sg * temp * compressibilityFactor)))
        # return round(A, 3)

    elif sg_ == 2:
        A = flowRate / (N9_O_m3hr_kPa_C * a_ * math.sqrt(x__ / (sg * b_)))
        print('gas sizing eq2 input in m3hr kpa and C:')
        print(flowRate, N9_O_m3hr_kPa_C, a_, x_, x__, sg, temp, compressibilityFactor)
        # return A

    elif sg_ == 3:
        A = flowRate / (
                N6_lbhr_psi_lbft3 * fP_gas(C, valveDia, inletDia, outletDia, N2_value) * Y_gas(inletPressure,
                                                                                               outletPressure,
                                                                                               gamma, C, valveDia,
                                                                                               inletDia, outletDia,
                                                                                               xT,
                                                                                               N2_value) * math.sqrt(
            x__ * sg * inletPressure))
        # return A

    else:
        A = flowRate / (N8_kghr_bar_K * a_ * math.sqrt((x__ * sg) / b_))
        # return A
    fk = F_Gamma_gas(gamma)
    x_choked = xChoked_gas(gamma, C, valveDia, inletDia, outletDia, xT, N2_value)
    y = Y_gas(inletPressure, outletPressure, gamma, C, valveDia, inletDia, outletDia, xT, N2_value)
    xtp = xTP_gas(xT, C, valveDia, inletDia, outletDia, N2_value)
    fp__ = fP_gas(C, valveDia, inletDia, outletDia, N2_value)
    output_list = [round(A, 3), x_, fk, x_choked, y, xT, xtp, fp__]
    return output_list

# flowrate in kg/hr, pressure in pa, density in kg/m3
def power_level_gas(specificHeatRatio, inletPressure, outletPressure, flowrate, density):
    pressureRatio = outletPressure / inletPressure
    specificVolume = 1 / density
    heatRatio = specificHeatRatio / (specificHeatRatio - 1)
    a_ = heatRatio * inletPressure * specificVolume
    b_ = (1 - pressureRatio ** (1 / heatRatio)) * flowrate / 36000000
    c_ = a_ * b_
    return round(c_, 3)



# pressure in psi
def trimExitVelocityGas(inletPressure, outletPressure):
    a__ = (inletPressure - outletPressure) / 0.0214
    a_ = math.sqrt(a__)
    return round(a_, 3)




# Gas sizng outputs
def getOutputsGas(flowrate_form, fl_unit_form, inletPressure_form, iPresUnit_form, outletPressure_form, oPresUnit_form,
                  inletTemp_form,
                  iTempUnit_form, vaporPressure, vPresUnit_form, specificGravity, viscosity, xt_fl,
                  criticalPressure_form,
                  cPresUnit_form,
                  inletPipeDia_form, iPipeUnit_form, iSch, outletPipeDia_form, oPipeUnit_form, oSch, densityPipe,
                  sosPipe,
                  valveSize_form, vSizeUnit_form,
                  seatDia, seatDiaUnit, ratedCV, rw_noise, item_selected, sg_choice, z_factor, sg_vale, fluidName):
    flowrate_form, fl_unit_form, inletPressure_form, iPresUnit_form, outletPressure_form, oPresUnit_form, inletTemp_form, iTempUnit_form, vaporPressure, vPresUnit_form, specificGravity, viscosity, xt_fl, criticalPressure_form, cPresUnit_form, inletPipeDia_form, iPipeUnit_form, iSch, outletPipeDia_form, oPipeUnit_form, oSch, densityPipe, sosPipe, valveSize_form, vSizeUnit_form, seatDia, seatDiaUnit, ratedCV, rw_noise, item_selected, z_factor, sg_vale = float(
        flowrate_form), fl_unit_form, float(inletPressure_form), iPresUnit_form, float(
        outletPressure_form), oPresUnit_form, float(inletTemp_form), iTempUnit_form, float(
        vaporPressure), vPresUnit_form, float(specificGravity), float(viscosity), float(xt_fl), float(
        criticalPressure_form), cPresUnit_form, float(inletPipeDia_form), iPipeUnit_form, iSch, float(
        outletPipeDia_form), oPipeUnit_form, oSch, float(densityPipe), float(sosPipe), float(
        valveSize_form), vSizeUnit_form, float(seatDia), seatDiaUnit, float(ratedCV), float(
        rw_noise), item_selected, float(z_factor), float(sg_vale)

    fl_unit = fl_unit_form
    if fl_unit in ['m3/hr', 'scfh', 'gpm']:
        fl_bin = 1
    else:
        fl_bin = 2

    sg_unit = sg_choice
    if sg_unit == 'sg':
        sg_bin = 1
    else:
        sg_bin = 2

    def chooses_gas_fun(flunit, sgunit):
        eq_dict = {(1, 1): 1, (1, 2): 2, (2, 1): 3, (2, 2): 4}
        return eq_dict[(flunit, sgunit)]

    sg__ = chooses_gas_fun(fl_bin, sg_bin)

    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))

    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                            schedule=iSch).first()
    thickness_pipe = float(i_pipearea_element.thickness)

    thickness_in = meta_convert_P_T_FR_L('L', thickness_pipe, 'mm', 'inch', 1000)

    if sg__ == 1:
        # to be converted to scfh, psi, R, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'scfh',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'R',
                                          1000)
    elif sg__ == 2:
        # to be converted to m3/hr, kPa, C, in
        # 3. Pressure - 2*thickness_in
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'kpa',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'kpa',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K',
                                          1000)
    elif sg__ == 3:
        # to be converted to lbhr, psi, F, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        # print(iPipeUnit_form)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'lb/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'F',
                                          1000)
    else:
        # to be converted to kg/hr, bar, K, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'bar',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'bar',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K',
                                          1000)

    print(f"dia of pipe: {outletPipeDia}, {inletPipeDia}")

    # python sizing function - gas

    inputDict_4 = {"inletPressure": inletPressure, "outletPressure": outletPressure,
                   "gamma": specificGravity,
                   "C": ratedCV,
                   "valveDia": vSize,
                   "inletDia": inletPipeDia,
                   "outletDia": outletPipeDia, "xT": float(xt_fl),
                   "compressibilityFactor": z_factor,
                   "flowRate": flowrate,
                   "temp": inletTemp, "sg": float(sg_vale), "sg_": sg__}

    print(inputDict_4)

    inputDict = inputDict_4
    N2_val = N2['inch']
    CV__ = Cv_gas(inletPressure=inputDict['inletPressure'], outletPressure=inputDict['outletPressure'],
                  gamma=inputDict['gamma'],
                  C=inputDict['C'], valveDia=inputDict['valveDia'], inletDia=inputDict['inletDia'],
                  outletDia=inputDict['outletDia'], xT=inputDict['xT'],
                  compressibilityFactor=inputDict['compressibilityFactor'],
                  flowRate=inputDict['flowRate'], temp=inputDict['temp'], sg=inputDict['sg'],
                  sg_=inputDict['sg_'], N2_value=N2_val)
    Cv__ = Cv_gas(inletPressure=inputDict['inletPressure'], outletPressure=inputDict['outletPressure'],
                  gamma=inputDict['gamma'],
                  C=CV__[0], valveDia=inputDict['valveDia'], inletDia=inputDict['inletDia'],
                  outletDia=inputDict['outletDia'], xT=inputDict['xT'],
                  compressibilityFactor=inputDict['compressibilityFactor'],
                  flowRate=inputDict['flowRate'], temp=inputDict['temp'], sg=inputDict['sg'],
                  sg_=inputDict['sg_'], N2_value=N2_val)
    Cv1 = Cv__[0]

    xChoked = xChoked_gas(gamma=inputDict['gamma'], C=inputDict['C'], valveDia=inputDict['valveDia'],
                          inletDia=inputDict['inletDia'], outletDia=inputDict['outletDia'],
                          xT=inputDict['xT'], N2_value=N2_val)

    # noise and velocities
    # Liquid Noise - need flowrate in kg/s, valves in m, density in kg/m3, pressure in pa
    inletPressure_gnoise = float(meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                       'pa',
                                                       1000))
    outletPressure_gnoise = float(meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                        'pa',
                                                        1000))
    # vaporPressure_gnoise = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'pa',
    #                                              1000)
    flowrate_gnoise = conver_FR_noise(flowrate_form, fl_unit)
    inletPipeDia_gnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                                specificGravity * 1000)
    outletPipeDia_gnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, iPipeUnit_form,
                                                 'm',
                                                 specificGravity * 1000)
    size_gnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                        'm', specificGravity * 1000)
    seat_dia_gnoise = meta_convert_P_T_FR_L('L', seatDia, seatDiaUnit, 'm',
                                            1000)
    # summation1 = summation(C=113.863, inletPressure=inletPressure_noise, outletPressure=outletPressure_noise, density=specificGravity*1000,
    #                        vaporPressure=vaporPressure_noise,
    #                        speedS=4000, massFlowRate=flowrate_noise, Fd=0.23, densityPipe=7800, speedSinPipe=5000,
    #                        wallThicknessPipe=0.0002, internalPipeDia=inletPipeDia_noise, seatDia=0.1, valveDia=size_noise,
    #                        densityAir=1.293,
    #                        holeDia=0, rW=0.25)

    # molecular weight needs to be made on case to case basis = here we're taking 19.8, but it needs to come from form or table
    mw = float(sg_vale)
    if sg_unit == 'sg':
        mw = 22.4 * float(sg_vale)
    elif sg_unit == 'mw':
        mw = float(sg_vale)

    temp_gnoise = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K', 1000)
    flp = fLP(Cv1, valveSize_form, inletPipeDia_form)
    fp = fP_gas(Cv1, valveSize_form, inletPipeDia_form, outletPipeDia_form, N2_val)
    sigmeta = sigmaEta_gas(valveSize_form, inletPipeDia_form, outletPipeDia_form)
    flowrate_gv = int(flowrate_form) / 3600
    inlet_density = inletDensity(inletPressure_gnoise, mw, 8314, temp_gnoise)
    # print('inlet density input:')
    # print(inletPressure_gnoise, mw, 8314, temp_gnoise)
    if sigmeta == 0:
        sigmeta = 0.86
    sc_initial_1 = {'valveSize': size_gnoise, 'valveOutletDiameter': outletPipeDia_gnoise,
                    'ratedCV': ratedCV,
                    'reqCV': 175,
                    'No': 6,
                    'FLP': flp,
                    'Iw': 0.181, 'valveSizeUnit': 'm', 'IwUnit': 'm', 'A': 0.00137,
                    'xT': float(xt_fl),
                    'iPipeSize': inletPipeDia_gnoise,
                    'oPipeSize': outletPipeDia_gnoise,
                    'tS': 0.008, 'Di': outletPipeDia_gnoise, 'SpeedOfSoundinPipe_Cs': sosPipe,
                    'DensityPipe_Ps': densityPipe,
                    'densityUnit': 'kg/m3',
                    'SpeedOfSoundInAir_Co': 343, 'densityAir_Po': 1.293, 'atmPressure_pa': 101325,
                    'atmPres': 'pa',
                    'stdAtmPres_ps': 101325, 'stdAtmPres': 'pa', 'sigmaEta': sigmeta, 'etaI': 1.2, 'Fp': fp,
                    'massFlowrate': flowrate_gnoise, 'massFlowrateUnit': 'kg/s',
                    'iPres': inletPressure_gnoise, 'iPresUnit': 'pa',
                    'oPres': outletPressure_gnoise, 'oPresUnit': 'pa', 'inletDensity': 5.3,
                    'iAbsTemp': temp_gnoise,
                    'iAbsTempUnit': 'K',
                    'specificHeatRatio_gamma': specificGravity, 'molecularMass': mw, 'mMassUnit': 'kg/kmol',
                    'internalPipeDia': inletPipeDia_gnoise,
                    'aEta': -3.8, 'stp': 0.2, 'R': 8314, 'RUnit': "J/kmol x K", 'fs': 1}

    sc_initial_2 = {'valveSize': size_gnoise, 'valveOutletDiameter': outletPipeDia_gnoise,
                    'ratedCV': ratedCV,
                    'reqCV': Cv1, 'No': 1,
                    'FLP': flp,
                    'Iw': 0.181, 'valveSizeUnit': 'm', 'IwUnit': 'm', 'A': 0.00137,
                    'xT': float(xt_fl),
                    'iPipeSize': inletPipeDia_gnoise,
                    'oPipeSize': outletPipeDia_gnoise,
                    'tS': 0.008, 'Di': inletPipeDia_gnoise, 'SpeedOfSoundinPipe_Cs': sosPipe,
                    'DensityPipe_Ps': densityPipe,
                    'densityUnit': 'kg/m3',
                    'SpeedOfSoundInAir_Co': 343, 'densityAir_Po': 1.293, 'atmPressure_pa': 101325,
                    'atmPres': 'pa',
                    'stdAtmPres_ps': 101325, 'stdAtmPres': 'pa', 'sigmaEta': sigmeta, 'etaI': 1.2,
                    'Fp': 0.98,
                    'massFlowrate': flowrate_gv, 'massFlowrateUnit': 'kg/s', 'iPres': inletPressure_gnoise,
                    'iPresUnit': 'pa',
                    'oPres': outletPressure_gnoise, 'oPresUnit': 'pa', 'inletDensity': inlet_density,
                    'iAbsTemp': temp_gnoise,
                    'iAbsTempUnit': 'K',
                    'specificHeatRatio_gamma': specificGravity, 'molecularMass': mw,
                    'mMassUnit': 'kg/kmol',
                    'internalPipeDia': inletPipeDia_gnoise,
                    'aEta': -3.8, 'stp': 0.2, 'R': 8314, 'RUnit': "J/kmol x K", 'fs': 1}

    sc_initial = sc_initial_2
    # print(sc_initial)

    summation1 = lpae_1m(sc_initial['specificHeatRatio_gamma'], sc_initial['iPres'], sc_initial['oPres'],
                         sc_initial['FLP'],
                         sc_initial['Fp'],
                         sc_initial['inletDensity'], sc_initial['massFlowrate'], sc_initial['aEta'],
                         sc_initial['R'],
                         sc_initial['iAbsTemp'],
                         sc_initial['molecularMass'], sc_initial['oPipeSize'],
                         sc_initial['internalPipeDia'], sc_initial['stp'],
                         sc_initial['No'],
                         sc_initial['A'], sc_initial['Iw'], sc_initial['reqCV'],
                         sc_initial['SpeedOfSoundinPipe_Cs'],
                         sc_initial['SpeedOfSoundInAir_Co'],
                         sc_initial['valveSize'], sc_initial['tS'], sc_initial['fs'],
                         sc_initial['atmPressure_pa'],
                         sc_initial['stdAtmPres_ps'], sc_initial['DensityPipe_Ps'], -3.002)

    print(f"gas summation: {summation1}")
    # summation1 = 97

    # convert flowrate and dias for velocities
    flowrate_v = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                       mw / 22.4)
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    outletPipeDia_v = round(meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'inch',
                                                  1000))

    size_v = round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                         'inch', specificGravity * 1000))

    # get gas velocities
    inletPressure_gv = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                             1000)
    outletPressure_gv = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'pa',
                                              1000)
    flowrate_gv = flowrate_form / 3600
    print(f'flowrate_gv: {flowrate_gv}')
    inletPipeDia_gnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                                specificGravity * 1000)
    outletPipeDia_gnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, iPipeUnit_form,
                                                 'm',
                                                 specificGravity * 1000)
    size_gnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                        'm', specificGravity * 1000)
    temp_gnoise = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K', 1000)

    gas_vels = getGasVelocities(sc_initial['specificHeatRatio_gamma'], inletPressure_gv, outletPressure_gv,
                                8314, temp_gnoise, mw, flowrate_gv,
                                size_gnoise, inletPipeDia_gnoise, outletPipeDia_gnoise)

    # Power Level
    # getting fr in lb/s
    flowrate_p = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                       specificGravity * 1000)
    inletPressure_p = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                            1000)
    outletPressure_p = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                             'pa',
                                             1000)
    pLevel = power_level_gas(specificGravity, inletPressure_p, outletPressure_p, flowrate_p, gas_vels[9])

    # print(sc_initial['specificHeatRatio_gamma'], inletPressure_gv, outletPressure_gv, 8314,
    #       temp_gnoise, mw, flowrate_gv, size_gnoise,
    #       inletPipeDia_gnoise, outletPipeDia_gnoise)

    # convert pressure for tex, p in bar, l in in
    inletPressure_v = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                            1000)
    outletPressure_v = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'pa',
                                             1000)
    # get tex pressure in psi
    inletPressure_tex = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'psia',
                                              1000)
    outletPressure_tex = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'psia',
                                               1000)

    tEX = trimExitVelocityGas(inletPressure_tex, outletPressure_tex) / 3.281
    print(
        f"tex: {tEX}, {inletPressure_tex}, {outletPressure_tex}, {inletPressure_tex - outletPressure_tex}")
    # print(summation1)
    iVelocity = gas_vels[6]
    oVelocity = gas_vels[7]
    pVelocity = gas_vels[8]

    data = {'cv': round(Cv1, 3),
            'percent': 83,
            'spl': round(summation1, 3),
            'iVelocity': round(iVelocity, 3),
            'oVelocity': round(oVelocity, 3), 'pVelocity': round(pVelocity, 3), 'choked': round(xChoked, 4),
            'texVelocity': round(tEX, 3)}

    units_string = f"{seatDia}+{seatDiaUnit}+{sosPipe}+{densityPipe}+{z_factor}+{fl_unit_form}+{iPresUnit_form}+{oPresUnit_form}+{oPresUnit_form}+{oPresUnit_form}+{iPipeUnit_form}+{oPipeUnit_form}+{vSizeUnit_form}+mm+mm+{iTempUnit_form}+{sg_choice}"
    # update valve size in item
    size_in_in = int(round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'inch', 1000)))
    size_id = db.session.query(cvTable).filter_by(valveSize=size_in_in).first()
    # print(size_id)
    item_selected.size = size_id
    # load case data with item ID
    # get valvetype - kc requirements
    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    valve_type_ = v_det_element.style.name
    trimtype = v_det_element.trimType__.name
    outletPressure_psia = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                'psia', 1000)
    inletPressure_psia = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                               'psia', 1000)
    dp_kc = inletPressure_psia - outletPressure_psia
    Kc = getKCValue(size_in_in, trimtype, dp_kc, valve_type_.lower(), xt_fl)

    # get other req values - Ff, Kc, Fd, Flp, Reynolds Number
    Ff_gas = 0.96
    Fd_gas = 1
    xtp = xTP_gas(inputDict['xT'], inputDict['C'], inputDict['valveDia'], inputDict['inletDia'],
                  inputDict['outletDia'], N2_val)
    N1_val = 0.865
    N4_val = 76000
    inletPressure_re = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'bar',
                                             1000)
    outletPressure_re = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'bar',
                                              1000)
    inletPipeDia_re = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'mm',
                                                  1000))
    flowrate_re = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                        mw / 22.4)
    RE_number = reynoldsNumber(N4_val, Fd_gas, flowrate_re,
                               1, 0.9, N2_val,
                               inletPipeDia_re, N1_val, inletPressure_re,
                               outletPressure_re,
                               mw / 22400)
    fpgas = fP(inputDict['C'], inputDict['valveDia'], inputDict['inletDia'], inputDict['outletDia'], N2_val)

    mac_sonic_list = [gas_vels[0], gas_vels[1], gas_vels[2],
                      gas_vels[3], gas_vels[4], gas_vels[5], gas_vels[9]]

    vp_ar = meta_convert_P_T_FR_L('P', vaporPressure, iPresUnit_form, iPresUnit_form, 1000)
    application_ratio = (inletPressure_form - outletPressure_form) / (inletPressure_form - vp_ar)
    # other_factors_string = f"{Ff_gas}+{Kc}+{Fd_gas}+{xtp}+{RE_number}+{fpgas}"
    # CV___ = [cv, x_, fk, x_choked, y, xT, xtp, fp__]
    other_factors_string = f"{Cv__[1]}+{Cv__[2]}+{Cv__[3]}+{Cv__[4]}+{Cv__[5]}+{Cv__[6]}+{Cv__[7]}+{Fd_gas}+{RE_number}+{Kc}+{mac_sonic_list[0]}+{mac_sonic_list[1]}+{mac_sonic_list[2]}+{mac_sonic_list[3]}+{mac_sonic_list[4]}+{mac_sonic_list[5]}+{mac_sonic_list[6]}+{round(application_ratio, 3)}+{z_factor}+{ratedCV}"
    # print(other_factors_string)
    valve_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    # tex new
    flow_character = getFlowCharacter(valve_det_element.flowCharacter__.name)
        # new trim exit velocity
        # for port area, travel filter not implemented
    try:
        port_area_ = db.session.query(portArea).filter_by(v_size=size_in_in, seat_bore=seatDia,
                                                        trim_type=trimtype,
                                                        flow_char=flow_character).first()
    except:
        port_area_ = None

    if port_area_:
        port_area = float(port_area_.area)
    else:
        port_area = 1
    tex_ = tex_new(Cv1, ratedCV, port_area, flowrate_re / 3600, inletPressure_v, outletPressure_v, mw,
                   8314, temp_gnoise, 'Gas')

    result_list = [flowrate_form, inletPressure_form, outletPressure_form, inletTemp_form, specificGravity,
                   vaporPressure, viscosity, float(sg_vale), valveSize_form, other_factors_string,
                   round(Cv1, 3), data['percent'], data['spl'], data['iVelocity'], data['oVelocity'],
                   data['pVelocity'], round(data['choked'] * inletPressure_form, 3), float(xt_fl), 1, tex_,
                   pLevel, units_string, fluidName, "Gas", round(criticalPressure_form, 3), inletPipeDia_form,
                   outletPipeDia_form, iSch, oSch, item_selected]
    
    # f"+{Fd_gas}+{RE_number}+{Kc}+{mac_sonic_list[0]}+{mac_sonic_list[1]}+{mac_sonic_list[2]}+{mac_sonic_list[3]}+{mac_sonic_list[4]}+{mac_sonic_list[5]}+{mac_sonic_list[6]}+{round(application_ratio, 3)}+{z_factor}+{ratedCV}"
    
    result_dict = {
        'flowrate': flowrate_form,
        'inletPressure':inletPressure_form,
        'outletPressure': outletPressure_form,
        'inletTemp': inletTemp_form,
        'specificGravity': specificGravity,
        'vaporPressure': vaporPressure,
        'kinematicViscosity': viscosity,
        'molecularWeight': float(sg_vale),
        'valveSize': valveSize_form,
        'fk': Cv__[2],
        'y': Cv__[4],
        'xt': float(xt_fl),
        'xtp': Cv__[6],
        'fd': Fd_gas,
        'Fp': Cv__[7],
        'ratedCv': ratedCV,
        'ar': round(application_ratio, 3),
        'kc': Kc,
        'reNumber': RE_number,
        'calculatedCv': round(Cv1, 3),
        'openingPercentage': data['percent'],
        'spl': data['spl'],
        'pipeInVel': data['iVelocity'],
        'pipeOutVel': data['oVelocity'],
        'valveVel': data['pVelocity'],
        'chokedDrop': round(data['choked'] * inletPressure_form, 3),
        'fl': xt_fl,
        'tex': tex_,
        'powerLevel': pLevel,
        'seatDia': seatDia,
        'criticalPressure': criticalPressure_form,
        'inletPipeSize': inletPipeDia_form,
        'outletPipeSize': outletPipeDia_form,
        'machNoUp': mac_sonic_list[0],
        'machNoDown': mac_sonic_list[1],
        'machNoVel': mac_sonic_list[2],
        'sonicVelUp': mac_sonic_list[3],
        'sonicVelDown': mac_sonic_list[4],
        'sonicVelValve': mac_sonic_list[5],
        'outletDensity': mac_sonic_list[6]
        }

    return result_dict


@app.route('/update_fluidState/proj-<proj_id>/item-<item_id>/<fs_id>', methods=['GET', 'POST'])
def updateFluidState(proj_id, item_id, fs_id):
    item_selected = getDBElementWithId(itemMaster, item_id)
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    fluid_state = getDBElementWithId(fluidState, fs_id)
    print(fluid_state.name)
    valve_element.state = fluid_state
    db.session.commit()
    return redirect(url_for('valveSizing', item_id=item_id, proj_id=proj_id))


def liqSizing(flowrate_form, specificGravity, inletPressure_form, outletPressure_form, vaporPressure,
              criticalPressure_form, outletPipeDia_form, inletPipeDia_form, valveSize_form, inletTemp_form, ratedCV,
              xt_fl, viscosity, seatDia, seatDiaUnit, sosPipe, densityPipe, rw_noise, item_selected, fl_unit_form,
              iPresUnit_form, oPresUnit_form, vPresUnit_form, cPresUnit_form, iPipeUnit_form, oPipeUnit_form,
              vSizeUnit_form,
              iSch, iPipeSchUnit_form, oSch, oPipeSchUnit_form, iTempUnit_form, open_percent, fd, travel, rated_cv_tex, fluidName, cv_table):
    # check whether flowrate, pres and l are in correct units
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    
    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                            schedule=iSch).first()
    thickness_pipe = float(i_pipearea_element.thickness)
    print(f"thickness: {thickness_pipe}")
    
    # 1. flowrate
    if fl_unit_form not in ['m3/hr', 'gpm']:
        flowrate_liq = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form,
                                             'm3/hr',
                                             specificGravity * 1000)
        fr_unit = 'm3/hr'
    else:
        fr_unit = fl_unit_form
        flowrate_liq = flowrate_form

    # 2. Pressure
    # A. inletPressure
    if iPresUnit_form not in ['kpa', 'bar', 'psia']:
        inletPressure_liq = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                  'bar', specificGravity * 1000)
        iPres_unit = 'bar'
    else:
        iPres_unit = iPresUnit_form
        inletPressure_liq = inletPressure_form

    # B. outletPressure
    if oPresUnit_form not in ['kpa', 'bar', 'psia']:
        outletPressure_liq = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                   'bar', specificGravity * 1000)
        oPres_unit = 'bar'
    else:
        oPres_unit = oPresUnit_form
        outletPressure_liq = outletPressure_form

    # C. vaporPressure
    if vPresUnit_form not in ['kpa', 'bar', 'psia']:
        vaporPressure = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'bar',
                                              specificGravity * 1000)
        vPres_unit = 'bar'
    else:
        vPres_unit = vPresUnit_form

    # D. Critical Pressure
    if cPresUnit_form not in ['kpa', 'bar', 'psia']:
        criticalPressure_liq = meta_convert_P_T_FR_L('P', criticalPressure_form,
                                                     cPresUnit_form, 'bar',
                                                     specificGravity * 1000)
        cPres_unit = 'bar'
    else:
        cPres_unit = cPresUnit_form
        criticalPressure_liq = criticalPressure_form

    # 3. Length
    if iPipeUnit_form not in ['mm']:
        inletPipeDia_liq = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form,
                                                 'mm',
                                                 specificGravity * 1000) - 2 * thickness_pipe
        iPipe_unit = 'mm'
    else:
        iPipe_unit = iPipeUnit_form
        inletPipeDia_liq = inletPipeDia_form - 2 * thickness_pipe

    if oPipeUnit_form not in ['mm']:
        outletPipeDia_liq = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                                  'mm', specificGravity * 1000) - 2 * thickness_pipe
        oPipe_unit = 'mm'
    else:
        oPipe_unit = oPipeUnit_form
        outletPipeDia_liq = outletPipeDia_form - 2 * thickness_pipe

    if vSizeUnit_form not in ['mm']:
        vSize_liq = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                          'mm', specificGravity * 1000)
        vSize_unit = 'mm'
    else:
        vSize_unit = vSizeUnit_form
        vSize_liq = valveSize_form

    print(f"dia of pipe: {outletPipeDia_liq}, {inletPipeDia_liq}")

    service_conditions_sf = {'flowrate': flowrate_liq, 'flowrate_unit': fr_unit,
                             'iPres': inletPressure_liq, 'oPres': outletPressure_liq,
                             'iPresUnit': iPres_unit,
                             'oPresUnit': oPres_unit, 'temp': inletTemp_form,
                             'temp_unit': iTempUnit_form, 'sGravity': specificGravity,
                             'iPipeDia': inletPipeDia_liq,
                             'oPipeDia': outletPipeDia_liq,
                             'valveDia': vSize_liq, 'iPipeDiaUnit': iPipe_unit,
                             'oPipeDiaUnit': oPipe_unit, 'valveDiaUnit': vSize_unit,
                             'C': 0.075 * vSize_liq * vSize_liq, 'FR': 1, 'vPres': vaporPressure, 'Fl': xt_fl,
                             'Ff': 0.90,
                             'cPres': criticalPressure_liq,
                             'FD': fd, 'viscosity': viscosity}

    service_conditions_1 = service_conditions_sf
    N1_val = N1[(service_conditions_1['flowrate_unit'], service_conditions_1['iPresUnit'])]
    N2_val = N2[service_conditions_1['valveDiaUnit']]
    N4_val = N4[(service_conditions_1['flowrate_unit'], service_conditions_1['valveDiaUnit'])]

    result_1 = CV(service_conditions_1['flowrate'], service_conditions_1['C'],
                  service_conditions_1['valveDia'],
                  service_conditions_1['iPipeDia'],
                  service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                  service_conditions_1['oPres'],
                  service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                  service_conditions_1['vPres'],
                  service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                  service_conditions_1['viscosity'], thickness_pipe)

    result = CV(service_conditions_1['flowrate'], result_1,
                service_conditions_1['valveDia'],
                service_conditions_1['iPipeDia'],
                service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                service_conditions_1['oPres'],
                service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                service_conditions_1['vPres'],
                service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                service_conditions_1['viscosity'], thickness_pipe)

    ff_liq = FF(service_conditions_1['vPres'], service_conditions_1['cPres'])
    # if valveSize_form != inletPipeDia_form:
    #     FLP = flP(result, service_conditions_1['valveDia'], service_conditions_1['iPipeDia'], N2_value, service_conditions_1['Fl'])
    #     FP = fP(result, service_conditions_1['valveDia'], service_conditions_1['iPipeDia'], service_conditions_1['oPipeDia'], N2_value)
    #     # print(f"FP: {FP}")
    #     FL = FLP / FP
    # else:
    #     FL = service_conditions_1['Fl']
    chokedP = delPMax(service_conditions_1['Fl'], ff_liq, service_conditions_1['iPres'], service_conditions_1['vPres'])
    print("liq sizing function, delpMax")

    # noise and velocities
    # Liquid Noise - need flowrate in kg/s, valves in m, density in kg/m3, pressure in pa
    # convert form data in units of noise formulae
    valveDia_lnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'm', 1000)
    iPipeDia_lnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                            1000)
    oPipeDia_lnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'm',
                                            1000)
    seat_dia_lnoise = meta_convert_P_T_FR_L('L', seatDia, seatDiaUnit, 'm',
                                            1000)

    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    
    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                            schedule=iSch).first()
# print(f"pipe dia: {inletPipeDia_v}, sch: {iSch}")

    iPipeSch_lnoise = meta_convert_P_T_FR_L('L', float(i_pipearea_element.thickness),
                                            'mm', 'm', 1000)
    
    flowrate_lnoise = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                            specificGravity * 1000) / 3600
    outletPressure_lnoise = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                  'pa', 1000)
    inletPressure_lnoise = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                 'pa', 1000)
    vPres_lnoise = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'pa', 1000)
    # print(f"3 press: {outletPressure_lnoise, inletPressure_lnoise, vPres_lnoise}")
    # service conditions for 4 inch vale with 8 as line size. CVs need to be changed
    sc_liq_sizing = {'valveDia': valveDia_lnoise, 'ratedCV': ratedCV, 'reqCV': result, 'FL': xt_fl,
                     'FD': fd,
                     'iPipeDia': iPipeDia_lnoise, 'iPipeUnit': 'm', 'oPipeDia': oPipeDia_lnoise,
                     'oPipeUnit': 'm',
                     'internalPipeDia': oPipeDia_lnoise,
                     'inPipeDiaUnit': 'm', 'pipeWallThickness': iPipeSch_lnoise, 'speedSoundPipe': sosPipe,
                     'speedSoundPipeUnit': 'm/s',
                     'densityPipe': densityPipe, 'densityPipeUnit': 'kg/m3', 'speedSoundAir': 343,
                     'densityAir': 1293,
                     'massFlowRate': flowrate_lnoise, 'massFlowRateUnit': 'kg/s',
                     'iPressure': inletPressure_lnoise,
                     'iPresUnit': 'pa',
                     'oPressure': outletPressure_lnoise,
                     'oPresUnit': 'pa', 'vPressure': vPres_lnoise, 'densityLiq': specificGravity * 1000,
                     'speedSoundLiq': 1400,
                     'rw': rw_noise,
                     'seatDia': seat_dia_lnoise,
                     'fi': 8000}

    sc_1 = sc_liq_sizing
    try:
        summation = Lpe1m(sc_1['fi'], sc_1['FD'], sc_1['reqCV'], sc_1['iPressure'], sc_1['oPressure'],
                        sc_1['vPressure'],
                        sc_1['densityLiq'], sc_1['speedSoundLiq'], sc_1['massFlowRate'], sc_1['rw'],
                        sc_1['FL'],
                        sc_1['seatDia'], sc_1['valveDia'], sc_1['densityPipe'], sc_1['pipeWallThickness'],
                        sc_1['speedSoundPipe'],
                        sc_1['densityAir'], sc_1['internalPipeDia'], sc_1['speedSoundAir'],
                        sc_1['speedSoundPipe'])
    except ZeroDivisionError:
        summation = 10
    except ValueError:
        summation = 10
    # summation = 56

    # Power Level
    outletPressure_p = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                             'psia', specificGravity * 1000)
    inletPressure_p = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                            'psia', specificGravity * 1000)
    pLevel = power_level_liquid(inletPressure_p, outletPressure_p, specificGravity, result)

    # convert flowrate and dias for velocities
    flowrate_v = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                       1000)
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    outletPipeDia_v = round(meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'inch',
                                                  1000))
    vSize_v = round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                          'inch', specificGravity * 1000))

    # convert pressure for tex, p in bar, l in inch
    inletPressure_v = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'psia',
                                            1000)
    outletPressure_v = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'psia',
                                             1000)

    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    trimtype = v_det_element.trimType__.name
    
    t_caps = trimtype

    tEX = trimExitVelocity(inletPressure_v, outletPressure_v, specificGravity, t_caps, 'other')

    flow_character = getFlowCharacter(v_det_element.flowCharacter__.name)
    # new trim exit velocity
    # for port area, travel filter not implemented
    # tex new
    if float(travel) in [2, 3, 8]:
        travel = int(travel)
    else:
        travel = float(travel)

    if float(seatDia) in [1, 11, 2, 3, 4, 7, 8]:
        seatDia = int(seatDia)
    else:
        seatDia = float(seatDia)
    try:
        port_area_ = db.session.query(portArea).filter_by(v_size=vSize_v, seat_bore=seatDia, trim_type=trimtype,
                                                        flow_char=flow_character, travel=travel).first()
    except:
        port_area_ = None
    print(f"port area table inputs: {vSize_v}, {seatDia}, {trimtype}, {flow_character}, {travel}")
    if port_area_:
        port_area = float(port_area_.area)
        tex_ = tex_new(result, int(rated_cv_tex), port_area, flowrate_v / 3600, inletPressure_form, inletPressure_form,
                       1, 8314,
                       inletTemp_form, 'Liquid')
    else:
        port_area = 1
        tex_ = None

    # ipipeSch_v = meta_convert_P_T_FR_L('L', float(iPipeSch_form), iPipeSchUnit_form,
    #                                    'inch',
    #                                    1000)
    # opipeSch_v = meta_convert_P_T_FR_L('L', float(oPipeSch_form), oPipeSchUnit_form,
    #                                    'inch',
    #                                    1000)
    # iVelocity, oVelocity, pVelocity = getVelocity(flowrate_v, inletPipeDia_v,
    #                                               outletPipeDia_v,
    #                                               vSize_v)
    # print(flowrate_v, (inletPipeDia_v - ipipeSch_v),
    #       (outletPipeDia_v - opipeSch_v),
    #       vSize_v)
    
    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                                schedule=iSch).first()
    area_in2 = float(i_pipearea_element.area)
    a_i = 0.00064516 * area_in2
    iVelocity = flowrate_v / (3600 * a_i)

    o_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(outletPipeDia_v),
                                                            schedule=oSch).first()
    print(f"oPipedia: {outletPipeDia_v}, sch: {oSch}")
    area_in22 = float(o_pipearea_element.area)
    a_o = 0.00064516 * area_in22
    oVelocity = flowrate_v / (3600 * a_o)
    valve_element_current = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    rating_current = valve_element_current.rating
    valvearea_element = db.session.query(valveArea).filter_by(rating=rating_current.name[5:],
                                                              nominalPipeSize=vSize_v).first()
    if valvearea_element:
        v_area_in = float(valvearea_element.area)
        v_area = 0.00064516 * v_area_in
    else:
        v_area = 0.00064516 * 1
    pVelocity = flowrate_v / (3600 * v_area)

    data = {'cv': round(result, 3),
            'percent': 80,
            'spl': round(summation, 3),
            'iVelocity': iVelocity,
            'oVelocity': round(oVelocity, 3), 'pVelocity': round(pVelocity, 3), 'choked': round(chokedP, 3),
            'texVelocity': round(433.9764, 3)}

    units_string = f"{seatDia}+{seatDiaUnit}+{sosPipe}+{densityPipe}+{rw_noise}+{fl_unit_form}+{iPresUnit_form}+{oPresUnit_form}+{vPresUnit_form}+{cPresUnit_form}+{iPipeUnit_form}+{oPipeUnit_form}+{vSizeUnit_form}+{iPipeSchUnit_form}+{oPipeSchUnit_form}+{iTempUnit_form}+sg"

    # update valve size in item
    size_in_in = int(round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'inch', 1000)))
    size_id = valveSize_form
    print(size_id)
    item_selected.size = size_id
    # load case data with item ID
    # get valvetype - kc requirements
    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    valve_type_ = v_det_element.style.name
    trimtype = v_det_element.trimType__.name
    outletPressure_psia = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                'psia', 1000)
    inletPressure_psia = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                               'psia', 1000)
    dp_kc = inletPressure_psia - outletPressure_psia
    Kc = getKCValue(size_in_in, trimtype, dp_kc, valve_type_.lower(), xt_fl)

    # get other req values - Ff, Kc, Fd, Flp, Reynolds Number
    Ff_liq = round(FF(service_conditions_1['vPres'], service_conditions_1['cPres']), 2)
    N2_fp = N2[vSizeUnit_form]
    Fd_liq = service_conditions_1['FD']
    FLP_liq = flP(result, valveSize_form, inletPipeDia_form, N2_fp,
                  service_conditions_1['Fl'])
    RE_number = reynoldsNumber(N4_val, service_conditions_1['FD'], service_conditions_1['flowrate'],
                               service_conditions_1['viscosity'], service_conditions_1['Fl'], N2_val,
                               service_conditions_1['iPipeDia'], N1_val, service_conditions_1['iPres'],
                               service_conditions_1['oPres'],
                               service_conditions_1['sGravity'])
    fp_liq = fP(result, valveSize_form, inletPipeDia_form,
                outletPipeDia_form, N2_fp)
    if valveSize_form != inletPipeDia_form:
        FL_ = (FLP_liq / fp_liq)
        print(f"FL is flp/fp: {FL_}")
    else:
        FL_ = service_conditions_1['Fl']
        print(f'fl is just fl: {FL_}')
    chokedP = delPMax(FL_, ff_liq, service_conditions_1['iPres'], service_conditions_1['vPres'])
    print(FL_, ff_liq, service_conditions_1['iPres'], service_conditions_1['vPres'], valveSize_form, inletPipeDia_form,
          FLP_liq, fp_liq)
    if chokedP == (service_conditions_1['iPres'] - service_conditions_1['oPres']):
        ff = 0.96
    else:
        ff = round(ff_liq, 3)

    vp_ar = meta_convert_P_T_FR_L('P', vaporPressure, vPres_unit, iPresUnit_form, 1000)
    application_ratio = (inletPressure_form - outletPressure_form) / (inletPressure_form - vp_ar)
    other_factors_string = f"{ff}+{Kc}+{Fd_liq}+{round(FLP_liq, 3)}+{RE_number}+{round(fp_liq, 2)}+{round(application_ratio, 3)}+{rated_cv_tex}"


    result_dict = {
        'flowrate': flowrate_form,
        'inletPressure':inletPressure_form,
        'outletPressure': outletPressure_form,
        'inletTemp': inletTemp_form,
        'specificGravity': specificGravity,
        'vaporPressure': vaporPressure,
        'kinematicViscosity': viscosity,
        'valveSize': valveSize_form,
        'fd': Fd_liq,
        'Ff': ff,
        'Fp': fp_liq,
        'Flp': FLP_liq,
        'ratedCv': ratedCV,
        'ar': round(application_ratio, 3),
        'kc': Kc,
        'reNumber': RE_number,
        'calculatedCv': round(result, 3),
        'openingPercentage': data['percent'],
        'spl': round(summation, 3),
        'pipeInVel': round(iVelocity, 3),
        'pipeOutVel': round(oVelocity, 3),
        'valveVel': round(pVelocity, 3),
        'chokedDrop': round(chokedP, 4),
        'fl': xt_fl,
        'tex': tex_,
        'powerLevel': pLevel,
        'seatDia': seatDia,
        'criticalPressure': criticalPressure_form,
        'inletPipeSize': inletPipeDia_form,
        'outletPipeSize': outletPipeDia_form,
        }

    output = result_dict

    new_case = caseMaster(flowrate=output['flowrate'], inletPressure=output['inletPressure'],
                        outletPressure=output['outletPressure'],
                        inletTemp=output['inletTemp'], specificGravity=output['specificGravity'],
                        vaporPressure=output['vaporPressure'], kinematicViscosity=output['kinematicViscosity'],
                        calculatedCv=output['calculatedCv'], openingPercentage=output['openingPercentage'],
                        valveSize=output['valveSize'], fd=output['fd'], Ff=output['Ff'],
                        Fp=output['Fp'], Flp=output['Flp'], ratedCv=output['ratedCv'], 
                        ar=output['ar'], kc=output['kc'], reNumber=output['reNumber'],
                        spl=output['spl'], pipeInVel=output['pipeInVel'],pipeOutVel=output['pipeOutVel'],
                        chokedDrop=output['chokedDrop'],
                        fl=output['fl'], tex=output['tex'], powerLevel=output['powerLevel'],
                        criticalPressure=output['criticalPressure'], inletPipeSize=output['inletPipeSize'],
                        outletPipeSize=output['outletPipeSize'], item=item_selected, cv=cv_table, iPipe=i_pipearea_element)

    db.session.add(new_case)
    db.session.commit()

    # print(data)
    # print(f"The calculated Cv is: {result}")
    return redirect(url_for('valveSizing', item_id=item_selected.id, proj_id=item_selected.project.id))


def gasSizing(inletPressure_form, outletPressure_form, inletPipeDia_form, outletPipeDia_form, valveSize_form,
              specificGravity, flowrate_form, inletTemp_form, ratedCV, z_factor, vaporPressure, seatDia, seatDiaUnit,
              sosPipe, densityPipe, criticalPressure_form, viscosity, item_selected, fl_unit_form, iPresUnit_form,
              oPresUnit_form, vPresUnit_form, iPipeUnit_form, oPipeUnit_form, vSizeUnit_form, iSch,
              iPipeSchUnit_form, oSch, oPipeSchUnit_form, iTempUnit_form, xt_fl, sg_vale, sg_choice,
              open_percent, fd, travel, rated_cv_tex, fluidName, cv_table):
    # Unit Conversion
    # 1. Flowrate

    # 2. Pressure

    # logic to choose which formula to use - using units of flowrate and sg
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))

    i_pipearea_element = db.session.query(pipeArea).filter_by(nominalPipeSize=float(inletPipeDia_v),
                                                            schedule=iSch).first()
    thickness_pipe = float(i_pipearea_element.thickness)
    thickness_in = meta_convert_P_T_FR_L('L', thickness_pipe, 'mm', 'inch', 1000)
    fl_unit = fl_unit_form
    if fl_unit in ['m3/hr', 'scfh', 'gpm']:
        fl_bin = 1
    else:
        fl_bin = 2

    sg_unit = sg_choice
    if sg_unit == 'sg':
        sg_bin = 1
    else:
        sg_bin = 2

    def chooses_gas_fun(flunit, sgunit):
        eq_dict = {(1, 1): 1, (1, 2): 2, (2, 1): 3, (2, 2): 4}
        return eq_dict[(flunit, sgunit)]

    sg__ = chooses_gas_fun(fl_bin, sg_bin)

    if sg__ == 1:
        # to be converted to scfh, psi, R, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'scfh',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'R',
                                          1000)
    elif sg__ == 2:
        # to be converted to m3/hr, kPa, C, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'kpa',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'kpa',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K',
                                          1000)
    elif sg__ == 3:
        # to be converted to lbhr, psi, F, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        # print(iPipeUnit_form)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'lb/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'F',
                                          1000)
    else:
        # to be converted to kg/hr, bar, K, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'bar',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'bar',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000) - 2 * thickness_in
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000) - 2 * thickness_in
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K',
                                          1000)

    print(f"dia of pipe: {outletPipeDia}, {inletPipeDia}")

    # python sizing function - gas

    inputDict_4 = {"inletPressure": inletPressure, "outletPressure": outletPressure,
                   "gamma": specificGravity,
                   "C": ratedCV,
                   "valveDia": vSize,
                   "inletDia": inletPipeDia,
                   "outletDia": outletPipeDia, "xT": float(xt_fl),
                   "compressibilityFactor": z_factor,
                   "flowRate": flowrate,
                   "temp": inletTemp, "sg": float(sg_vale), "sg_": sg__}

    print(inputDict_4)

    inputDict = inputDict_4
    N2_val = N2['inch']

    CV__ = Cv_gas(inletPressure=inputDict['inletPressure'], outletPressure=inputDict['outletPressure'],
                  gamma=inputDict['gamma'],
                  C=inputDict['C'], valveDia=inputDict['valveDia'], inletDia=inputDict['inletDia'],
                  outletDia=inputDict['outletDia'], xT=inputDict['xT'],
                  compressibilityFactor=inputDict['compressibilityFactor'],
                  flowRate=inputDict['flowRate'], temp=inputDict['temp'], sg=inputDict['sg'],
                  sg_=inputDict['sg_'], N2_value=N2_val)
    Cv__ = Cv_gas(inletPressure=inputDict['inletPressure'], outletPressure=inputDict['outletPressure'],
                  gamma=inputDict['gamma'],
                  C=CV__[0], valveDia=inputDict['valveDia'], inletDia=inputDict['inletDia'],
                  outletDia=inputDict['outletDia'], xT=inputDict['xT'],
                  compressibilityFactor=inputDict['compressibilityFactor'],
                  flowRate=inputDict['flowRate'], temp=inputDict['temp'], sg=inputDict['sg'],
                  sg_=inputDict['sg_'], N2_value=N2_val)
    Cv1 = Cv__[0]

    xChoked = xChoked_gas(gamma=inputDict['gamma'], C=inputDict['C'], valveDia=inputDict['valveDia'],
                          inletDia=inputDict['inletDia'], outletDia=inputDict['outletDia'],
                          xT=inputDict['xT'], N2_value=N2_val)

    # noise and velocities
    # Liquid Noise - need flowrate in kg/s, valves in m, density in kg/m3, pressure in pa
    inletPressure_gnoise = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                 'pa',
                                                 1000)
    outletPressure_gnoise = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                  'pa',
                                                  1000)
    # vaporPressure_gnoise = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'pa',
    #                                              1000)
    flowrate_gnoise = conver_FR_noise(flowrate_form, fl_unit)
    inletPipeDia_gnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                                specificGravity * 1000)
    outletPipeDia_gnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, iPipeUnit_form,
                                                 'm',
                                                 specificGravity * 1000)
    size_gnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                        'm', specificGravity * 1000)
    seat_dia_gnoise = meta_convert_P_T_FR_L('L', seatDia, seatDiaUnit, 'm',
                                            1000)
    mw = float(sg_vale)
    if sg_unit == 'sg':
        mw = 28.96 * float(sg_vale)
    elif sg_unit == 'mw':
        mw = float(sg_vale)

    temp_gnoise = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K', 1000)
    flp = fLP(Cv1, valveSize_form, inletPipeDia_form)
    fp = fP_gas(Cv1, valveSize_form, inletPipeDia_form, outletPipeDia_form, N2_val)
    sigmeta = sigmaEta_gas(valveSize_form, inletPipeDia_form, outletPipeDia_form)
    flowrate_gv = flowrate_form / 3600
    inlet_density = inletDensity(inletPressure_gnoise, mw, 8314, temp_gnoise)
    if sigmeta == 0:
        sigmeta = 0.86
    sc_initial_1 = {'valveSize': size_gnoise, 'valveOutletDiameter': outletPipeDia_gnoise,
                    'ratedCV': ratedCV,
                    'reqCV': 175,
                    'No': 6,
                    'FLP': flp,
                    'Iw': 0.181, 'valveSizeUnit': 'm', 'IwUnit': 'm', 'A': 0.00137,
                    'xT': float(xt_fl),
                    'iPipeSize': inletPipeDia_gnoise,
                    'oPipeSize': outletPipeDia_gnoise,
                    'tS': 0.008, 'Di': outletPipeDia_gnoise, 'SpeedOfSoundinPipe_Cs': sosPipe,
                    'DensityPipe_Ps': densityPipe,
                    'densityUnit': 'kg/m3',
                    'SpeedOfSoundInAir_Co': 343, 'densityAir_Po': 1.293, 'atmPressure_pa': 101325,
                    'atmPres': 'pa',
                    'stdAtmPres_ps': 101325, 'stdAtmPres': 'pa', 'sigmaEta': sigmeta, 'etaI': 1.2, 'Fp': fp,
                    'massFlowrate': flowrate_gnoise, 'massFlowrateUnit': 'kg/s',
                    'iPres': inletPressure_gnoise, 'iPresUnit': 'pa',
                    'oPres': outletPressure_gnoise, 'oPresUnit': 'pa', 'inletDensity': 5.3,
                    'iAbsTemp': temp_gnoise,
                    'iAbsTempUnit': 'K',
                    'specificHeatRatio_gamma': specificGravity, 'molecularMass': mw, 'mMassUnit': 'kg/kmol',
                    'internalPipeDia': inletPipeDia_gnoise,
                    'aEta': -3.8, 'stp': 0.2, 'R': 8314, 'RUnit': "J/kmol x K", 'fs': 1}

    sc_initial_2 = {'valveSize': size_gnoise, 'valveOutletDiameter': outletPipeDia_gnoise,
                    'ratedCV': ratedCV,
                    'reqCV': Cv1, 'No': 1,
                    'FLP': flp,
                    'Iw': 0.181, 'valveSizeUnit': 'm', 'IwUnit': 'm', 'A': 0.00137,
                    'xT': float(xt_fl),
                    'iPipeSize': inletPipeDia_gnoise,
                    'oPipeSize': outletPipeDia_gnoise,
                    'tS': 0.008, 'Di': inletPipeDia_gnoise, 'SpeedOfSoundinPipe_Cs': sosPipe,
                    'DensityPipe_Ps': densityPipe,
                    'densityUnit': 'kg/m3',
                    'SpeedOfSoundInAir_Co': 343, 'densityAir_Po': 1.293, 'atmPressure_pa': 101325,
                    'atmPres': 'pa',
                    'stdAtmPres_ps': 101325, 'stdAtmPres': 'pa', 'sigmaEta': sigmeta, 'etaI': 1.2, 'Fp': 0.98,
                    'massFlowrate': flowrate_gv, 'massFlowrateUnit': 'kg/s', 'iPres': inletPressure_gnoise,
                    'iPresUnit': 'pa',
                    'oPres': outletPressure_gnoise, 'oPresUnit': 'pa', 'inletDensity': inlet_density,
                    'iAbsTemp': temp_gnoise,
                    'iAbsTempUnit': 'K',
                    'specificHeatRatio_gamma': specificGravity, 'molecularMass': mw,
                    'mMassUnit': 'kg/kmol',
                    'internalPipeDia': inletPipeDia_gnoise,
                    'aEta': -3.8, 'stp': 0.2, 'R': 8314, 'RUnit': "J/kmol x K", 'fs': 1}
    # print(sc_initial)
    sc_initial = sc_initial_2

    summation1 = lpae_1m(sc_initial['specificHeatRatio_gamma'], sc_initial['iPres'], sc_initial['oPres'],
                         sc_initial['FLP'],
                         sc_initial['Fp'],
                         sc_initial['inletDensity'], sc_initial['massFlowrate'], sc_initial['aEta'],
                         sc_initial['R'],
                         sc_initial['iAbsTemp'],
                         sc_initial['molecularMass'], sc_initial['oPipeSize'],
                         sc_initial['internalPipeDia'], sc_initial['stp'],
                         sc_initial['No'],
                         sc_initial['A'], sc_initial['Iw'], sc_initial['reqCV'],
                         sc_initial['SpeedOfSoundinPipe_Cs'],
                         sc_initial['SpeedOfSoundInAir_Co'],
                         sc_initial['valveSize'], sc_initial['tS'], sc_initial['fs'],
                         sc_initial['atmPressure_pa'],
                         sc_initial['stdAtmPres_ps'], sc_initial['DensityPipe_Ps'], -3.002)
    print(f'gas summation noise: {summation1}')
    # summation1 = 97

    # convert flowrate and dias for velocities
    flowrate_v = round(meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                             mw / 22.4))
    inletPipeDia_v = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                                 1000))
    outletPipeDia_v = round(meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form, 'inch',
                                                  1000))

    size_v = round(meta_convert_P_T_FR_L('L', valveSize_form, 'inch',
                                         'inch', specificGravity * 1000))
    print(f"vsize_form: {valveSize_form}, vsize_unit: {vSizeUnit_form}")

    # get gas velocities
    inletPressure_gv = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                             1000)
    outletPressure_gv = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'pa',
                                              1000)
    flowrate_gv = flowrate_form / 3600
    print(f'flowrate_gv: {flowrate_gv}')
    inletPipeDia_gnoise = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'm',
                                                specificGravity * 1000)
    outletPipeDia_gnoise = meta_convert_P_T_FR_L('L', outletPipeDia_form, iPipeUnit_form,
                                                 'm',
                                                 specificGravity * 1000)
    size_gnoise = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                        'm', specificGravity * 1000)
    temp_gnoise = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K', 1000)

    gas_vels = getGasVelocities(sc_initial['specificHeatRatio_gamma'], inletPressure_gv, outletPressure_gv, 8314,
                                temp_gnoise, sc_initial['molecularMass'], flowrate_gv, size_gnoise,
                                inletPipeDia_gnoise, outletPipeDia_gnoise)

    # Power Level
    # getting fr in lb/s
    flowrate_p = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                       specificGravity * 1000)
    inletPressure_p = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                            1000)
    outletPressure_p = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                             'pa',
                                             1000)
    pLevel = power_level_gas(specificGravity, inletPressure_p, outletPressure_p, flowrate_p, gas_vels[9])
    print(sc_initial['specificHeatRatio_gamma'], inletPressure_gv, outletPressure_gv, 8314,
          temp_gnoise, sc_initial['molecularMass'], flowrate_gv, size_gnoise,
          inletPipeDia_gnoise, outletPipeDia_gnoise)
    print(f"gas velocities: {gas_vels}")

    # endof get gas

    # convert pressure for tex, p in bar, l in in
    inletPressure_v = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'pa',
                                            1000)
    outletPressure_v = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'pa',
                                             1000)
    # print(f"Outlet Pressure V{outletPressure_v}")

    # get tex pressure in psi
    inletPressure_tex = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'psia',
                                              1000)
    outletPressure_tex = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'psia',
                                               1000)

    tEX = trimExitVelocityGas(inletPressure_tex, outletPressure_tex) / 3.281
    print(f"tex: {tEX}, {inletPressure_tex}, {outletPressure_tex}, {inletPressure_tex - outletPressure_tex}")
    # print(summation1)
    iVelocity = gas_vels[6]
    oVelocity = gas_vels[7]
    pVelocity = gas_vels[8]

    data = {'cv': round(Cv1, 3),
            'percent': 83,
            'spl': round(summation1, 3),
            'iVelocity': round(iVelocity, 3),
            'oVelocity': round(oVelocity, 3), 'pVelocity': round(pVelocity, 3), 'choked': round(xChoked, 4),
            'texVelocity': round(tEX, 3)}

    units_string = f"{seatDia}+{seatDiaUnit}+{sosPipe}+{densityPipe}+{z_factor}+{fl_unit_form}+{iPresUnit_form}+{oPresUnit_form}+{oPresUnit_form}+{oPresUnit_form}+{iPipeUnit_form}+{oPipeUnit_form}+{vSizeUnit_form}+{iPipeSchUnit_form}+{oPipeSchUnit_form}+{iTempUnit_form}+{sg_choice}"
    # change valve in item
    size_in_in = int(round(meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form, 'inch', 1000)))
    size_id = valveSize_form
    print(size_id)
    item_selected.size = size_id
    # load case data with item ID
    # get valvetype - kc requirements
    v_det_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    valve_type_ = v_det_element.style.name
    trimtype = v_det_element.trimType__.name
    outletPressure_psia = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                'psia', 1000)
    inletPressure_psia = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                               'psia', 1000)
    dp_kc = inletPressure_psia - outletPressure_psia
    Kc = getKCValue(size_in_in, trimtype, dp_kc, valve_type_.lower(), xt_fl)

    # get other req values - Ff, Kc, Fd, Flp, Reynolds Number#####
    Ff_gas = 0.96
    Fd_gas = fd
    xtp = xTP_gas(inputDict['xT'], inputDict['C'], inputDict['valveDia'], inputDict['inletDia'], inputDict['outletDia'],
                  N2_val)
    N1_val = 0.865
    N4_val = 76000
    inletPressure_re = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'bar',
                                             1000)
    outletPressure_re = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form, 'bar',
                                              1000)
    inletPipeDia_re = round(meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'mm',
                                                  1000))
    flowrate_re = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                        mw / 22.4)
    RE_number = reynoldsNumber(N4_val, Fd_gas, flowrate_re,
                               1, 0.9, N2_val,
                               inletPipeDia_re, N1_val, inletPressure_re,
                               outletPressure_re,
                               mw / 22400)

    fpgas = fP(inputDict['C'], inputDict['valveDia'], inputDict['inletDia'], inputDict['outletDia'], N2_val)
    if data['choked'] == (inputDict['inletPressure'] - inputDict['outletPressure']):
        ff = 0.96
    else:
        ff = round(Ff_gas, 3)
    mac_sonic_list = [gas_vels[0], gas_vels[1], gas_vels[2],
                      gas_vels[3], gas_vels[4], gas_vels[5], gas_vels[9]]
    other_factors_string = f"{Ff_gas}+{Kc}+{Fd_gas}+{xtp}+{RE_number}+{fpgas}"

    vp_ar = meta_convert_P_T_FR_L('P', vaporPressure, iPresUnit_form, iPresUnit_form, 1000)
    application_ratio = (inletPressure_form - outletPressure_form) / (inletPressure_form - vp_ar)
    other_factors_string = f"{Cv__[1]}+{Cv__[2]}+{Cv__[3]}+{Cv__[4]}+{Cv__[5]}+{Cv__[6]}+{Cv__[7]}+{Fd_gas}+{RE_number}+{Kc}+{mac_sonic_list[0]}+{mac_sonic_list[1]}+{mac_sonic_list[2]}+{mac_sonic_list[3]}+{mac_sonic_list[4]}+{mac_sonic_list[5]}+{mac_sonic_list[6]}+{round(application_ratio, 3)}+{ratedCV}"

    # tex new
    flow_character = getFlowCharacter(v_det_element.flowCharacter__.name)
        # new trim exit velocity
        # for port area, travel filter not implemented

    if float(travel) in [2, 3, 8]:
        travel = int(travel)
    else:
        travel = float(travel)

    if float(seatDia) in [1, 11, 2, 3, 4, 7, 8]:
        seatDia = int(seatDia)
    else:
        seatDia = float(seatDia)
    try:
        port_area_ = db.session.query(portArea).filter_by(v_size=size_in_in, seat_bore=seatDia, trim_type=trimtype,
                                                        flow_char=flow_character, travel=travel).first()
    except:
        port_area_ = None
    print(f'port area inputs: {size_in_in}, {seatDia}, {trimtype}, {flow_character}, {travel}')

    if port_area_:
        port_area = float(port_area_.area)
        tex_ = tex_new(Cv1, int(rated_cv_tex), port_area, flowrate_re / 3600, inletPressure_v, outletPressure_v, mw,
                       8314, temp_gnoise, 'Gas')
    else:
        port_area = 1
        tex_ = None

    result_dict = {
        'fk': Cv__[2],
        'y': Cv__[4],
        'xt': float(xt_fl),
        'xtp': Cv__[6],
        'fd': Fd_gas,
        'Fp': Cv__[7],
        'ratedCv': ratedCV,
        'ar': round(application_ratio, 3),
        'kc': Kc,
        'reNumber': RE_number,
        'calculatedCv': round(Cv1, 3),
        'openingPercentage': data['percent'],
        'spl': data['spl'],
        'pipeInVel': data['iVelocity'],
        'pipeOutVel': data['oVelocity'],
        'valveVel': data['pVelocity'],
        'chokedDrop': round(data['choked'] * inletPressure_form, 3),
        'fl': xt_fl,
        'tex': tex_,
        'powerLevel': pLevel,
        'seatDia': seatDia,
        'criticalPressure': criticalPressure_form,
        'inletPipeSize': inletPipeDia_form,
        'outletPipeSize': outletPipeDia_form,
        'machNoUp': mac_sonic_list[0],
        'machNoDown': mac_sonic_list[1],
        'machNoVel': mac_sonic_list[2],
        'sonicVelUp': mac_sonic_list[3],
        'sonicVelDown': mac_sonic_list[4],
        'sonicVelValve': mac_sonic_list[5],
        'outletDensity': mac_sonic_list[6],
        'x_delp': (inletPressure_form-outletPressure_form)/inletPressure_form
        }

    new_case = caseMaster(flowrate=flowrate_form, inletPressure=inletPressure_form,
                         outletPressure=outletPressure_form,
                         inletTemp=inletTemp_form, specificGravity=specificGravity,
                         vaporPressure=vaporPressure, kinematicViscosity=viscosity,
                         molecularWeight=float(sg_vale), y_expansion=result_dict['y'],
                         calculatedCv=round(Cv1, 3), openingPercentage=round(open_percent),
                         spl=data['spl'], pipeInVel=data['iVelocity'], pipeOutVel=data['oVelocity'],
                         valveVel=data['pVelocity'],
                         chokedDrop=round((data['choked'] * inletPressure_form), 3),
                         xt=float(xt_fl),tex=tex_,
                         powerLevel=pLevel,
                         criticalPressure=round(criticalPressure_form, 3), inletPipeSize=inletPipeDia_form,
                         outletPipeSize=outletPipeDia_form,
                         item=item_selected, fk=result_dict['fk'], xtp=result_dict['xtp'], ratedCv=result_dict['ratedCv'],
                         fd=result_dict['fd'], Fp=result_dict['Fp'], ar=result_dict['ar'], kc=result_dict['kc'], reNumber=result_dict['reNumber'],
                         machNoUp=result_dict['machNoUp'], machNoDown=result_dict['machNoDown'], machNoValve=result_dict['machNoVel'],
                         sonicVelUp=result_dict['sonicVelUp'], sonicVelDown=result_dict['sonicVelDown'],
                         sonicVelValve=result_dict['sonicVelValve'], outletDensity=result_dict['outletDensity'],x_delp=result_dict['x_delp'],
                         cv=cv_table, iPipe=i_pipearea_element)
    db.session.add(new_case)
    db.session.commit()


    return redirect(url_for('valveSizing', item_id=item_selected.id, proj_id=item_selected.project.id))


def getCVresult(fl_unit_form, specificGravity, iPresUnit_form, inletPressure_form, flowrate_form, outletPressure_form,
                oPresUnit_form,
                vPresUnit_form, vaporPressure, cPresUnit_form, criticalPressure_form, inletPipeDia_form, iPipeUnit_form,
                outletPipeDia_form, oPipeUnit_form, valveSize_form, vSizeUnit_form, inletTemp_form, ratedCV, xt_fl, fd,
                viscosity, iTempUnit_form):
    # 1. flowrate
    if fl_unit_form not in ['m3/hr', 'gpm']:
        flowrate_liq = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form,
                                             'm3/hr',
                                             specificGravity * 1000)
        fr_unit = 'm3/hr'
    else:
        fr_unit = fl_unit_form
        flowrate_liq = flowrate_form

    # 2. Pressure
    # A. inletPressure
    if iPresUnit_form not in ['kpa', 'bar', 'psia']:
        inletPressure_liq = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                                  'bar', specificGravity * 1000)
        iPres_unit = 'bar'
    else:
        iPres_unit = iPresUnit_form
        inletPressure_liq = inletPressure_form

    # B. outletPressure
    if oPresUnit_form not in ['kpa', 'bar', 'psia']:
        outletPressure_liq = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                                   'bar', specificGravity * 1000)
        oPres_unit = 'bar'
    else:
        oPres_unit = oPresUnit_form
        outletPressure_liq = outletPressure_form

    # C. vaporPressure
    if vPresUnit_form not in ['kpa', 'bar', 'psia']:
        vaporPressure = meta_convert_P_T_FR_L('P', vaporPressure, vPresUnit_form, 'bar',
                                              specificGravity * 1000)
        vPres_unit = 'bar'
    else:
        vPres_unit = vPresUnit_form

    # D. Critical Pressure
    if cPresUnit_form not in ['kpa', 'bar', 'psia']:
        criticalPressure_liq = meta_convert_P_T_FR_L('P', criticalPressure_form,
                                                     cPresUnit_form, 'bar',
                                                     specificGravity * 1000)
        cPres_unit = 'bar'
    else:
        cPres_unit = cPresUnit_form
        criticalPressure_liq = criticalPressure_form

    # 3. Length
    if iPipeUnit_form not in ['mm']:
        inletPipeDia_liq = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form,
                                                 'mm',
                                                 specificGravity * 1000)
        iPipe_unit = 'mm'
    else:
        iPipe_unit = iPipeUnit_form
        inletPipeDia_liq = inletPipeDia_form

    if oPipeUnit_form not in ['mm']:
        outletPipeDia_liq = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                                  'mm', specificGravity * 1000)
        oPipe_unit = 'mm'
    else:
        oPipe_unit = oPipeUnit_form
        outletPipeDia_liq = outletPipeDia_form

    if vSizeUnit_form not in ['mm']:
        vSize_liq = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                          'mm', specificGravity * 1000)
        vSize_unit = 'mm'
    else:
        vSize_unit = vSizeUnit_form
        vSize_liq = valveSize_form

    service_conditions_sf = {'flowrate': flowrate_liq, 'flowrate_unit': fr_unit,
                             'iPres': inletPressure_liq, 'oPres': outletPressure_liq,
                             'iPresUnit': iPres_unit,
                             'oPresUnit': oPres_unit, 'temp': inletTemp_form,
                             'temp_unit': iTempUnit_form, 'sGravity': specificGravity,
                             'iPipeDia': inletPipeDia_liq,
                             'oPipeDia': outletPipeDia_liq,
                             'valveDia': vSize_liq, 'iPipeDiaUnit': iPipe_unit,
                             'oPipeDiaUnit': oPipe_unit, 'valveDiaUnit': vSize_unit,
                             'C': 0.075 * vSize_liq * vSize_liq, 'FR': 1, 'vPres': vaporPressure, 'Fl': xt_fl,
                             'Ff': 0.90,
                             'cPres': criticalPressure_liq,
                             'FD': fd, 'viscosity': viscosity}

    service_conditions_1 = service_conditions_sf
    N1_val = N1[(service_conditions_1['flowrate_unit'], service_conditions_1['iPresUnit'])]
    N2_val = N2[service_conditions_1['valveDiaUnit']]
    N4_val = N4[(service_conditions_1['flowrate_unit'], service_conditions_1['valveDiaUnit'])]

    result_1 = CV(service_conditions_1['flowrate'], service_conditions_1['C'],
                  service_conditions_1['valveDia'],
                  service_conditions_1['iPipeDia'],
                  service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                  service_conditions_1['oPres'],
                  service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                  service_conditions_1['vPres'],
                  service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                  service_conditions_1['viscosity'], 0)

    result = CV(service_conditions_1['flowrate'], result_1,
                service_conditions_1['valveDia'],
                service_conditions_1['iPipeDia'],
                service_conditions_1['oPipeDia'], N2_val, service_conditions_1['iPres'],
                service_conditions_1['oPres'],
                service_conditions_1['sGravity'], N1_val, service_conditions_1['FD'],
                service_conditions_1['vPres'],
                service_conditions_1['Fl'], service_conditions_1['cPres'], N4_val,
                service_conditions_1['viscosity'], 0)

    return result


def getCVGas(fl_unit_form, specificGravity, sg_choice, inletPressure_form, iPresUnit_form, outletPressure_form,
             oPresUnit_form, valveSize_form, vSizeUnit_form,
             flowrate_form, inletTemp_form, iTempUnit_form, ratedCV, inletPipeDia_form, iPipeUnit_form,
             outletPipeDia_form, oPipeUnit_form, xt_fl, z_factor,
             sg_vale):
    fl_unit = fl_unit_form
    if fl_unit in ['m3/hr', 'scfh', 'gpm']:
        fl_bin = 1
    else:
        fl_bin = 2

    sg_unit = sg_choice
    if sg_unit == 'sg':
        sg_bin = 1
    else:
        sg_bin = 2

    def chooses_gas_fun(flunit, sgunit):
        eq_dict = {(1, 1): 1, (1, 2): 2, (2, 1): 3, (2, 2): 4}
        return eq_dict[(flunit, sgunit)]

    sg__ = chooses_gas_fun(fl_bin, sg_bin)

    if sg__ == 1:
        # to be converted to scfh, psi, R, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000)
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'scfh',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'R',
                                          1000)
    elif sg__ == 2:
        # to be converted to m3/hr, kPa, C, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'kpa',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'kpa',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000)
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'm3/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'C',
                                          1000)
    elif sg__ == 3:
        # to be converted to lbhr, psi, F, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form,
                                              'psia',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'psia',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000)
        # print(iPipeUnit_form)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000)
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'lb/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'F',
                                          1000)
    else:
        # to be converted to kg/hr, bar, K, in
        # 3. Pressure
        inletPressure = meta_convert_P_T_FR_L('P', inletPressure_form, iPresUnit_form, 'bar',
                                              1000)
        outletPressure = meta_convert_P_T_FR_L('P', outletPressure_form, oPresUnit_form,
                                               'bar',
                                               1000)
        # 4. Length
        inletPipeDia = meta_convert_P_T_FR_L('L', inletPipeDia_form, iPipeUnit_form, 'inch',
                                             1000)
        outletPipeDia = meta_convert_P_T_FR_L('L', outletPipeDia_form, oPipeUnit_form,
                                              'inch',
                                              1000)
        vSize = meta_convert_P_T_FR_L('L', valveSize_form, vSizeUnit_form,
                                      'inch', specificGravity * 1000)
        # 1. Flowrate
        flowrate = meta_convert_P_T_FR_L('FR', flowrate_form, fl_unit_form, 'kg/hr',
                                         1000)
        # 2. Temperature
        inletTemp = meta_convert_P_T_FR_L('T', inletTemp_form, iTempUnit_form, 'K',
                                          1000)

    # python sizing function - gas

    inputDict_4 = {"inletPressure": inletPressure, "outletPressure": outletPressure,
                   "gamma": specificGravity,
                   "C": ratedCV,
                   "valveDia": vSize,
                   "inletDia": inletPipeDia,
                   "outletDia": outletPipeDia, "xT": float(xt_fl),
                   "compressibilityFactor": z_factor,
                   "flowRate": flowrate,
                   "temp": inletTemp, "sg": float(sg_vale), "sg_": sg__}

    # print(inputDict_4)

    inputDict = inputDict_4
    N2_val = N2['inch']

    Cv__ = Cv_gas(inletPressure=inputDict['inletPressure'], outletPressure=inputDict['outletPressure'],
                  gamma=inputDict['gamma'],
                  C=inputDict['C'], valveDia=inputDict['valveDia'], inletDia=inputDict['inletDia'],
                  outletDia=inputDict['outletDia'], xT=inputDict['xT'],
                  compressibilityFactor=inputDict['compressibilityFactor'],
                  flowRate=inputDict['flowRate'], temp=inputDict['temp'], sg=inputDict['sg'],
                  sg_=inputDict['sg_'], N2_value=N2_val)
    Cv_gas_final = Cv__[0]
    return Cv_gas_final




@app.route('/valve-sizing/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def valveSizing(proj_id, item_id):
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=getDBElementWithId(itemMaster, int(item_id))).first()
    metadata_ = metadata()
    item_selected = getDBElementWithId(itemMaster, item_id)
    itemCases_1 = db.session.query(caseMaster).filter_by(item=item_selected).all()
    print(len(itemCases_1))
    if request.method =='POST':
        valve_style = getValveType(valve_element.style.name)
        f_state = valve_element.state.name
        data = request.form.to_dict(flat=False)
        a = jsonify(data).json

        fluid_element = getDBElementWithId(fluidProperties, a['fluid_name'][0])
        # RW Noise
        if valve_style == 'globe':
            rw_noise = 0.25
        else:
            rw_noise = 0.5

        if f_state == 'Liquid':
                len_cases_input = len(a['inletPressure'])
                for i in itemCases_1:
                    db.session.delete(i)
                    db.session.commit()
                try:
                    for k in range(len_cases_input):
                        output = getOutputs(a['flowrate'][k], item_selected.project.flowrateUnit, a['inletPressure'][k],
                                            item_selected.project.pressureUnit,
                                            a['outletPressure'][k], item_selected.project.pressureUnit,
                                            a['inletTemp'][k], item_selected.project.temperatureUnit, a['vaporPressure'][k], 
                                            item_selected.project.pressureUnit,
                                            a['specificGravity'][k], a['kinematicViscosity'][k],
                                            a['fl'][k], a['criticalPressure'][0], item_selected.project.pressureUnit, a['inletPipeSize'][0],
                                            item_selected.project.lengthUnit, a['iSch'][0],
                                            a['outletPipeSize'][0], item_selected.project.lengthUnit, a['oSch'][0], 7800,
                                            5000, a['vSize'][0],
                                            item_selected.project.lengthUnit, a['vSize'][0], item_selected.project.lengthUnit, a['ratedCV'][0],
                                            rw_noise, item_selected, fluid_element.fluidName, valve_element)
                        
                        sch_element = db.session.query(pipeArea).filter_by(schedule=a['iSch'][0], nominalPipeSize=float(output['inletPipeSize'])).first()
                        new_case = caseMaster(flowrate=output['flowrate'], inletPressure=output['inletPressure'],
                                                outletPressure=output['outletPressure'],
                                                inletTemp=output['inletTemp'], specificGravity=output['specificGravity'],
                                                vaporPressure=output['vaporPressure'], kinematicViscosity=output['kinematicViscosity'],
                                                calculatedCv=output['calculatedCv'], openingPercentage=output['openingPercentage'],
                                                valveSize=output['valveSize'], fd=output['fd'], Ff=output['Ff'],
                                                Fp=output['Fp'], Flp=output['Flp'], ratedCv=output['ratedCv'], 
                                                ar=output['ar'], kc=output['kc'], reNumber=output['reNumber'],
                                                spl=output['spl'], pipeInVel=output['pipeInVel'],pipeOutVel=output['pipeOutVel'],
                                                chokedDrop=output['chokedDrop'],
                                                fl=output['fl'], tex=output['tex'], powerLevel=output['powerLevel'],
                                                criticalPressure=output['criticalPressure'], inletPipeSize=output['inletPipeSize'],
                                                outletPipeSize=output['outletPipeSize'], item=item_selected, iPipe=sch_element
                                                )
                        
                        
                        db.session.add(new_case)
                        db.session.commit()

                    flash_message = "Calculation Complete"
                    flash_category = "success"
                except ValueError:
                    flash_message = "Data Incomplete"
                    flash_category = "error"

                flash(flash_message, flash_category)
                # print(data)
                print(a)
                # print(f"The calculated Cv is: {result}")
                return redirect(url_for('valveSizing', item_id=item_id, proj_id=proj_id))
        elif f_state == 'Gas':
                # logic to choose which formula to use - using units of flowrate and sg

                len_cases_input = len(a['inletPressure'])
                for i in itemCases_1:
                    db.session.delete(i)
                    db.session.commit()
                
                try:
                    for k in range(len_cases_input):
                        output = getOutputsGas(a['flowrate'][k], item_selected.project.flowrateUnit, a['inletPressure'][k],
                                                item_selected.project.pressureUnit,
                                                a['outletPressure'][k], item_selected.project.pressureUnit,
                                                a['inletTemp'][k], item_selected.project.temperatureUnit, '1', 'pa',
                                                a['specificHeatRatio'][k], '1',
                                                a['xt'][k], a['criticalPressure'][0], item_selected.project.pressureUnit, a['inletPipeSize'][0],
                                                item_selected.project.lengthUnit, a['iSch'][0],
                                                a['outletPipeSize'][0], item_selected.project.lengthUnit, a['oSch'][0], 7800,
                                                5000, a['vSize'][0],
                                                item_selected.project.lengthUnit, a['vSize'][0], item_selected.project.lengthUnit, a['ratedCV'][0],
                                                rw_noise, item_selected, a['mw_sg'][0], a['compressibility'][k], a['molecularWeight'][k], fluid_element.fluidName)
                        sch_element = db.session.query(pipeArea).filter_by(schedule=a['iSch'][0], nominalPipeSize=float(output['inletPipeSize'])).first()
                        new_case = caseMaster(flowrate=output['flowrate'], inletPressure=output['inletPressure'],
                                                outletPressure=output['outletPressure'],
                                                inletTemp=output['inletTemp'], specificGravity=output['specificGravity'],
                                                vaporPressure=output['vaporPressure'], kinematicViscosity=output['kinematicViscosity'], 
                                                molecularWeight=output['molecularWeight'],
                                                valveSize=output['valveSize'],
                                                calculatedCv=output['calculatedCv'], openingPercentage=output['openingPercentage'],
                                                spl=output['spl'],
                                                chokedDrop=output['chokedDrop'], reNumber=output['reNumber'],
                                                xt=output['xt'], tex=output['tex'],
                                                criticalPressure=output['criticalPressure'], inletPipeSize=output['inletPipeSize'],
                                                outletPipeSize=output['outletPipeSize'], powerLevel=output['powerLevel'],
                                                Fp=output['Fp'], fk=output['fk'], y_expansion=output['y'], xtp=output['xtp'],
                                                fd=output['fd'], ratedCv=output['ratedCv'], ar=output['ar'], kc=output['kc'],
                                                pipeInVel=output['pipeInVel'], pipeOutVel=output['pipeOutVel'], valveVel=output['valveVel'],
                                                seatDia=output['seatDia'], machNoUp=output['machNoUp'], machNoDown=output['machNoDown'], machNoValve=output['machNoVel'],
                                                sonicVelUp=output['sonicVelUp'], sonicVelDown=output['sonicVelDown'],
                                                sonicVelValve=output['sonicVelValve'], outletDensity=output['outletDensity'],
                                                item=item_selected, specificHeatRatio=a['specificHeatRatio'][0], compressibility=a['compressibility'][0], iPipe=sch_element)

                        db.session.add(new_case)
                        db.session.commit()
                    flash_message = "Calculation Complete"
                    flash_category = "success"
                except ValueError:
                    flash_message = "Data Incomplete"
                    flash_category = "error"
            
                flash(flash_message, flash_category)
                return redirect(url_for('valveSizing', item_id=item_id, proj_id=proj_id))

        else:
            flash("No Computation for Two-Phase", "error")
            return redirect(url_for('valveSizing', item_id=item_id, proj_id=proj_id))

 
        
        # return f"<p>{a}</p>"
    if valve_element.state.name == 'Liquid':
        html_page = 'valvesizing.html'
    else:
        html_page = 'valvesizinggas.html'
    return render_template(html_page, item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='valveSizing', valve=valve_element, case_length=range(6), cases=itemCases_1)

def interpolate(data, x_db, y_db, vtype):
    x_list = [x_db.one, x_db.two, x_db.three, x_db.four, x_db.five, x_db.six, x_db.seven, x_db.eight, x_db.nine,
              x_db.ten]
    y_list = [y_db.one, y_db.two, y_db.three, y_db.four, y_db.five, y_db.six, y_db.seven, y_db.eight, y_db.nine,
              y_db.ten]
    opening = interpolate_percent(data, x_db, vtype)
    diff = opening - (opening // 10) * 10
    # print(f"FL list: {y_list}")
    if x_list[0] < data < x_list[-1]:
        a = 0
        while True:
            # print(f"Cv1, C: {Cv1[a], C}")
            if x_list == data:
                return y_list[a]
            elif x_list[a] > data:
                break
            else:
                a += 1

        # value_interpolate = y_list[a - 1] - (
        #         ((x_list[a - 1] - data) / (x_list[a - 1] - x_list[a])) * (y_list[a - 1] - y_list[a]))
        if diff >= 5:
            value_interpolate = y_list[a]
        else:
            value_interpolate = y_list[a - 1]

        return round(value_interpolate, 4)
    else:
        return 0.5


def interpolate_fd(data, x_db, y_db, vtype):
    x_list = [x_db.one, x_db.two, x_db.three, x_db.four, x_db.five, x_db.six, x_db.seven, x_db.eight, x_db.nine,
              x_db.ten]
    y_list = [y_db.one, y_db.two, y_db.three, y_db.four, y_db.five, y_db.six, y_db.seven, y_db.eight, y_db.nine,
              y_db.ten]
    # print(f"FL list: {y_list}")

    opening = interpolate_percent(data, x_db, vtype)
    diff = opening - (opening // 10) * 10
    if x_list[0] < data < x_list[-1]:
        a = 0
        while True:
            # print(f"Cv1, C: {Cv1[a], C}")
            if x_list == data:
                return y_list[a]
            elif x_list[a] > data:
                break
            else:
                a += 1

        if diff >= 5:
            value_interpolate = y_list[a]
        else:
            value_interpolate = y_list[a - 1]
        # print(f"fd: {value_interpolate}, a: {a}")
        # print(f"diff:{diff}, opening: {opening}, interpolates: {y_list[a]}, {y_list[a - 1]}")

        return round(value_interpolate, 3)
    else:
        return 0.5


def interpolate_percent(data, x_db, vtype):
    x_list = [x_db.one, x_db.two, x_db.three, x_db.four, x_db.five, x_db.six, x_db.seven, x_db.eight, x_db.nine,
              x_db.ten]
    if vtype.lower() == 'globe':
        y_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    else:
        y_list = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    if x_list[0] < data < x_list[-1]:
        a = 0
        while True:
            # print(f"Cv1, C: {Cv1[a], C}")
            if x_list == data:
                break
            elif x_list[a] > data:
                break
            else:
                a += 1
        # print(f"percentage: {y_list[a - 1]}, a:{a}")

        value_interpolate = y_list[a - 1] - (
                ((x_list[a - 1] - data) / (x_list[a - 1] - x_list[a])) * (y_list[a - 1] - y_list[a]))

        print(y_list[a - 1], x_list[a - 1], x_list[a], y_list[a], data)

        return round(value_interpolate, 3)
    else:
        return 60



@app.route('/select-valve/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def selectValve(proj_id, item_id):
    metadata_ = metadata()
    item_selected = getDBElementWithId(itemMaster, item_id)
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_selected).first()
    cases = db.session.query(caseMaster).filter_by(item=item_selected).all()
    if request.method == "POST":
        if len(cases) > 0:
            if request.form.get('getv'):
                print('post')
                data = request.form.to_dict(flat=False)
                a = jsonify(data).json
                print(a)

                vType = getDBElementWithId(valveStyle, a['style'][0]) 
                trimType_ = getDBElementWithId(trimType, a['trimType'][0])  
                flowChara = getDBElementWithId(flowCharacter, a['flowcharacter'][0])
                flowDirec = getDBElementWithId(flowDirection, a['flowdirection'][0])
                rating_v = getDBElementWithId(ratingMaster, a['rating'][0])

                cv_values = []
                for i in cases:
                    cv_value = i.calculatedCv
                    cv_values.append(cv_value)
                min_cv = min(cv_values)
                max_cv = max(cv_values)

                # update changes in valve details
                valve_element.trimType__ = trimType_
                valve_element.flowCharater__ = flowChara
                valve_element.flowDirection__ = flowDirec
                valve_element.rating = rating_v
                valve_element.style = vType
                db.session.commit()
                return_globe_data = []
                cv__lists = db.session.query(cvTable).filter_by(trimType_=trimType_, flowCharacter_=flowChara, flowDirection_=flowDirec, rating_c=rating_v, style=vType).all()
                
                cv_id_lists = [cv_.id for cv_ in cv__lists]
                cv_lists = cvValues.query.filter(cvValues.cvId.in_(cv_id_lists)).all()
                for i in cv_lists:
                    seat_bore = i.seatBore
                    travel = i.travel
                    i_list = [i.one, i.two, i.three, i.four, i.five, i.six, i.seven,
                                i.eight,
                                i.nine, i.ten, 0.89, travel, seat_bore, i.id, i.cv.valveSize]
                    return_globe_data.append(i_list)
                print(return_globe_data)
                # cv_dummy = last_case.CV
                # print(cv_dummy)
                index_to_remove = []
                for i in return_globe_data:
                    if i[0] < min_cv < i[9]:
                        a = 0
                        while True:
                            if i[a] == min_cv:
                                break
                            elif i[a] > min_cv:
                                break
                            else:
                                a += 1
                        i.append(a)
                        # print(a)
                        # print('CV in Range')
                        # print(i)
                    if i[0] < max_cv < i[9]:
                        b = 0
                        while True:
                            if i[b] == max_cv:
                                break
                            elif i[b] > max_cv:
                                break
                            else:
                                b += 1
                        i.append(b)
                        # print(a)
                        # print('CV in Range')
                        # print(i)
                    else:
                        i.append(10)
                        i.append(10)
                        index_to_remove.append(return_globe_data.index(i))
                        # print(f"Index to remove: {index_to_remove}")
                        # print('CV not in range')
                for i in return_globe_data:
                    if len(i) == 16:
                        index_to_remove.append(return_globe_data.index(i))
                print(f"Index to remove final: {index_to_remove}")
                for ele in sorted(index_to_remove, reverse=True):
                    del return_globe_data[ele]

                print(f'The final return globe is: {return_globe_data}')

                return render_template('selectvalve.html', item=getDBElementWithId(itemMaster, int(item_id)), valve_data=return_globe_data,
                                        page='selectValve',metadata=metadata_, user=current_user, valve=valve_element)
                
            elif request.form.get('select'):
                for last_case in cases:
                    valve_d_id = getDBElementWithId(cvValues, request.form.get('valve'))
                    cv_element = valve_d_id.cv
                    # Adding valve id in new table
                    last_case.cv = valve_d_id.cv
                    db.session.commit()
                    
                    # print(last_case.cv.balancing_.name)
                    valve_style = getValveType(valve_element.style.name)
                    # RW Noise
                    if valve_style == 'globe':
                        rw_noise = 0.25
                    else:
                        rw_noise = 0.5
                    # ## done adding
                    seatDia, seatDiaUnit, sosPipe, densityPipe, rw_noise, fl_unit, iPresUnit, oPresUnit, vPresUnit, cPresUnit, iPipeUnit, oPipeUnit, vSizeUnit, iPipeSchUnit, oPipeSchUnit, iTempUnit, sg_choice = last_case.seatDia, item_selected.project.lengthUnit, 5000, 7800, rw_noise, item_selected.project.flowrateUnit, item_selected.project.pressureUnit, item_selected.project.pressureUnit, item_selected.project.pressureUnit, item_selected.project.pressureUnit, item_selected.project.lengthUnit,item_selected.project.lengthUnit,item_selected.project.lengthUnit,item_selected.project.lengthUnit,item_selected.project.lengthUnit,item_selected.project.temperatureUnit, last_case.mw_sg
                    # select_dict = db.session.query(globeTable).filter_by(id=int(valve_d_id)).first()
                    # select_dict_fl = db.session.query(globeTable).filter_by(id=int(valve_d_id) + 1).first()
                    # select_dict_xt = db.session.query(globeTable).filter_by(id=int(valve_d_id) + 2).first()
                    # select_dict_fd = db.session.query(globeTable).filter_by(id=int(valve_d_id) + 3).first()

                    select_dict = db.session.query(cvValues).filter_by(cv=cv_element, coeff='Cv').first()
                    select_dict_fl = db.session.query(cvValues).filter_by(cv=cv_element, coeff='FL').first()
                    select_dict_xt = db.session.query(cvValues).filter_by(cv=cv_element, coeff='Xt').first()
                    select_dict_fd = db.session.query(cvValues).filter_by(cv=cv_element, coeff='Fd').first()
                    print(select_dict_fl.one)

                    v_size = round(meta_convert_P_T_FR_L('L', cv_element.valveSize, 'inch', 'inch', 1000))
                    # get cv for o_percent
                    # get valveType from valveDetails
                    valve_type_ = valve_element.style.name

                    fl = interpolate(last_case.calculatedCv, select_dict, select_dict_fl, valve_type_)
                    xt = interpolate(last_case.calculatedCv, select_dict, select_dict_xt, valve_type_)
                    fd = interpolate_fd(last_case.calculatedCv, select_dict, select_dict_fd, valve_type_)
                    rated_cv_tex = select_dict.ten
                    if valve_element.state.name == 'Liquid':
                        final_cv = getCVresult(fl_unit, last_case.specificGravity, iPresUnit, last_case.inletPressure,
                                               last_case.flowrate,
                                               last_case.outletPressure,
                                               oPresUnit, vPresUnit, last_case.vaporPressure, cPresUnit,
                                               last_case.criticalPressure,
                                               last_case.inletPipeSize,
                                               iPipeUnit, last_case.outletPipeSize, oPipeUnit, v_size, 'inch',
                                               last_case.inletTemp,
                                               select_dict.ten, fl, fd,
                                               last_case.kinematicViscosity, iTempUnit)
                    else:
                        final_cv = getCVGas(fl_unit, last_case.specificGravity, last_case.mw_sg, last_case.inletPressure, iPresUnit,
                                            last_case.outletPressure, oPresUnit, v_size, 'inch',
                                            last_case.flowrate, last_case.inletTemp, iTempUnit, select_dict.ten,
                                            last_case.inletPipeSize, iPipeUnit, last_case.outletPipeSize, oPipeUnit, xt,
                                            rw_noise,
                                            last_case.molecularWeight)
                    # print(f"last_cv: {final_cv}")
                    fl = interpolate(final_cv, select_dict, select_dict_fl, valve_type_)
                    xt = interpolate(final_cv, select_dict, select_dict_xt, valve_type_)
                    fd = interpolate_fd(final_cv, select_dict, select_dict_fd, valve_type_)

                    if valve_element.state.name == 'Liquid':
                        final_cv1 = getCVresult(fl_unit, last_case.specificGravity, iPresUnit, last_case.inletPressure,
                                               last_case.flowrate,
                                               last_case.outletPressure,
                                               oPresUnit, vPresUnit, last_case.vaporPressure, cPresUnit,
                                               last_case.criticalPressure,
                                               last_case.inletPipeSize,
                                               iPipeUnit, last_case.outletPipeSize, oPipeUnit, v_size, 'inch',
                                               last_case.inletTemp,
                                               select_dict.ten, fl, fd,
                                               last_case.kinematicViscosity, iTempUnit)
                    else:
                        final_cv1 = getCVGas(fl_unit, last_case.specificGravity, last_case.mw_sg, last_case.inletPressure, iPresUnit,
                                            last_case.outletPressure, oPresUnit, v_size, 'inch',
                                            last_case.flowrate, last_case.inletTemp, iTempUnit, select_dict.ten,
                                            last_case.inletPipeSize, iPipeUnit, last_case.outletPipeSize, oPipeUnit, xt,
                                            rw_noise,
                                            last_case.molecularWeight)

                    o_percent = interpolate_percent(final_cv1, select_dict, valve_type_)
                    fl = interpolate(final_cv1, select_dict, select_dict_fl, valve_type_)
                    xt = interpolate(final_cv1, select_dict, select_dict_xt, valve_type_)
                    fd = interpolate_fd(final_cv1, select_dict, select_dict_fd, valve_type_)
                    print('final fl, xt, select dict')
                    print(fl, xt, select_dict_xt.id)

                    seat_bore = valve_d_id.seatBore
                    travel = valve_d_id.travel

                    fluidName_ = ''

                    if valve_element.state.name == 'Liquid':
                        liqSizing(last_case.flowrate, last_case.specificGravity, last_case.inletPressure, last_case.outletPressure,
                                  last_case.vaporPressure, last_case.criticalPressure, last_case.outletPipeSize,
                                  last_case.inletPipeSize,
                                  v_size, last_case.inletTemp, final_cv1, fl,
                                  last_case.kinematicViscosity, seat_bore, 'inch', sosPipe, densityPipe, rw_noise,
                                  item_selected,
                                  fl_unit, iPresUnit, oPresUnit, vPresUnit, cPresUnit, iPipeUnit, oPipeUnit, 'inch',
                                  last_case.iPipe.schedule, iPipeSchUnit, last_case.iPipe.schedule, oPipeSchUnit, iTempUnit,
                                  o_percent, fd, travel, rated_cv_tex, fluidName_, valve_d_id.cv)
                        db.session.delete(last_case)
                        db.session.commit()
                    else:
                        gasSizing(last_case.inletPressure, last_case.outletPressure, last_case.inletPipeSize, last_case.outletPipeSize,
                                  v_size,
                                  last_case.specificGravity, last_case.flowrate, last_case.inletTemp, final_cv1, rw_noise,
                                  last_case.vaporPressure,
                                  seat_bore, 'inch',
                                  sosPipe, densityPipe, last_case.criticalPressure, last_case.kinematicViscosity, item_selected,
                                  fl_unit,
                                  iPresUnit,
                                  oPresUnit, vPresUnit, iPipeUnit, oPipeUnit, 'inch',
                                  last_case.iPipe.schedule,
                                  iPipeSchUnit, last_case.iPipe.schedule, oPipeSchUnit, iTempUnit, xt, last_case.molecularWeight,
                                  sg_choice, o_percent, fd, travel, rated_cv_tex,fluidName_, valve_d_id.cv)

                        db.session.delete(last_case)
                        db.session.commit()

                return redirect(url_for('valveSizing', item_id=item_id, proj_id=proj_id))
        else:
            flash('Add Case to select valve')
            return redirect(url_for('selectValve', item_id=item_id, proj_id=proj_id))
    return render_template('selectvalve.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='selectValve', valve=valve_element, valve_data=[])


# Actuator Sizing
@app.route('/actuator-sizing/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def actuatorSizing(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    act_element = db.session.query(actuatorMaster).filter_by(item=item_element).first()
    metadata_ = metadata()
    if request.method == 'POST':
        actuator_input_dict = {}
        actuator_input_dict['actuatorType'] = [request.form.get('actType')]
        actuator_input_dict['springAction'] = [request.form.get('failAction')]
        actuator_input_dict['handWheel'] = [request.form.get('mount')]
        actuator_input_dict['adjustableTravelStop'] = [request.form.get('travel')]
        actuator_input_dict['orientation'] = [request.form.get('orientation')]
        actuator_input_dict['availableAirSupplyMin'] = [request.form.get('availableAirSupplyMin')]
        actuator_input_dict['availableAirSupplyMax'] = [request.form.get('availableAirSupplyMax')]
        # print(actuator_input_dict)
        if request.form.get('sliding'):
            print('working')
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('slidingStem', item_id=item_id, proj_id=proj_id))
        elif request.form.get('rotary'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('rotaryActuator', item_id=item_id, proj_id=proj_id))
        elif request.form.get('stroketime'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('strokeTime', item_id=item_id, proj_id=proj_id))
        else:
            pass
    return render_template('actuatorSizing.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='actuatorSizing', valve=valve_element, act=act_element)

@app.route('/sliding-stem/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def slidingStem(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    cases = db.session.query(caseMaster).filter_by(item=item_element).all()
    cv_element = db.session.query(cvValues).filter_by(cv=cases[0].cv).first() 

    print(cv_element.seatBore)
    act_element = db.session.query(actuatorMaster).filter_by(item=item_element).first()
    print(len(cases))
    selected_sized_valve_element = cases[0].cv
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    metadata_ = metadata()
    print(selected_sized_valve_element.balancing_.name)
    if request.method == 'POST':
        actuator_input_dict = {}
        actuator_input_dict['actuatorType'] = [request.form.get('actType')]
        actuator_input_dict['springAction'] = [request.form.get('failAction')]
        actuator_input_dict['handWheel'] = [request.form.get('mount')]
        actuator_input_dict['adjustableTravelStop'] = [request.form.get('travel')]
        actuator_input_dict['orientation'] = [request.form.get('orientation')]
        actuator_input_dict['availableAirSupplyMin'] = [request.form.get('availableAirSupplyMin')]
        actuator_input_dict['availableAirSupplyMax'] = [request.form.get('availableAirSupplyMax')]
        # print(actuator_input_dict)
        if request.form.get('sliding'):
            print('working')
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('slidingStem', item_id=item_id, proj_id=proj_id))
        elif request.form.get('rotary'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('rotaryActuator', item_id=item_id, proj_id=proj_id))
        elif request.form.get('stroketime'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('strokeTime', item_id=item_id, proj_id=proj_id))
        elif request.form.get('submit1'):
            plugDia = float(request.form.get('plugDia'))
            stemDia = float(request.form.get('stemDia'))
            ua = float(request.form.get('ua'))
            seatDia = float(request.form.get('seatDia'))
            balance = request.form.get('balance')
            stroke = request.form.get('stroke')
            iPressure = float(request.form.get('iPressure'))
            oPressure = float(request.form.get('oPressure'))
            shutOffDelP = float(request.form.get('shutOffDelP'))
            valve_forces = valveForces(iPressure, oPressure, seatDia, plugDia, stemDia, ua, valve_element.rating.name, 'ptfe1',
                                        valve_element.seatLeakageClass__.name, valve_element.trimType__.name, balance, valve_element.flowDirection__.name, 'shutoff+', shutOffDelP)
            vf_shutoff = valveForces(iPressure, oPressure, seatDia, plugDia, stemDia, ua, valve_element.rating.name, 'ptfe1',
                                        valve_element.seatLeakageClass__.name, valve_element.trimType__.name, balance, valve_element.flowDirection__.name, 'shutoff', shutOffDelP)
            vf_open = valveForces(iPressure, oPressure, seatDia, plugDia, stemDia, ua, valve_element.rating.name, 'ptfe1',
                                        valve_element.seatLeakageClass__.name, valve_element.trimType__.name, balance, valve_element.flowDirection__.name, 'open', shutOffDelP)
            vf_close = valveForces(iPressure, oPressure, seatDia, plugDia, stemDia, ua, valve_element.rating.name, 'ptfe1',
                                        valve_element.seatLeakageClass__.name, valve_element.trimType__.name, balance, valve_element.flowDirection__.name, 'close', shutOffDelP)
            v_shutoff, v_shutoff_plus, v_open, v_close = round(vf_shutoff[0]), round(valve_forces[0]), round(
                vf_open[0]), round(vf_close[0])

            packing_fric = valve_forces[2]
            seatload_fact = valve_forces[3]
            # store data in v_details
            valve_element.valve_size = f"{balance}#{stroke}#{round(seatDia, 3)}#{plugDia}#{stemDia}#{ua}#{v_shutoff}#{v_shutoff_plus}#{v_open}#{v_close}#{packing_fric}#{seatload_fact}"
            db.session.commit()
            v_data = [v_shutoff, v_shutoff_plus, v_open, v_close]
            act_case_data = db.session.query(actuatorCaseData).filter_by(actuator_=act_element).all()
            if len(act_case_data) == 0:
                new_act = actuatorCaseData(actuator_=act_element)
                db.session.add(new_act)
                db.session.commit()
            
            act_case_data_ = db.session.query(actuatorCaseData).filter_by(actuator_=act_element).first()
            
            # get data again
            data__ = [valve_element.trimType__.name, valve_element.flowDirection__.name, cases[0].valveSize, cv_element.seatBore, iPressure, oPressure, shutOffDelP,
                        iPressure - oPressure]
        else:
            pass
    return render_template('slidingstem.html', item=getDBElementWithId(itemMaster, int(item_id)), 
                           user=current_user, metadata=metadata_, page='slidingStem', 
                           valve=valve_element, cv=selected_sized_valve_element, act=act_element, 
                           cases=cases, cv_element=cv_element)


@app.route('/rotary-actuator/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def rotaryActuator(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    act_element = db.session.query(actuatorMaster).filter_by(item=item_element).first()
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    metadata_ = metadata()
    if request.method == 'POST':
        actuator_input_dict = {}
        actuator_input_dict['actuatorType'] = [request.form.get('actType')]
        actuator_input_dict['springAction'] = [request.form.get('failAction')]
        actuator_input_dict['handWheel'] = [request.form.get('mount')]
        actuator_input_dict['adjustableTravelStop'] = [request.form.get('travel')]
        actuator_input_dict['orientation'] = [request.form.get('orientation')]
        actuator_input_dict['availableAirSupplyMin'] = [request.form.get('availableAirSupplyMin')]
        actuator_input_dict['availableAirSupplyMax'] = [request.form.get('availableAirSupplyMax')]
        # print(actuator_input_dict)
        if request.form.get('sliding'):
            print('working')
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('slidingStem', item_id=item_id, proj_id=proj_id))
        elif request.form.get('rotary'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('rotaryActuator', item_id=item_id, proj_id=proj_id))
        elif request.form.get('stroketime'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('strokeTime', item_id=item_id, proj_id=proj_id))
        else:
            pass
    return render_template('RotaryActuatorSizing.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='rotaryActuator', valve=valve_element, act=act_element)


@app.route('/stroke-time/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def strokeTime(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    act_element = db.session.query(actuatorMaster).filter_by(item=item_element).first()
    actuator_element = db.session.query(actuatorMaster).filter_by(item=item_element).first()
    metadata_ = metadata()
    if actuator_element.actuatorType == 'Piston without Spring':
        html_page = 'stroke_time_piston.html'
    else:
        html_page = 'stroke_time_spring.html'
    if request.method == 'POST':
        actuator_input_dict = {}
        actuator_input_dict['actuatorType'] = [request.form.get('actType')]
        actuator_input_dict['springAction'] = [request.form.get('failAction')]
        actuator_input_dict['handWheel'] = [request.form.get('mount')]
        actuator_input_dict['adjustableTravelStop'] = [request.form.get('travel')]
        actuator_input_dict['orientation'] = [request.form.get('orientation')]
        actuator_input_dict['availableAirSupplyMin'] = [request.form.get('availableAirSupplyMin')]
        actuator_input_dict['availableAirSupplyMax'] = [request.form.get('availableAirSupplyMax')]
        # print(actuator_input_dict)
        if request.form.get('sliding'):
            print('working')
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('slidingStem', item_id=item_id, proj_id=proj_id))
        elif request.form.get('rotary'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('rotaryActuator', item_id=item_id, proj_id=proj_id))
        elif request.form.get('stroketime'):
            act_element.update(actuator_input_dict, act_element.id)
            return redirect(url_for('strokeTime', item_id=item_id, proj_id=proj_id))
        else:
            pass
    return render_template(html_page, item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='strokeTime', valve=valve_element, act=act_element)


# Accessories
@app.route('/accessories/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def accessories(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()
    metadata_ = metadata()
    if request.method == 'POST':
        data = request.form.to_dict(flat=False)
        a = jsonify(data).json
        accessories_element.update(a, accessories_element.id)
        return redirect(url_for('accessories', item_id=item_id, proj_id=proj_id))

    return render_template("accessories.html", item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_, page='accessories', valve=valve_element, acc=accessories_element)

# Accessories Positioner
@app.route('/positioner/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def positionerRender(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    positioner_ = positioner.query.all()
    metadata_ = metadata()
    metadata_['positioner'] = positioner_
    return render_template("positioner.html", item=getDBElementWithId(itemMaster, int(item_id)),
                            page='positionerRender', valve=valve_element, metadata=metadata_, user=current_user)


@app.route('/select-positioner/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def selectPositioner(proj_id, item_id):
    pos_id = request.form.get('positioner')
    pos_element = getDBElementWithId(positioner, pos_id)
    item_element = getDBElementWithId(itemMaster, int(item_id))
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()
    accessories_element.manufacturer = pos_element.manufacturer
    accessories_element.model = pos_element.series
    accessories_element.action = pos_element.action
    db.session.commit()
    return redirect(url_for('accessories', item_id=item_id, proj_id=proj_id))


# Accessories AFR
@app.route('/afr/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def afrRender(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    afr_ = afr.query.all()
    metadata_ = metadata()
    metadata_['afr_'] = afr_
    return render_template("afr.html", item=getDBElementWithId(itemMaster, int(item_id)),
                            page='positionerRender', valve=valve_element, metadata=metadata_, user=current_user)


@app.route('/select-afr/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def selectAfr(proj_id, item_id):
    afr_id = request.form.get('afr')
    afr_element = getDBElementWithId(afr, afr_id)
    item_element = getDBElementWithId(itemMaster, int(item_id))
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()
    accessories_element.afr = f"{afr_element.manufacturer}/{afr_element.model}"
    db.session.commit()
    return redirect(url_for('accessories', item_id=item_id, proj_id=proj_id))



# Accessories Limit Switch
@app.route('/limit/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def limitRender(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    limits = limitSwitch.query.all()
    metadata_ = metadata()
    metadata_['limits'] = limits
    return render_template("limitSwitch.html", item=getDBElementWithId(itemMaster, int(item_id)),
                            page='limitRender', valve=valve_element, metadata=metadata_, user=current_user)


@app.route('/select-limit/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def selectlimit(proj_id, item_id):
    limit_id = request.form.get('limit')
    limit_element = getDBElementWithId(limitSwitch, limit_id)
    item_element = getDBElementWithId(itemMaster, int(item_id))
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()
    accessories_element.limit = limit_element.model
    db.session.commit()
    return redirect(url_for('accessories', item_id=item_id, proj_id=proj_id))


# Accessories Solenoid
@app.route('/solenoid/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def solenoidRender(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, int(item_id))
    valve_element = db.session.query(valveDetailsMaster).filter_by(item=item_element).first()
    solenoid_ = solenoid.query.all()
    metadata_ = metadata()
    metadata_['solenoid_'] = solenoid_
    return render_template("solenoid.html", item=getDBElementWithId(itemMaster, int(item_id)),
                            page='limitRender', valve=valve_element, metadata=metadata_, user=current_user)


@app.route('/select-solenoid/proj-<proj_id>/item-<item_id>', methods=["GET", "POST"])
def selectSolenoid(proj_id, item_id):
    limit_id = request.form.get('solenoid')
    limit_element = getDBElementWithId(solenoid, limit_id)
    item_element = getDBElementWithId(itemMaster, int(item_id))
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()
    accessories_element.solenoid_make = limit_element.make
    accessories_element.solenoid_modle = limit_element.model
    accessories_element.solenoid_action = limit_element.type
    db.session.commit()
    return redirect(url_for('accessories', item_id=item_id, proj_id=proj_id))

# Item Notes
@app.route('/item-notes/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def itemNotes(proj_id, item_id):
    MAX_NOTE_LENGTH = 7
    item_element = getDBElementWithId(itemMaster, int(item_id))
    item_notes_list = db.session.query(itemNotesData).filter_by(item=item_element).order_by('notesNumber').all()
    accessories_element = db.session.query(accessoriesData).filter_by(item=item_element).first()

    uniqueNotes = []
    for notes_ in db.session.query(notesMaster.notesNumber).distinct():
        uniqueNotes.append(notes_.notesNumber)
    
    notes_dict = {}
    for nnn in uniqueNotes:
        contents = db.session.query(notesMaster).filter_by(notesNumber=nnn).all()
        content_list = [cont.content for cont in contents]
        notes_dict[nnn] = content_list
    # print("len of notes comparison")
    # print(len(item_notes_list))
    # print(MAX_NOTE_LENGTH)
    if request.method == 'POST':
        if request.form.get('accessories'):
            
            data = request.form.to_dict(flat=False)
            a = jsonify(data).json
            a.pop('note')
            a.pop('nvalues')
            accessories_element.update(a, accessories_element.id)
        else:
            item_notes_list_2 = db.session.query(itemNotesData).filter_by(item=item_element).order_by('notesNumber').all()
            if len(item_notes_list_2) <= MAX_NOTE_LENGTH:
                note_number = request.form.get('note')
                note_content = request.form.get('nvalues')
                content_list = [abc.content for abc in item_notes_list_2]
                if note_content in content_list:
                    flash(f'Note: "{note_content}" already exists', "error")
                else:
                    print(note_number, note_content)
                    new_item_note = itemNotesData(item=item_element, content=note_content, notesNumber=note_number)
                    db.session.add(new_item_note)
                    db.session.commit()
                    flash("Note Added Successfully", "success")
            else:
                flash(f"Max Length ({MAX_NOTE_LENGTH}) of Notes reached", "error")
        return redirect(url_for('itemNotes', item_id=item_id, proj_id=proj_id))

    return render_template("itemNotes.html", item=getDBElementWithId(itemMaster, int(item_id)), page='itemNotes',
                         user=current_user, dropdown=json.dumps(notes_dict),
                        notes_list=item_notes_list, acc=accessories_element)


# Project Notes
@app.route('/project-notes/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def project_notes(proj_id, item_id):
    project_element = getDBElementWithId(projectMaster, proj_id)
    notes_ = db.session.query(projectNotes).filter_by(project=project_element).all()
    print(len(notes_))
    if request.method == 'POST':
        new_note = projectNotes(notesNumber=request.form.get('notesNumber'), notes=request.form.get('notes'), project=project_element)
        db.session.add(new_note)
        db.session.commit()
        return redirect(url_for('project_notes', item_id=item_id, proj_id=proj_id))

    return render_template("projectNotes.html", item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                            page='projectNotes', notes=notes_)



@app.route('/del-project-notes/<note_id>/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def delProjectNotes(note_id, item_id, proj_id):
    note_element = projectNotes.query.get(note_id)
    db.session.delete(note_element)
    db.session.commit()
    # db.session.delete(addresss_element)
    # db.session.commit()
    return redirect(url_for('project_notes',item_id=item_id, proj_id=proj_id))

@app.route('/del-item-notes/<note_id>/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def delItemNotes(note_id, item_id, proj_id):
    note_element = itemNotesData.query.get(note_id)
    db.session.delete(note_element)
    db.session.commit()
    # db.session.delete(addresss_element)
    # db.session.commit()
    return redirect(url_for('itemNotes',item_id=item_id, proj_id=proj_id))

# Data View Module

@app.route('/view-data/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def viewData(item_id, proj_id):
    data2 = table_data_render
    metadata_ = metadata()
    return render_template('view_data_old.html', item=getDBElementWithId(itemMaster, int(item_id)), metadata=metadata_, data=data2, page='viewData', user=current_user)


@app.route('/render-data/proj-<proj_id>/item-<item_id>/<topic>', methods=['GET'])
def renderData(topic, item_id, proj_id):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    all_keys = table_data_render[int(topic) - 1]['db'].__table__.columns.keys()
    all_keys_ = [abc.capitalize() for abc in all_keys]
    table_data = table_.query.all()
    all_data = []
    for data_ in table_data:
        single_row_data = {}
        for key_ in all_keys:
        # all_data[0][all_keys[1]]
            single_row_data[key_] = getattr(data_, key_)
        all_data.append(single_row_data)
    # print(table_.__tablename__)
    # print(len(table_data))
    return render_template("render_data.html", data=table_data, topic=topic, page='renderData', name=name,
                           item=getDBElementWithId(itemMaster, int(item_id)), user=current_user, 
                           all_keys=all_keys, all_data=all_data, all_keys_=all_keys_)


@app.route('/download-data/proj-<proj_id>/item-<item_id>/<topic>', methods=['GET'])
def downloadData(topic, item_id, proj_id):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    table_data = table_.query.all()
    with open('my_file.csv', 'w', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)

        # Write data to the CSV file
        all_keys = table_data_render[int(topic) - 1]['db'].__table__.columns.keys()
        writer.writerow(all_keys)
        for data_ in table_data:
            single_row_data = []
            for key_ in all_keys:
            # all_data[0][all_keys[1]]
                abc = getattr(data_, key_)
                single_row_data.append(abc)
            writer.writerow(single_row_data)
        # Close the CSV file
        csvfile.close()
    path = 'my_file.csv'
    return send_file(path, as_attachment=True, download_name=f"{table_.__tablename__}.csv")


@app.route('/upload-data/proj-<proj_id>/item-<item_id>/<topic>', methods=['GET', 'POST'])
def uploadData(topic, item_id, proj_id):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    table_data = table_.query.all()

    if request.method == 'POST':
        try:
            b_list = request.files.get('file').stream.read().decode().strip().split('\n')
            if len(b_list[1].split(',')) < 3:
                b_list_2 = [abc.split(',')[1].split('\r')[0] for abc in b_list[1:]]
                data_upload(b_list_2, table_)
            if topic == '25':
                pt_list = []
                for i in b_list[1:]:
                    try:
                        i_dict = {'maxTemp': float(i.split(',')[1]), 'minTemp': float(i.split(',')[2]) * (-1),
                                'pressure': float(i.split(',')[3]), 'material': i.split(',')[4],
                                'rating': i.split(',')[5].split('\r')[0]}
                        pt_list.append(i_dict)
                    except ValueError:
                        pass

                pressure_temp_upload(pt_list)
            else:
                all_keys = table_data_render[int(topic) - 1]['db'].__table__.columns.keys()
                table__ = table_data_render[int(topic) - 1]['db']
                others_list = []
                pass
                data_delete(table__)
                for i in b_list[1:]:
                    i_dict = {}
                    for ind in range(len(all_keys[1:])):
                        col_type = table__.__table__.columns[all_keys[1:][ind]].type
                        if col_type == String or VARCHAR:
                            i_dict[all_keys[ind]] = i.split(',')[ind]
                        elif col_type == FLOAT:
                            i_dict[all_keys[ind]] = float(i.split(',')[ind])
                        elif col_type == INTEGER:
                            i_dict[all_keys[ind]] = int(i.split(',')[ind])
                    others_list.append(i_dict)
                    db.session.add(table__(**i_dict))
                    db.session.commit()
        except Exception as e:
            # Write logic for headers mismatch later
            # flash(f'An Error Occured: {e}')
            print(e)
            pass



    return redirect(url_for('renderData', topic=topic, item_id=item_id, proj_id=proj_id))



@app.route('/nextItem/<control>/<page>/item-<item_id>/proj-<proj_id>', methods=['GET', 'POST'])
def nextItem(control, page, item_id, proj_id):
    with app.app_context():
        current_item = getDBElementWithId(itemMaster, item_id)
        item_all = db.session.query(itemMaster).filter_by(project=current_item.project).all()
        len_items = len(item_all)
        item_1_index = item_all.index(current_item)
        if control == 'next':
            if item_all.index(current_item)+1 < len_items:
                current_item = db.session.query(itemMaster).filter_by(id=item_all[item_1_index + 1].id).first()
            else:
                current_item = db.session.query(itemMaster).filter_by(id=item_all[-1].id).first()
        elif control == 'prev':
            if item_all.index(current_item) > 0:
                current_item = db.session.query(itemMaster).filter_by(id=item_all[item_1_index - 1].id).first()
            else:
                current_item = db.session.query(itemMaster).filter_by(id=item_all[0].id).first()
        elif control == 'first':
            current_item = db.session.query(itemMaster).filter_by(id=item_all[0].id).first()
            print('condition working')
            print(item_all[0].id)
        elif control == 'last':
            current_item = db.session.query(itemMaster).filter_by(id=item_all[-1].id).first()

        return redirect(url_for(page, item_id=current_item.id, proj_id=current_item.project.id))



@app.route('/generate-csv/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def generate_csv(item_id, proj_id):
    with app.app_context():
        item_selected = getDBElementWithId(itemMaster, item_id)
        project_ = item_selected.project

        all_items = db.session.query(itemMaster).filter_by(project=getDBElementWithId(projectMaster, proj_id)).all()
        cases__ = []
        units__ = []
        others__ = []

        for item in all_items:
            v_details = db.session.query(valveDetailsMaster).filter_by(item=item).first()
            acc_details = db.session.query(accessoriesData).filter_by(item=item).first()
            acc_list = [acc_details.manufacturer, acc_details.model, acc_details.action, acc_details.afr,
                        acc_details.afr,
                        acc_details.transmitter, acc_details.limit, acc_details.proximity, acc_details.booster,
                        acc_details.pilot_valve,
                        acc_details.air_lock, acc_details.ip_make, acc_details.ip_model, acc_details.solenoid_make,
                        acc_details.solenoid_model,
                        '3/2 Way', acc_details.volume_tank]
            # Act data
            # Act data
            act_data_string = []
            # else:
            act_valve_data_string = []
            act_other = []
            act_model = None
            model_str = None
            v_model_lower = getValveType(v_details.style.name)
            

            # material_ = material_updated.name
            itemCases_1 = db.session.query(caseMaster).filter_by(item=item).all()
            date = datetime.date.today().strftime("%d-%m-%Y -- %H-%M-%S")

            fields___ = ['Flow Rate', 'Inlet Pressure', 'Outlet Pressure', 'Inlet Temperature', 'Specific Gravity',
                         'Viscosity', 'Vapor Pressure', 'Xt', 'Calculated Cv', 'Open %', 'Valve SPL', 'Inlet Velocity',
                         'Outlet Velocity', 'Trim Exit Velocity', 'Tag Number', 'Item Number', 'Fluid State',
                         'Critical Pressure',
                         'Inlet Pipe Size', 'Outlet Pipe Size', 'Valve Size', 'Rating', 'Quote No.', 'Work Order No.',
                         'Customer']

            rows___ = []

            # get units
            cases = db.session.query(caseMaster).filter_by(item=item).all()
            if len(cases) == 0:
                pass
            else:
                last_case = cases[len(cases) - 1]
                
                if v_model_lower == 'globe':
                    percent__, i_pipe_vel, o_pipe_vel, t_vel = '%', 'm/s', 'm/s', 'm/s'
                else:
                    percent__, i_pipe_vel, o_pipe_vel, t_vel = 'degree', 'mach', 'mach', 'mach'
                unit_list = [item.project.flowrateUnit, item.project.pressureUnit, item.project.pressureUnit, item.project.temperatureUnit, '', 'centipose', item.project.pressureUnit, '', '', percent__,
                             'dB',
                             i_pipe_vel,
                             o_pipe_vel, t_vel, item.project.lengthUnit, item.project.lengthUnit]
                
               

                item_notes_list = db.session.query(itemNotesData).filter_by(item=item).order_by('notesNumber').all()

                cv_value_element = db.session.query(cvValues).filter_by(cv=cases[0].cv).first()

                other_val_list = [v_details.serialNumber, 1, item.project.projectRef, cases[0].criticalPressure, item.project.pressureUnit, v_details.shutOffDelP, cases[0].valveSize, item.project.lengthUnit, v_details.rating.name,
                                  v_details.material.name, v_details.bonnetType__.name, "See Note 1", "See Note 1", v_details.gasket__.name, v_details.trimType__.name, v_details.flowDirection__.name, v_details.seat__.name,
                                  v_details.disc__.name,
                                  v_details.seatLeakageClass__.name, v_details.endConnection__.name, v_details.endFinish__.name, v_model_lower, model_str, v_details.bonnet__.name,
                                  v_details.bonnetExtDimension, v_details.studNut__.name, cases[0].ratedCv, v_details.balanceSeal__.name, acc_list, v_details.application, cases[0].fluid.fluidName, 
                                  v_details.maxPressure, v_details.maxTemp, v_details.minTemp, None, None, v_details.packing__.name,
                                  cv_value_element.seatBore, cv_value_element.travel, v_details.flowDirection__.name, v_details.flowCharacter__.name, v_details.shaft__.name, item_notes_list]
                
                customer__ = db.session.query(addressProject).filter_by(isCompany=True, project=item.project).first()
                
                for i in itemCases_1[:6]:
                    case_list = [i.flowrate, i.inletPressure, i.outletPressure, i.inletTemp, i.specificGravity, i.kinematicViscosity, i.vaporPressure,
                                 i.xt,
                                 i.calculatedCv, i.openingPercentage, i.spl,
                                 i.pipeInVel, i.pipeOutVel, i.tex, v_details.tagNumber, item.id,
                                 v_details.state.name, itemCases_1[0].criticalPressure,
                                 itemCases_1[0].inletPipeSize, itemCases_1[0].outletPipeSize, i.valveSize, v_details.rating.name, item.project.projectId,
                                 item.project.workOderNo,
                                 f"{customer__.address.company.name} {customer__.address.address}"]
                    
                    # case_list_dict = {
                    #                     "flowrate": i.flowrate, "iPressure": i.iPressure, "oPressure": i.oPressure,
                    #                     "iTemp": i.iTemp, "sGravity": i.sGravity, "viscosity": i.viscosity, "vPressure": i.vPressure,
                    #                     "Xt": i.Xt, "CV": i.CV, "openPercent": i.openPercent, "valveSPL": i.valveSPL,
                    #                     "iVelocity": i.iVelocity, "oVelocity": i.oVelocity, "trimExVelocity": i.trimExVelocity, "tagNo": item.tag_no,
                    #                     "itemId": item.id, "fluidState": itemCases_1[0].fluidState, "criticalPressure": itemCases_1[0].criticalPressure,
                    #                     "iPipeSize": itemCases_1[0].iPipeSize, "oPipeSize": itemCases_1[0].oPipeSize, "size_": size__, "rating": rating__,
                    #                     "quote": project__.quote, "workOrder": project__.work_order, "customer": customer__
                    #                 }
                    rows___.append(case_list)

                cases__.append(rows___)
                units__.append(unit_list)
                others__.append(other_val_list)
                try:
                    act_dict_ = {'v_type': cases[0].ratedCv, 'trim_type': v_details.trimType__.name, 'Balancing': v_details.balanceSeal__.name,
                                'fl_direction': v_details.flowDirection__.name, 'v_size': cases[0].valveSize,
                                'v_size_unit': item.project.lengthUnit,
                                'Seat_Dia': i.seatDia,
                                'seat_dia_unit': item.project.lengthUnit, 'unbalance_area': act_valve_data_string[5],
                                'unbalance_area_unit': 'inch^2',
                                'Stem_size': act_valve_data_string[4], 'Stem_size_unit': 'inch',
                                'Travel': act_valve_data_string[1],
                                'travel_unit': 'inch', 'Packing_Friction': act_data_string[13],
                                'packing_friction_unit': 'mm', 'Seat_Load_Factor': act_data_string[24],
                                'Additional_Factor': 0,
                                'P1': itemCases_1[-1].iPressure,
                                'p1_unit': item.project.pressureUnit,
                                'P2': itemCases_1[-1].oPressure, 'p2_unit': item.project.pressureUnit,
                                'delP_Shutoff': v_details.shutOffDelP, 'delP_Shutoff_unit': 'bar', 'unbal_force': 0,
                                'Kn': act_data_string[15], 'delP_flowing': 0,
                                'act_type': act_other[0],
                                'fail_action': act_data_string[4], 'act_size': act_data_string[0],
                                'act_size_unit': 'inch',
                                'act_travel': act_data_string[1], 'act_travel_unit': 'inch',
                                'eff_area': act_data_string[0], 'eff_area_unit': 'inch^2',
                                'sMin': act_data_string[2], 'sMax': act_data_string[3], 'spring_rate': act_data_string[18],
                                'spring_windup': act_data_string[19], 'max_spring_load': act_data_string[20],
                                'max_air_supply': act_other[6],
                                'set_pressure': act_data_string[5], 'set_pressure_unit': 'bar', 'act_thrust_down': 0,
                                'act_thrust_up': 0, 'handwheel': act_other[2],
                                'friction_band': act_data_string[21],
                                'req_handWheel_thrust': act_data_string[22], 'max_thrust': act_data_string[23],
                                'v_thrust_close': 0, 'v_thrust_open': 0, 'seat_load': act_data_string[14],
                                'orientation': act_other[3], 'act_model': act_model, 'travel_stops': act_other[8]
                                }
                except IndexError:
                    act_dict_ = {'v_type': cases[0].ratedCv, 'trim_type': v_details.trimType__.name, 'Balancing': v_details.balanceSeal__.name,
                                'fl_direction':  v_details.flowDirection__.name, 'v_size': cases[0].valveSize,
                                'v_size_unit': item.project.lengthUnit,
                                'Seat_Dia': i.seatDia,
                                'seat_dia_unit': item.project.lengthUnit, 'unbalance_area': None,
                                'unbalance_area_unit': 'inch^2',
                                'Stem_size': None, 'Stem_size_unit': 'inch',
                                'Travel': None,
                                'travel_unit': 'inch', 'Packing_Friction': None,
                                'packing_friction_unit': 'mm', 'Seat_Load_Factor': None,
                                'Additional_Factor': 0,
                                'P1': itemCases_1[-1].inletPressure,
                                'p1_unit': item.project.pressureUnit,
                                'P2': itemCases_1[-1].outletPressure, 'p2_unit': item.project.pressureUnit,
                                'delP_Shutoff': v_details.shutOffDelP, 'delP_Shutoff_unit': 'bar', 'unbal_force': 0,
                                'Kn': None, 'delP_flowing': 0,
                                'act_type': None,
                                'fail_action': None, 'act_size': None,
                                'act_size_unit': 'inch',
                                'act_travel': None, 'act_travel_unit': 'inch',
                                'eff_area': None, 'eff_area_unit': 'inch^2',
                                'sMin': None, 'sMax': None, 'spring_rate': None,
                                'spring_windup': None, 'max_spring_load': None,
                                'max_air_supply': None,
                                'set_pressure': None, 'set_pressure_unit': 'bar', 'act_thrust_down': 0,
                                'act_thrust_up': 0, 'handwheel': None,
                                'friction_band': None,
                                'req_handWheel_thrust': None, 'max_thrust': None,
                                'v_thrust_close': 0, 'v_thrust_open': 0, 'seat_load': None,
                                'orientation': None, 'act_model': act_model, 'travel_stops': None
                                }
                act_dict = act_dict_

        print(act_dict)
        createSpecSheet(cases__, units__, others__, act_dict)
        path = "specsheet.xlsx"
        project_number = item.project.id
        current_datetime = datetime.datetime.today().date().timetuple()

        str_current_datetime = str(current_datetime)
        a__ = datetime.datetime.now()
        a_ = a__.strftime("%a, %d %b %Y %H-%M-%S")
        spec_sheet_name = f'Specsheet_P{project_number}_{a_}.xlsx'

        return send_file(path, as_attachment=True, download_name=spec_sheet_name)



####################### DATA UPLOAD BULK
def DATA_UPLOAD_BULK():    
    industry_list = ['Oil & Gas - Onshore', 'Oil & Gas - Offshore', 'Refinery & Petrochemical',
                    'Oil & Gas - Transportation & Distribution', 'Chem & Pharma', 'Food & Beverages', 'OEM',
                    'Pulp & Paper', 'Mining & Metal', 'Thermal Power & Nuclear Power', 'Defence, Nuclear & Aerospace',
                    'Air Separation & LNG', 'Desalination & Water Treatment Plant', 'Others']

    region_list = ['Domestic', 'South East Asia', 'China', 'Australia', 'Europe', 'Middle East', 'Africa', 'Far East',
                'Russia', 'North America', 'South America', 'Special Project']

    f_state_list = ['Liquid', 'Gas', 'Two Phase']

    design_std_list = ['ASME', 'API']

    valve_style_list = ['Globe Straight', 'Globe Angle', 'Butterfly Lugged Wafer', 'Butterfly Double Flanged']

    application_list = ['Temperature Control', 'Pressure Control', 'Flow Control', 'Level Control', 'Compressor Re-Cycle',
                        'Compressor Anti-Surge', 'Cold Box Service', 'Condensate Service', 'Cryogenic Service',
                        'Desuperheater Service', 'Feedwater Service', 'Heater Drain', 'High P&T Steam', 'H/He Service',
                        'Joule Thompson Valve', 'LNG Service', 'Soot Blower Valve', 'Spraywater Valve', 'Switching Valve']

    rating_list = ['ASME 150', 'ASME 300', 'ASME 600', 'ASME 900', 'ASME 1500', 'ASME 2500', 'API 5000', 'API 10000',
                'API 15000']

    material_list = ['ASTM A216 WCB', 'ASTM A216 WCC', 'ASTM A352 LCC', 'ASTM A352 LCB', 'ASTM A351 CF8M',
                    'ASTM A351 CF3M', 'ASTM A351 CF8', 'ASTM A351 CF3', 'ASTM A217 WC6', 'ASTM A217 WC9',
                    'ASTM A217 C12A', 'ASTM A217 C5', 'ASTM A995 CD3MN (4A)', 'ASTM A995 CE8MN (5A)',
                    'ASTM A995 CD3MWCuN (6A)', 'ASTM A351 CK3MCuN']

    balance_seal_list = ['Unbalanced', 'Balanced PTFE', 'Balanced Graphite', 'Metal']

    bonnet_list = ['ASTM A216 WCB', 'ASTM A216 WCC', 'ASTM A352 LCC', 'ASTM A352 LCB', 'ASTM A351 CF8M',
                    'ASTM A351 CF3M', 'ASTM A351 CF8', 'ASTM A351 CF3', 'ASTM A217 WC6', 'ASTM A217 WC9',
                    'ASTM A217 C12A', 'ASTM A217 C5', 'ASTM A995 CD3MN (4A)', 'ASTM A995 CE8MN (5A)',
                    'ASTM A995 CD3MWCuN (6A)', 'ASTM A351 CK3MCuN']

    bonnetType_list = ['Standard', 'Standard Extension', 'Normalised/Finned', "Bellow Seal", 'Cryogenic',
                        'Cryogenic + Drip Plate', 'Cryogenic + Seal Boot', 'Cryogenic + Cold Box Flange']

    certification_list = ['2.1 Certification', '2.2 Certification', '3.1 Certification', '3.2 Certification', 'NABL Certified']

    cleaning_list = ['As per FCC Standard', 'As per Customer specification']

    flow_dir_list = ['Over', 'Under', 'Seat Downstream', 'Seat Upstream']

    trim_type_list_globe = ['Microspline', 'Contour', 'Ported', 'Anti-Cavitation I', 'Anti-Cavitation II', 'Anti-Cavitation III', 'MHC',
                    'Low Noise Trim A1','Low Noise Trim A3','Low Noise Trim B1','Low Noise Trim B3','Low Noise Trim C1',
                    'Low Noise Trim C3','Low Noise Trim D1','Low Noise Trim D3']

    trim_type_list_butterfly = ['Double Offset', 'Triple Offset']


    flow_charac_list = ['Equal %', 'Linear', 'Modified Equal %']

    balancing_list = ['Balanced', 'Unbalanced', 'N/A']

    disc_material_list_butterfly = ['316SS', '316 / Stellite Overlay', '316L SS', '316L / Stellite Overlay', 'UNS 31254 / 6Mo',
                                    'UNS 31803 / DSS', 'Al. Bronze', 'UNS 32760 / SDSS', 'Hastelloy C', 'Alloy 625', 'Monel 400', 
                                    'Monel 500', 'Titanium', 'Alloy 800']

    plug_material_list_globe = ['316SS', '304SS', '304SS / Stellite FC', '304SS / Stellite SA', '304L SS', '304L SS / Stellite FC', '304L SS / Stellite SA',
                                '316 SS / Stellite FC', '316 SS / Stellite SA', '316L SS', '316L SS / Stellite FC', '316L SS / Stellite SA',
                                '410SS', '410SS Hardened', '440C SS Hardened', 'Al. Bronze', 'Duplex SS', 'Duplex SS / Stellite FC', 'Duplex SS / Stellite SA',
                                'Hastelloy B', 'Hastelloy C', 'Alloy 625', 'Alloy 625 / Stellite FC', 'Alloy 625 / Stellite SA', 'Monel 400 / K500',
                                'Monel / Col / LG2', 'Super Duplex SS', 'Super Duplex SS / Stellite FC', 'Super Duplex SS / Stellite SA', 'Tungsten. Co / 17-4PH',
                                'Tungsten. Co / 316SS']

    seat_material_list_globe = ['S41000', 'S31600 w/CoCr-A SA', 'S316 w/CoCr-A FC', 'CA6NM HT', '2205 Duplex w/CoCr-A', 
                                '2507 Super Duplex w/CoCr-A', 'PTFE']

    seat_material_list_butterfly = ['PTFE', '316SS', 'S32760', 'Alloy 625', 'Laminated 316L + Graphite', 'Laminated 625 + Graphite']

    packing_material_list_butterfly = ['PTFE Chevron', 'PTFE Braid', 'Graphite', 'RPTFE Graphite', 'Low Emmission EVSP', 'High Intensity Gland', 
                                    'HIG Spagrapf', 'Gland Security System', 'Packing + Wiper PTFE', 'Packing + Wiper Graphite']

    designation_list = ['Manager','Director','Managing Director','Sr.Manager','Assistant Manager','Deputy Manager','Engineer',
                        'GET','Ass.Engineer','Sr. Engineer','Executive','Technician']

    department_list = ['Finance & HR', 'Administration', 'Finance', 'Design & Engineering', 'Application Engineering, Sales & Contracts',
                    'Purchase', 'Quality Control', 'Information Technology', 'Production', 'Production & Maintenance']

    end_connection_list = ['None', 'Integral Flange', 'Loose Flange', 'Flange (Drilled ASME 150)', 'Screwed NPT', 'Screwed BSPT', 
                        'Screwed BSP', 'Socket Weld', 'Butt Weld', 'Grayloc Hub', 'Vector / Techloc Hub', 'Destec Hub', 
                        'Galperti Hub', 'BW Stubs', 'Plain Stubs', 'Drilled Lug', 'Tapped Lug', 'BW Stubs Sch 10', 'BW Stubs Sch 40', 
                        'BW Stubs Sch 80']

    end_finish_list = ['None', 'RF Serrated', 'RF (125-250 AARH) 3.2-6.3 μm', 'RF (63-125 AARH) 1.6-3.2 μm', 'FF Serrated',
                    'FF (125-250 AARH) 3.2-6.3 μm', 'FF (63-125 AARH) 1.6-3.2 μm', 'RTJ', 'ASME B16.21 Fig. 2a']

    seat_leakage_class_list = ['ANSI Class II', 'ANSI Class III', 'ANSI Class IV', 'ANSI Class V', 'ANSI Class VI']

    stud_material_list = ['None', 'Standard for Body Material', 'B7 / 2H', 'B7 / 2H Galvanised', 'L7 / 4', 'L7 / 7 Xylan Coated', 
                        'L7M / 7M', 'B8M / 8M', 'B8 Class 1/8', 'B8 / 8', 'Al-Br B150 Gr C6300 HR50', 'B7M / 2HM', 'B16 / 4']

    gasket_material_list = ['Standard for Service', 'PTFE', 'PCTFE (KEL-F)', 'Spiral Wond 316L / Graph.', 
                            'Spiral Wond 316L / PTFE', 'Spiral Wond 31803 / Graph.', 'Spiral Wond 31803 / PTFE', 
                            'Spiral Wond 32760 / Graph.', 'Spiral Wond 32760 / PTFE', 'Spiral Wond 625 / Graph.', 
                            'Spiral Wond 625 / PTFE', 'Graphite', 'Metal Seal', 'Double ABS (cryo)']

    cage_clamp_material_list = ["316", "17-4PH", "17-4PH (H900)", "316 Cr Plated", 
                                "32760 (Super Duplex)",  "31803 Duplex", "410"]


    packing_type_list = ['Single', 'Double', 'Inverted']



    # print(getRowsFromCsvFile("csv/afr.csv"))
    # print(getRowsFromCsvFile("csv/cvtable.csv")[::6])
    # print(getRowsFromCsvFile("csv/shaft.csv"))


    with app.app_context():
    #     data_upload(valve_style_list, valveStyle)
        # butterfly_element_1 = db.session.query(valveStyle).filter_by(name="Butterfly Lugged Wafer").first()
        # butterfly_element_2 = db.session.query(valveStyle).filter_by(name="Butterfly Double Flanged").first()
        # globe_element_1 = db.session.query(valveStyle).filter_by(name="Globe Straight").first()
        # globe_element_2 = db.session.query(valveStyle).filter_by(name="Globe Angle").first()
        # v_style_list = [butterfly_element_1, butterfly_element_2, globe_element_1, globe_element_2]   
        # data_upload(industry_list, industryMaster)
        # data_upload(region_list, regionMaster)
        # data_upload(f_state_list, fluidState)
        # data_upload(design_std_list, designStandard)
        # data_upload(application_list, applicationMaster)
        # data_upload(rating_list, ratingMaster)
        # data_upload(material_list, materialMaster)
        # data_upload(bonnet_list, bonnet)
        # add_many(getRowsFromCsvFile("csv/afr.csv"), afr)
        # add_many(getRowsFromCsvFile("csv/fluidProperties.csv"), fluidProperties)
        # add_many(getRowsFromCsvFile("csv/pipearea.csv"), pipeArea)
        # add_many(getRowsFromCsvFile("csv/valvearea.csv"), valveArea)
        # data_upload(balance_seal_list, balanceSeal)
        # data_upload(bonnetType_list, bonnetType)
        # data_upload(certification_list, certification)
        # data_upload(cleaning_list, cleaning)
        # data_upload(flow_dir_list, flowDirection)
        # data_upload(trim_type_list, trimType)
        # data_upload(flow_charac_list, flowCharacter)
        # data_upload(balancing_list, balancing)
        # # cv_upload(getRowsFromCsvFile("csv/cvtable_small.csv"))
        # cv_upload(getRowsFromCsvFile("csv/cvtable.csv"))
        # data_upload_disc_seat_packing([disc_material_list_butterfly, disc_material_list_butterfly, plug_material_list_globe, plug_material_list_globe], v_style_list, disc)
        # data_upload_disc_seat_packing([seat_material_list_butterfly, seat_material_list_butterfly, seat_material_list_globe, seat_material_list_globe], v_style_list, seat)
        # data_upload_disc_seat_packing([trim_type_list_butterfly, trim_type_list_butterfly, trim_type_list_globe, trim_type_list_globe], v_style_list, trimType)
        # data_upload(department_list, departmentMaster)
        # data_upload(designation_list, designationMaster)
        # data_upload_shaft(getRowsFromCsvFile("csv/shaft.csv"), v_style_list)
        # data_upload(end_connection_list, endConnection)
        # data_upload(end_finish_list, endFinish)
        # data_upload(seat_leakage_class_list, seatLeakageClass)
        # data_upload(packing_material_list_butterfly, packing)
        # data_upload(stud_material_list, studNut)
        # data_upload(gasket_material_list, gasket)
        # data_upload(cage_clamp_material_list, cageClamp)
        # data_upload(packing_type_list, packingType)
        # add_many(getRowsFromCsvFile("csv/slidingActuatorData.csv"), slidingActuatorData)
        # add_many(getRowsFromCsvFile("csv/rotaryActuatorData.csv"), rotaryActuatorData)
        # add_many(getRowsFromCsvFile("csv/notesMaster.csv"), notesMaster)
        # add_many(getRowsFromCsvFile("csv/positioner.csv"), positioner)
        # # add_many(getRowsFromCsvFile("csv/limit_switch.csv"), limitSwitch)
        # add_many(getRowsFromCsvFile("csv/solenoid.csv"), solenoid)
        pass

# DATA_UPLOAD_BULK()
# cv_upload(getRowsFromCsvFile("csv/cvtable.csv"))
    

if __name__ == "__main__":
    app.run(debug=False)
