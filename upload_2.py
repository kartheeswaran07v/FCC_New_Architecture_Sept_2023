from datetime import datetime
from main import cageClamp, data_upload_shaft, db, app, deleteCVDuplicates, endConnection, endFinish, fluidProperties, gasket, industryMaster, limitSwitch, notesMaster, packing, packingType, pipeArea, positioner, pressure_temp_upload, \
    regionMaster, fluidState, designStandard, rotaryActuatorData, seat, seatLeakageClass, shaft, slidingActuatorData, solenoid, studNut, valveArea, valveStyle, applicationMaster, \
    ratingMaster, materialMaster, data_upload, add_many, afr, balanceSeal, bonnet, bonnetType, certification, \
    cleaning, flowDirection, trimType, flowCharacter, balancing, cv_upload, data_upload_disc_seat_packing, disc, \
    departmentMaster, designationMaster, packing_friction_upload
import csv





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




# print(getRowsFromCsvFile("csv/afr.csv"))
# print(getRowsFromCsvFile("csv/cvtable.csv")[::6])
# print(getRowsFromCsvFile("csv/shaft.csv"))


with app.app_context():
    # data_upload(valve_style_list, valveStyle)
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
    # # data_upload(trim_type_list, trimType)
    # data_upload(flow_charac_list, flowCharacter)
    # data_upload(balancing_list, balancing)
    # # cv_upload(getRowsFromCsvFile("csv/cvtable_small.csv"))
    # cv_upload(getRowsFromCsvFile("csv/cvtable.csv"))
    # deleteCVDuplicates()
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
    # add_many(getRowsFromCsvFile("csv/limit_switch.csv"), limitSwitch)
    # add_many(getRowsFromCsvFile("csv/solenoid.csv"), solenoid)
    # pressure_temp_upload(getRowsFromCsvFile("csv/pressureTemp.csv"))
    # packing_friction_upload(getRowsFromCsvFile("csv/packing_friction.csv"))
    pass


# region___list = ['North America', 'South America', 'European Union', 
#                'Indian Subcontinent', 'South East Asia And Japan', 'Africa', 
#                'Australia / New Zealand', 'China', 'Middle Asia']
# region_dict = []
# for region_ in region___list:
#     abc_ = {'name': region_}
#     region_dict.append(abc_)

# print(region_dict)

# deploy 1
abc = getRowsFromCsvFile("csv/hydrasave-country.csv")
print(abc)
# print(getList(abc[0]))
valve_table_keys = [
  'id',
  'quantity',
  'tagNumber',
  'serialNumber',
  'shutOffDelP',
  'maxPressure',
  'maxTemp',
  'minTemp',
  'shutOffDelPUnit',
  'maxPressureUnit',
  'maxTempUnit',
  'minTempUnit',
  'bonnetExtDimension',
  'application',
  'itemId',
  'ratingId',
  'materialId',
  'designStandardId',
  'valveStyleId',
  'fluidStateId',
  'endConnectionId',
  'endFinishId',
  'bonnetTypeId',
  'packingTypeId',
  'trimTypeId',
  'flowCharacterId',
  'flowDirectionId',
  'seatLeakageClassId',
  'bonnetId',
  'nde1Id',
  'nde2Id',
  'shaftId',
  'discId',
  'seatId',
  'packingId',
  'balanceSealId',
  'studNutId',
  'gasketId',
  'cageId'
]

# valve_table_dict = {}
# for val_ in valve_table_keys[15:]:
#     valve_table_dict[val_] = ""
# print(valve_table_dict)

# print(len(valve_table_keys))
# print(valve_table_keys[:15])