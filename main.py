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
from functions import full_format, project_status_list, notes_dict_reorder, purpose_list, units_dict

# -----------^^^^^^^^^^^^^^----------------- IMPORT STATEMENTS -----------------^^^^^^^^^^^^^------------ #


### --------------------------------- APP CONFIGURATION -----------------------------------------------------###

# app configuration
app = Flask(__name__)

app.config['SECRET_KEY'] = "kkkkk"
Bootstrap(app)

# CONNECT TO DB
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///fcc-db-v3-1.db"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL1", "sqlite:///fcc-db-v3-1.db")
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


class userMaster(UserMixin, db.Model):
    __tablename__ = "userMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(1000))
    password = Column(String(100))
    employeeId = Column(String(100))
    email = Column(String(100), unique=True)
    mobile = Column(String(100))
    fccUser = Column(Boolean)

    # relationships
    # TODO 1 - Project Master
    project = relationship("projectMaster", back_populates="user")

    # relationship as child
    departmentId = Column(Integer, ForeignKey("departmentMaster.id"))
    department = relationship("departmentMaster", back_populates="user")

    designationId = Column(Integer, ForeignKey("designationMaster.id"))
    designation = relationship("designationMaster", back_populates="user")


class companyMaster(db.Model):
    __tablename__ = "companyMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    description = Column(String(300))

    # relationship as parent
    address = relationship('addressMaster', back_populates='company')


class departmentMaster(db.Model):
    __tablename__ = "departmentMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    user = relationship("userMaster", back_populates="department")


class designationMaster(db.Model):
    __tablename__ = "designationMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    user = relationship("userMaster", back_populates="designation")


# data upload done
class industryMaster(db.Model):
    __tablename__ = "industryMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    # relationship as parent
    project = relationship("projectMaster", back_populates="industry")


# data upload done
class regionMaster(db.Model):
    __tablename__ = "regionMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    # relationship as parent
    project = relationship("projectMaster", back_populates="region")


class addressMaster(db.Model):
    __tablename__ = "addressMaster"
    id = Column(Integer, primary_key=True)
    address = Column(String(300))
    customerCode = Column(String(15))  # to add as A001 to A999 and B001 to B999 and so on.
    isActive = Column(Boolean)

    # relationship as parent
    # projectCompany = relationship('projectMaster',uselist=False, backref='address_company')
    # projectEnduser = relationship('projectMaster',uselist=False, backref='address_enduser')
    address_project = relationship('addressProject', back_populates='address')

    # relationship as child
    companyId = Column(Integer, ForeignKey("companyMaster.id"))
    company = relationship("companyMaster", back_populates="address")


class addressProject(db.Model):
    __tablename__ = "addressProject"
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
    id = Column(Integer, primary_key=True)
    name = Column(String(300))
    designation = Column(String(300))

    # relationship as parent
    engineer_project = relationship('engineerProject', back_populates='engineer')
    # projectContract = relationship("projectMaster",uselist=False, backref="engineer_contract")
    # projectApplicaton = relationship("projectMaster",uselist=False, backref="engineer_application")


class projectMaster(db.Model):
    __tablename__ = "projectMaster"
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
    # relationship as parent
    item = relationship("itemMaster", cascade="all,delete", back_populates="project")
    projectnotes = relationship('projectNotes', back_populates='project')
    project_address = relationship('addressProject', back_populates='project')
    project_engineer = relationship('engineerProject', back_populates='project')

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
    id = Column(Integer, primary_key=True)
    notes = Column(String(300))
    date = Column(DateTime)

    # relationship as child
    projectId = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="projectnotes")


class itemMaster(db.Model):
    __tablename__ = "itemMaster"
    id = Column(Integer, primary_key=True)
    itemNumber = Column(Integer)
    alternate = Column(String(50))
    pressureUnit = Column(String(50))
    flowrateUnit = Column(String(50))
    temperatureUnit = Column(String(50))
    lengthUnit = Column(String(50))

    # rel as parent
    case = relationship("caseMaster", back_populates="item")

    # one-to-one relationship with valve, actuator and accessories, as parent
    valve = relationship("valveDetailsMaster", back_populates="item")
    actuator = relationship("actuatorMaster", back_populates="item")
    accessories = relationship("accessoriesData", back_populates="item")

    # relationship as child
    projectID = Column(Integer, ForeignKey("projectMaster.id"))
    project = relationship("projectMaster", back_populates="item")


# data upload done
class fluidState(db.Model):
    __tablename__ = "fluidState"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', back_populates='state')


# data upload done
class designStandard(db.Model):
    __tablename__ = "designStandard"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', back_populates='design')


# data upload done
class valveStyle(db.Model):
    __tablename__ = "valveStyle"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', back_populates='style')
    cv = relationship('cvTable', back_populates='style')
    shaft_ = relationship('shaft', back_populates='style')
    disc_ = relationship('disc', back_populates='style')
    seat_ = relationship('seat', back_populates='style')
    packing_ = relationship('packing', back_populates='style')
    trimtype_ = relationship('trimType', back_populates='style')


# data upload done
class applicationMaster(db.Model):
    __tablename__ = "applicationMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


# data upload done
class ratingMaster(db.Model):
    __tablename__ = "ratingMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', back_populates='rating')
    pt = relationship('pressureTempRating', back_populates='rating')
    cv = relationship('cvTable', back_populates='rating_c')
    packingF = relationship('packingFriction', back_populates='rating')
    torque = relationship("packingTorque", back_populates='rating')


# data upload done
class materialMaster(db.Model):
    __tablename__ = "materialMaster"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # relationship as parent
    valve = relationship('valveDetailsMaster', back_populates='material')
    pt = relationship('pressureTempRating', back_populates='material')


# data upload done
class pressureTempRating(db.Model):
    __tablename__ = "pressureTempRating"
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
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    endConnection_ = relationship('valveDetailsMaster', back_populates='endConnection__')


# 19
class endFinish(db.Model):
    __tablename__ = "endFinish"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    endFinish_ = relationship('valveDetailsMaster', back_populates='endFinish__')


# 20
class bonnetType(db.Model):
    __tablename__ = "bonnetType"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    bonnetType_ = relationship('valveDetailsMaster', back_populates='bonnetType__')


# 21
class packingType(db.Model):
    __tablename__ = "packingType"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    packingType_ = relationship('valveDetailsMaster', back_populates='packingType__')


class trimType(db.Model):
    __tablename__ = "trimType"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    trimType_ = relationship('valveDetailsMaster', back_populates='trimType__')
    trimType_c = relationship('cvTable', back_populates='trimType_')
    seatLoad = relationship('seatLoadForce', back_populates='trimType_')
    kn = relationship("knValue", back_populates="trimType_")

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='trimtype_')


class flowCharacter(db.Model):  # TODO - Paandi  ............Done
    __tablename__ = "flowCharacter"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    flowCharacter_ = relationship('valveDetailsMaster', back_populates='flowCharacter__')
    flowCharacter_c = relationship('cvTable', back_populates='flowCharacter_')
    kn = relationship('knValue', back_populates='flowCharacter_')


# 23
class flowDirection(db.Model):  # TODO - Paandi  ............Done
    __tablename__ = "flowDirection"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    flowDirection_ = relationship('valveDetailsMaster', back_populates='flowDirection__')
    flowDirection_c = relationship('cvTable', back_populates='flowDirection_')
    kn = relationship('knValue', back_populates='flowDirection_')


# 24
class seatLeakageClass(db.Model):  # TODO - Paandi    ..........Done
    __tablename__ = "seatLeakageClass"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    seatLeakageClass_ = relationship('valveDetailsMaster', back_populates='seatLeakageClass__')
    seatLoad = relationship('seatLoadForce', back_populates='leakage')


# 25
class bonnet(db.Model):
    __tablename__ = "bonnet"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    bonnet_ = relationship('valveDetailsMaster', back_populates='bonnet__')


class nde1(db.Model):
    __tablename__ = "nde1"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    nde1_ = relationship('valveDetailsMaster', back_populates='nde1__')


class nde2(db.Model):
    __tablename__ = "nde2"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    nde2_ = relationship('valveDetailsMaster', back_populates='nde2__')


class shaft(db.Model):  # Stem in globe
    __tablename__ = "shaft"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    yield_strength = Column(Float)

    shaft_ = relationship('valveDetailsMaster', back_populates='shaft__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='shaft_')


class disc(db.Model):  # plug in globe
    __tablename__ = "disc"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    disc_ = relationship('valveDetailsMaster', back_populates='disc__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='disc_')


class seat(db.Model):  # both seat
    __tablename__ = "seat"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    seat_ = relationship('valveDetailsMaster', back_populates='seat__')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='seat_')


class packing(db.Model):
    __tablename__ = "packing"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    packing_ = relationship('valveDetailsMaster', back_populates='packing__')
    packingF = relationship('packingFriction', back_populates='packing_')

    valveStyleId = Column(Integer, ForeignKey("valveStyle.id"))
    style = relationship('valveStyle', back_populates='packing_')


class balanceSeal(db.Model):  # NDE  # TODO - Paandi
    __tablename__ = "balanceSeal"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    balanceSeal_ = relationship('valveDetailsMaster', back_populates='balanceSeal__')


class studNut(db.Model):  # NDE  # TODO - Paandi
    __tablename__ = "studNut"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    studNut_ = relationship('valveDetailsMaster', back_populates='studNut__')


class gasket(db.Model):
    __tablename__ = "gasket"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    gasket_ = relationship('valveDetailsMaster', back_populates='gasket__')


class cageClamp(db.Model):
    __tablename__ = "cageClamp"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    cage_ = relationship('valveDetailsMaster', back_populates='cage__')


# To cv table
class balancing(db.Model):
    __tablename__ = "balancing"
    id = Column(Integer, primary_key=True)
    name = Column(String(300))

    balancing_c = relationship('cvTable', back_populates='balancing_')


# TODO dropdowns end

class valveDetailsMaster(db.Model):
    __tablename__ = "valveDetailsMaster"
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
    id = Column(Integer, primary_key=True)
    nominalDia = Column(Float)
    nominalPipeSize = Column(Float)
    outerDia = Column(Float)
    thickness = Column(Float)
    area = Column(Float)
    schedule = Column(String(50))

    # rel as parent
    caseI = relationship("caseMaster", back_populates="iPipe")
    # caseO = relationship("caseMaster", back_populates="oPipe")


class cvTable(db.Model):
    __tablename__ = "cvTable"
    id = Column(Integer, primary_key=True)
    # valveStyleId = Column(Integer)
    valveSize = Column(Float)
    series = Column(String(50))

    # rel as parent
    value = relationship("cvValues", back_populates="cv")
    case = relationship("caseMaster", back_populates="cv")
    torque = relationship("packingTorque", back_populates="cv")

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
    case = relationship("caseMaster", back_populates="fluid")


class caseMaster(db.Model):
    __tablename__ = "caseMaster"
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
    id = Column(Integer, primary_key=True)
    actuatorType = Column(String(100))
    springAction = Column(String(100))  # Fail Action
    handWheel = Column(String(100))
    orientation = Column(String(100))
    availableAirSupplyMin = Column(Float)
    availableAirSupplyMax = Column(Float)
    travelStops = Column(String(100))

    # rel as parent
    actCase = relationship('actuatorCaseData', back_populates='actuator_')

    # rel as child to item
    itemId = Column(Integer, ForeignKey("itemMaster.id"))
    item = relationship('itemMaster', back_populates='actuator')


class slidingActuatorData(db.Model):
    __tablename__ = "slidingActuatorData"
    id = Column(Integer, primary_key=True)
    actType = Column(String(100))
    failAction = Column(String(100))
    stemDia = Column(Float)
    yokeBossDia = Column(Float)
    actSize = Column(Float)
    effectiveArea = Column(Float)
    travel = Column(Float)
    sMin = Column(Float)
    sMax = Column(Float)
    springRate = Column(Float)
    VO = Column(Float)
    VM = Column(Float)

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', back_populates='slidingActuator')


class rotaryActuatorData(db.Model):
    __tablename__ = "rotaryActuatorData"
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
    actuatorCase = relationship('actuatorCaseData', back_populates='rotaryActuator')


class actuatorCaseData(db.Model):
    __tablename__ = "actuatorCaseData"
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


class packingFriction(db.Model):
    __tablename__ = "packingFriction"
    id = Column(Integer, primary_key=True)
    stemDia = Column(Float)
    value = Column(Float)

    # rel as child
    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship('ratingMaster', back_populates='packingF')

    packingMaterialId = Column(Integer, ForeignKey("packing.id"))
    packing_ = relationship('packing', back_populates='packingF')

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', back_populates='packingF')


class packingTorque(db.Model):
    __tablename__ = "packingTorque"
    id = Column(Integer, primary_key=True)
    shaftDia = Column(Float)

    # rel as child
    ratingId = Column(Integer, ForeignKey("ratingMaster.id"))
    rating = relationship('ratingMaster', back_populates='torque')

    cvId = Column(Integer, ForeignKey("cvTable.id"))
    cv = relationship('cvTable', back_populates='torque')

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', back_populates='packingT')


class seatLoadForce(db.Model):
    __tablename__ = "seatLoadForce"
    id = Column(Integer, primary_key=True)
    seatBore = Column(Float)
    value = Column(Float)

    # rel as parent
    actuatorCase = relationship('actuatorCaseData', back_populates='seatLoad')

    # rel as child
    trimTypeId = Column(Integer, ForeignKey("trimType.id"))
    trimType_ = relationship('trimType', back_populates='seatLoad')

    leakageClassId = Column(Integer, ForeignKey('seatLeakageClass.id'))
    leakage = relationship('seatLeakageClass', back_populates='seatLoad')


class seatingTorque(db.Model):
    __tablename__ = "seatingTorque"
    id = Column(Integer, primary_key=True)
    discDia = Column(Float)
    valveSize = Column(Float)
    cusc = Column(Float)
    cusp = Column(Float)

    actuatorCase = relationship('actuatorCaseData', back_populates='seatT')


class positioner(db.Model):
    __tablename__ = "positioner"
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
    id = Column(Integer, primary_key=True)
    make = Column(String(200))
    explosion = Column(String(200))
    moc = Column(String(200))
    sensor = Column(String(200))
    display = Column(String(200))
    model = Column(String(200))
    remark = Column(String(200))
    pressure_range = Column(String(200))


class solenoid(db.Model):
    __tablename__ = "solenoid"
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
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class paintCerts(db.Model):
    __tablename__ = "paintCerts"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class paintFinish(db.Model):
    __tablename__ = "paintFinish"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class certification(db.Model):
    __tablename__ = "certification"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class positionerSignal(db.Model):
    __tablename__ = "positionerSignal"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class accessoriesData(db.Model):
    __tablename__ = "accessoriesData"
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


class valveArea(db.Model):
    __tablename__ = "valveArea"
    id = Column(Integer, primary_key=True)
    rating = Column(String(300))
    nominalPipeSize = Column(String(300))
    inMM = Column(String(300))
    inInch = Column(String(300))
    area = Column(String(300))


class portArea(db.Model):
    __tablename__ = "portArea"
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
    id = Column(Integer, primary_key=True)
    failAction = Column(String(20))
    mount = Column(String(20))
    ac_size = Column(String(20))
    max_thrust = Column(String(20))
    dia = Column(String(20))


class knValue(db.Model):
    __tablename__ = "knValue"
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
    {'name': 'Pressure Temperature', 'db': pressureTempRating, 'id': 25}
]


### --------------------------------- Major Functions -----------------------------------------------------###

# Delete completed data in db table
def data_delete(table_name):
    with app.app_context():
        data_list = table_name.query.all()
        for data_ in data_list:
            db.session.delete(data_)
            db.session.commit()


def next_alpha(s):
    return chr((ord(s.upper()) + 1 - 65) % 26 + 65)


# Data upload function
def data_upload(data_list, table_name):
    with app.app_context():
        data_delete(table_name)
        for data_ in data_list:
            new_data = table_name(name=data_)
            db.session.add(new_data)
            db.session.commit()


def pressure_temp_upload(data_set):
    with app.app_context():
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
    with app.app_context():
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
        data_delete(cvTable)
        data_delete(cvValues)
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
    with app.app_context():
        data_delete(table_name)
        for style_index in range(len(valve_style)):
            for data in data_list[style_index]:
                new_data = table_name(name=data, style=valve_style[style_index])
                db.session.add(new_data)
                db.session.commit()


def data_upload_shaft(data_list, v_style_list):
    with app.app_context():
        data_delete(shaft)
        all_elements = []
        for style_ in v_style_list:
            for data_ in data_list:
                new_shaft = shaft(name=data_['name'], yield_strength=data_['yield_strength'], style=style_)
                all_elements.append(new_shaft)

        db.session.add_all(all_elements)
        db.session.commit()


def addProjectRels(cname, cnameE, address, addressE, aEng, cEng, project, operation):
    with app.app_context():
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
    with app.app_context():
        new_engineer = engineerMaster(name=name, designation=designation)
        db.session.add(new_engineer)
        db.session.commit()


def newUserProjectItem(user):
    with app.app_context():
        new_project = projectMaster(user=user,
                                    projectId=f"Q{date_today[2:4]}0000",
                                    enquiryReceivedDate=datetime.datetime.today(),
                                    receiptDate=datetime.datetime.today(),
                                    bidDueDate=datetime.datetime.today())
        new_item = itemMaster(project=new_project, itemNumber=1, alternate='A')
        new_valve = valveDetailsMaster(item=new_item)
        db.session.add_all([new_project, new_item, new_valve])
        db.session.commit()


def newProjectItem(project):
    with app.app_context():
        new_item = itemMaster(project=project, itemNumber=1, alternate='A')
        db.session.add(new_item)
        db.session.commit()
        new_valve_det = valveDetailsMaster(item=new_item)
        db.session.add(new_valve_det)
        db.session.commit()
        return new_item


def addNewItem(project, itemNumber, alternate):
    with app.app_context():
        new_item = itemMaster(project=project, itemNumber=itemNumber, alternate=alternate)
        db.session.add(new_item)
        db.session.commit()
        new_valve_det = valveDetailsMaster(item=new_item)
        db.session.add(new_valve_det)
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
    with app.app_context():
        address_ = []
        eng_ = []
        for project in all_projects:
            address_c = db.session.query(addressProject).filter_by(project=project, isCompany=True).first()
            eng_a = db.session.query(engineerProject).filter_by(project=project, isApplication=False).first()
            address_.append(address_c)
            eng_.append(eng_a)
        return address_, eng_


def getEngAddrProject(project):
    with app.app_context():
        address_c = db.session.query(addressProject).filter_by(project=project, isCompany=True).first()
        address_e = db.session.query(addressProject).filter_by(project=project, isCompany=False).first()
        eng_a = db.session.query(engineerProject).filter_by(project=project, isApplication=True).first()
        eng_c = db.session.query(engineerProject).filter_by(project=project, isApplication=False).first()
        return address_c, address_e, eng_a, eng_c


def getDBElementWithId(table_name, id):
    with app.app_context():
        output_element = db.session.query(table_name).filter_by(id=id).first()
        return output_element


date_today = datetime.datetime.now().strftime("%Y-%m-%d")


def metadata():
    with app.app_context():
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
            "units_dict": units_dict
        }
        return data_dict


### --------------------------------- Routes -----------------------------------------------------###


# TODO Login Module

@app.route('/admin-register', methods=["GET", "POST"])
def register():
    designations = designationMaster.query.all()
    departments = departmentMaster.query.all()
    # form = RegisterForm()
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

            if department_element.id == 5:
                addUserAsEng(request.form['name'], designation_element.name)

            # Add Project and Item
            newUserProjectItem(user=new_user)
            # login_user(new_user)
            # flash('Logged in successfully.')
            return redirect(url_for('login'))

    return render_template("admin-registration.html", designations=designations, departments=departments)


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
    with app.app_context():
        item_element = itemMaster.query.get(int(item_id))
        all_projects = db.session.query(projectMaster).filter_by(user=current_user).all()
        address_, eng_ = getEngAddrList(all_projects)
        items_list = db.session.query(itemMaster).filter_by(project=projectMaster.query.get(int(proj_id))).order_by(
            itemMaster.itemNumber.asc()).all()
        valve_list = [db.session.query(valveDetailsMaster).filter_by(item=item_).first() for item_ in items_list]
        return render_template('dashboard.html', user=current_user, projects=all_projects, address=address_, eng=eng_,
                               item=item_element, items=valve_list)


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
    itemNumberCurrent = int(item_element.itemNumber) + 1
    addNewItem(project=project_element, itemNumber=itemNumberCurrent, alternate='A')
    return redirect(url_for('home', proj_id=proj_id, item_id=item_id))


@app.route('/add-alternate/proj-<proj_id>/item-<item_id>', methods=['GET'])
def addAlternate(proj_id, item_id):
    item_element = getDBElementWithId(itemMaster, item_id)
    project_element = getDBElementWithId(projectMaster, item_element.project.id)
    itemNumberCurrent = int(item_element.itemNumber)
    alternateCurrent = next_alpha(item_element.alternate)
    addNewItem(project=project_element, itemNumber=itemNumberCurrent, alternate=alternateCurrent)
    return redirect(url_for('home', proj_id=proj_id, item_id=item_id))


@app.route('/preferences/proj-<proj_id>/item-<item_id>', methods=['GET'])
def preferences(proj_id, item_id):
    if request.method == 'POST':
        item_element = getDBElementWithId(itemMaster, item_id)
        project_element = getDBElementWithId(projectMaster, item_element.project.id)
        itemNumberCurrent = int(item_element.itemNumber)
        alternateCurrent = next_alpha(item_element.alternate)
        addNewItem(project=project_element, itemNumber=itemNumberCurrent, alternate=alternateCurrent)
        return redirect(url_for('home', proj_id=proj_id, item_id=item_id))
    return render_template('preferences.html', user=current_user, item=getDBElementWithId(itemMaster, item_id))


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
    return render_template('company.html', companies=all_company, user=current_user,
                           item=getDBElementWithId(itemMaster, item_id))


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
    return render_template('company-edit.html', user=current_user, company=company_element, addresses=addresses,
                           addresses_len=range(len_addr), item=getDBElementWithId(itemMaster, item_id))


@app.route('/del-address/<address_id>', methods=['GET', 'POST'])
def delAddress(address_id):
    addresss_element = addressMaster.query.get(address_id)
    company_id = addresss_element.company.id
    if addresss_element.isActive:
        addresss_element.isActive = False
    else:
        addresss_element.isActive = True
    db.session.commit()
    # db.session.delete(addresss_element)
    # db.session.commit()
    return redirect(url_for('companyEdit', company_id=company_id))


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
                               item=getDBElementWithId(itemMaster, item_id))


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
                           eng_c=eng_c_id)


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
                           metadata=metadata_, valve=valve_element)


@app.route('/valve-sizing/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def valveSizing(proj_id, item_id):
    metadata_ = metadata()
    return render_template('valvesizing.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_)


@app.route('/select-valve/proj-<proj_id>/item-<item_id>', methods=['GET', 'POST'])
def selectValve(proj_id, item_id):
    metadata_ = metadata()
    return render_template('selectvalve.html', item=getDBElementWithId(itemMaster, int(item_id)), user=current_user,
                           metadata=metadata_)


# Data View Module

@app.route('/view-data', methods=['GET', 'POST'])
def viewData():
    data2 = table_data_render
    return render_template('view_data.html', data=data2, page='viewData', user=current_user)


@app.route('/render-data/<topic>', methods=['GET'])
def renderData(topic):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    table_data = table_.query.all()
    print(table_.__tablename__)
    print(len(table_data))
    return render_template("render_data.html", data=table_data, topic=topic, page='renderData', name=name,
                           user=current_user)


@app.route('/download-data/<topic>', methods=['GET'])
def downloadData(topic):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    table_data = table_.query.all()
    with open('my_file.csv', 'w', newline='') as csvfile:
        # Create a CSV writer object
        writer = csv.writer(csvfile)

        # Write data to the CSV file
        if topic != '25':
            writer.writerow(['Id', 'Name'])
            for i in table_data:
                writer.writerow([i.id, i.name])
        elif topic == '25':
            writer.writerow(['Id', 'Max Temp', 'Min Temp', 'Pressure', 'Material', 'Rating'])
            for i in table_data:
                try:
                    writer.writerow([i.id, i.maxTemp, i.minTemp, i.pressure, i.material.name, i.rating.name])
                except AttributeError:
                    writer.writerow([i.id, i.maxTemp, i.minTemp, i.pressure, None, i.rating.name])

        # Close the CSV file
        csvfile.close()
    path = 'my_file.csv'
    return send_file(path, as_attachment=True, download_name=f"{table_.__tablename__}.csv")


@app.route('/upload-data/<topic>', methods=['GET', 'POST'])
def uploadData(topic):
    table_ = table_data_render[int(topic) - 1]['db']
    name = table_data_render[int(topic) - 1]['name']
    table_data = table_.query.all()

    if request.method == 'POST':
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

    return redirect(url_for('renderData', topic=topic))


if __name__ == "__main__":
    app.run(debug=False)
