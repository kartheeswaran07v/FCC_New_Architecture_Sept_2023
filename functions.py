# To get running numbers for customer master
def full_format(i):
    # limit of first range is 26 letters (A-Z) times 999 numbers (001-999)
    if i < 26 * 999:
        c,n = divmod(i,999)   # quotient c is index of letter 0-25, remainder n is 0-998
        c = chr(ord('A') + c) # compute letter
        n += 1
        return f'{c}{n:03}'
    # After first range, second range is 26 letters times 26 letters * 99 numbers (01-99)
    elif i < 26*999 + 26*26*99:
        i -= 26*999               # remove first range offset
        cc,n = divmod(i,99)       # remainder n is 0-98, use quotient cc to compute two letters
        c1,c2 = divmod(cc,26)     # c1 is index of first letter, c2 is index of second letter
        c1 = chr(ord('A') + c1)   # compute first letter
        c2 = chr(ord('A') + c2)   # compute second letter
        n += 1
        return f'{c1}{c2}{n:02}'
    else:
        raise OverflowError(f'limit is {26*999+26*26*99}')
    


project_status_list = ['Dead', 'Live', 'Lost', 'Regret', 'Won']
purpose_list = ['Bid On', 'Budget', 'Example', 'Order To Place', 'Technical']
# length_unit_list = [{'id': 'inch', 'name': 'inch'}, {'id': 'm', 'name': 'm'}, {'id': 'mm', 'name': 'mm'},
#                     {'id': 'cm', 'name': 'cm'}]

# flowrate_unit_list = [{'id': 'm3/hr', 'name': 'm3/hr'}, {'id': 'scfh', 'name': 'scfh'},
#                         {'id': 'gpm', 'name': 'gpm'},
#                         {'id': 'lb/hr', 'name': 'lb/hr'}, {'id': 'kg/hr', 'name': 'kg/hr'}]

# pressure_unit_list = [{'id': 'bar', 'name': 'bar (a)'}, {'id': 'bar', 'name': 'bar (g)'},
#                         {'id': 'kpa', 'name': 'kPa (a)'}, {'id': 'kpa', 'name': 'kPa (g)'},
#                         {'id': 'mpa', 'name': 'MPa (a)'}, {'id': 'mpa', 'name': 'MPa (g)'},
#                         {'id': 'pa', 'name': 'Pa (a)'}, {'id': 'pa', 'name': 'Pa (g)'},
#                         {'id': 'inh20', 'name': 'in H2O (a)'}, {'id': 'inh20', 'name': 'in H2O (g)'},
#                         {'id': 'inhg', 'name': 'in Hg (a)'}, {'id': 'inhg', 'name': 'in Hg (g)'},
#                         {'id': 'kg/cm2', 'name': 'kg/cm2 (a)'}, {'id': 'kg/cm2', 'name': 'kg/cm2 (g)'},
#                         {'id': 'mmh20', 'name': 'm H2O (a)'}, {'id': 'mmh20', 'name': 'm H2O (g)'},
#                         {'id': 'mbar', 'name': 'mbar (a)'}, {'id': 'mbar', 'name': 'mbar (g)'},
#                         {'id': 'mmhg', 'name': 'mm Hg (a)'}, {'id': 'mmhg', 'name': 'mm Hg (g)'},
#                         {'id': 'psia', 'name': 'psi (g)'}, {'id': 'psia', 'name': 'psi (a)'}]

# temp_unit_list = [{'id': 'C', 'name': '°C'}, {'id': 'F', 'name': '°F'}, {'id': 'K', 'name': 'K'},
#                     {'id': 'R', 'name': 'R'}]


def reorder_list(element, list_):
    if type(list_) == list:
        list_.pop(list_.index(element))
        list_.insert(0, element)
        return list_
    elif type(list_) == dict:
        list__ = list(list_.keys())
        list__.pop(list__.index(element))
        list__.insert(0, element)
        return list__





def notes_dict_reorder(input_dict, company, address):
    print(f"{input_dict}")
    output_dict = {}
    key_list_ = list(input_dict.keys())
    key_list = reorder_list(company, key_list_)
    for keys_ in key_list:
        if keys_ == company:
            addresses_ = input_dict[keys_]
            address_reorder = reorder_list(address, addresses_)
            output_dict[keys_] = address_reorder
        else:
            output_dict[keys_] = input_dict[keys_]
    return output_dict


temperature_unit_list = [{"id": "C", "name": "°C"}, {"id": "F", "name": "°F"}, {"id": "R", "name": "R"}, {"id": "K", "name": "K"}]
length_unit_list = [{'id': 'inch', 'name': 'inch'}, {'id': 'mm', 'name': 'mm'}]
pressure_unit_list = [{'id': 'bar', 'name': 'bar (a)'}, {'id': 'bar', 'name': 'bar (g)'},
                          {'id': 'kpa', 'name': 'kPa (a)'}, {'id': 'kpa', 'name': 'kPa (g)'},
                          {'id': 'mpa', 'name': 'MPa (a)'}, {'id': 'mpa', 'name': 'MPa (g)'},
                          {'id': 'pa', 'name': 'Pa (a)'}, {'id': 'pa', 'name': 'Pa (g)'},
                          {'id': 'inh20', 'name': 'in H2O (a)'}, {'id': 'inh20', 'name': 'in H2O (g)'},
                          {'id': 'inhg', 'name': 'in Hg (a)'}, {'id': 'inhg', 'name': 'in Hg (g)'},
                          {'id': 'kg/cm2', 'name': 'kg/cm2 (a)'}, {'id': 'kg/cm2', 'name': 'kg/cm2 (g)'},
                          {'id': 'mmh20', 'name': 'm H2O (a)'}, {'id': 'mmh20', 'name': 'm H2O (g)'},
                          {'id': 'mbar', 'name': 'mbar (a)'}, {'id': 'mbar', 'name': 'mbar (g)'},
                          {'id': 'mmhg', 'name': 'mm Hg (a)'}, {'id': 'mmhg', 'name': 'mm Hg (g)'},
                          {'id': 'psia', 'name': 'psi (g)'}, {'id': 'psia', 'name': 'psi (a)'},
                          {'id': 'atm', 'name': 'atm (g)'}, {'id': 'atm', 'name': 'atm (a)'},
                          {'id': 'torr', 'name': 'torr (g)'}, {'id': 'torr', 'name': 'torr (a)'}]
flowrate_unit_list = [{'id': 'm3/hr', 'name': 'm3/hr'}, {'id': 'scfh', 'name': 'scfh'},
                          {'id': 'gpm', 'name': 'gpm'},
                          {'id': 'lb/hr', 'name': 'lb/hr'}, {'id': 'kg/hr', 'name': 'kg/hr'}]

del_p_unit_list = [{'id': 'bar', 'name': 'bar'},
                          {'id': 'kpa', 'name': 'kPa'},
                          {'id': 'mpa', 'name': 'MPa'}, 
                          {'id': 'pa', 'name': 'Pa'}, 
                          {'id': 'inh20', 'name': 'in H2O'}, 
                          {'id': 'inhg', 'name': 'in Hg'}, 
                          {'id': 'kg/cm2', 'name': 'kg/cm2'}, 
                          {'id': 'mmh20', 'name': 'm H2O'}, 
                          {'id': 'mbar', 'name': 'mbar'}, 
                          {'id': 'mmhg', 'name': 'mm Hg'}, 
                          {'id': 'psia', 'name': 'psi'}, 
                          {'id': 'atm', 'name': 'atm'}, 
                          {'id': 'torr', 'name': 'torr'}, ]

pipe_schedule = ['std', 10, 20, 30, 40, 80, 120, 160, 'xs', 'xxs']

pipe_shedule_list = [{"id": item, "name": item} for item in pipe_schedule]

units_dict = {"pressure": pressure_unit_list, "temperature": temperature_unit_list, "flowrate": flowrate_unit_list, "length": length_unit_list, "delPressure": del_p_unit_list, "pipe_schedule": pipe_shedule_list}

# Unit Conversion Logic
def convert_L_SI(val, unit_in, unit_out, density):
    SI = {'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'km': 1000.0, 'inch': 0.0254}
    return val * SI[unit_in] / SI[unit_out]


def conver_P_SI(val, unit_in, unit_out, density):
    SI = {'psia': 6894.76, 'kg/cm2': 98066.5, 'pa': 1, 'kpa': 1000, 'bar': 100000, 'mpa': 1000000,
          'inh20': 0.00401865, 'mmh20': 0.10197162129, 'inhg': 0.0002953, 'mmhg': 0.00750062, 'mbar': 0.01}
    return val * SI[unit_in] / SI[unit_out]




def convert_T_SI(val, unit_in, unit_out, density):
    def c_to_c(value):
        return value

    def c_to_f(value):
        return 1.8 * value + 32

    def c_to_k(value):
        return value + 273.15

    def c_to_r(value):
        return 1.8 * value + 491.67

    def f_to_c(value):
        return (value - 32) * (5 / 9)

    def k_to_c(value):
        return value - 273.15

    def r_to_c(value):
        return (value - 491.67) * (5 / 9)

    SI = {'F': c_to_f, 'K': c_to_k, 'R': c_to_r, 'C': c_to_c}
    SI_2 = {'F': f_to_c, 'K': k_to_c, 'R': r_to_c, 'C': c_to_c}

    # val_to_c = SI[unit_in](val)
    return SI[unit_out](SI_2[unit_in](val))


def conver_FR_SI(val, unit_in, unit_out, density):
    SI = {'m3/hr': 1, 'scfh': 1 / 35.31, 'gpm': 1 / 4.402868, 'lb/hr': 1 / (2.2 * density), 'kg/hr': 1 / density}
    return val * SI[unit_in] / SI[unit_out]


def meta_convert_P_T_FR_L(prop, val, unit_in, unit_out, density):
    properties = {"T": convert_T_SI, "P": conver_P_SI, "FR": conver_FR_SI, "L": convert_L_SI}
    return properties[prop](val, unit_in, unit_out, density)


def conver_FR_noise(val, unit_in):
    SI = {'m3/hr': 0.001, 'scfh': 0.049, 'gpm': 0.0060, 'lb/hr': 2.20462, 'kg/hr': 1}
    a = (val * SI[unit_in] / SI['kg/hr']) / 3600
    return a


N1 = {('m3/hr', 'kpa'): 0.0865, ('m3/hr', 'bar'): 0.865, ('gpm', 'psia'): 1}
N2 = {'mm': 0.00214, 'inch': 890}
N4 = {('m3/hr', 'mm'): 76000, ('gpm', 'inch'): 173000}


# FR values for 56-40000

REv = [56, 66, 79, 94, 110, 130, 154, 188, 230, 278, 340, 471, 620, 980, 1560, 2470, 4600, 10200, 40000]
FR = [0.284, 0.32, 0.36, 0.4, 0.44, 0.48, 0.52, 0.56, 0.6, 0.64, 0.68, 0.72, 0.76, 0.8, 0.84, 0.88, 0.92, 0.96, 1]

def getValveType(valveStyle):
    valve_dict = {'Globe Straight': 'globe', 'Globe Angle': 'globe', 'Butterfly Lugged Wafer': 'butterfly', 'Butterfly Double Flanged': 'butterfly'}
    return valve_dict[valveStyle]



# Constants
# todo = Constants
N5_mm = 0.00241  # in mm
N5_in = 1000
N6_kghr_kPa_kgm3 = 2.73
N6_kghr_bar_kgm3 = 27.3
N6_lbhr_psi_lbft3 = 63.3
N7_O_m3hr_kPa_C = 3.94  # input in Kelvin
N7_0_m3hr_bar_C = 394
N7_155_m3hr_kPa_C = 4.17
N7_155_m3hr_bar_C = 417
N7_60_scfh_psi_F = 1360  # input in R
N8_kghr_kPa_K = 0.498
N8_kghr_bar_K = 94.8
N8_lbhr_psi_K = 19.3
N9_O_m3hr_kPa_C = 21.2  # input in Kelvin
N9_0_m3hr_bar_C = 2120
N9_155_m3hr_kPa_C = 22.4
N9_155_m3hr_bar_C = 2240
N9_60_scfh_psi_F = 7320  # input in R

def getFlowCharacter(flowcharacter):
    flowcharact_dict = {'Equal %': 'equal', 'Linear': 'linear', 'Modified Equal %': 'equal'}
    return flowcharact_dict[flowcharacter]


actuator_type_dict = [
      {'id': 'Manual Gearbox', 'name': 'Manual Gearbox'},
      {'id': 'Spring & Diaphragam', 'name': 'Spring & Diaphragam'},
      {'id': 'Multi Spring & Diaphragam', 'name': 'Multi Spring & Diaphragam'},
      {'id': 'Piston with Spring', 'name': 'Piston with Spring'},
      {'id': 'Piston without Spring', 'name': 'Piston without Spring'},
      {'id': 'SY', 'name': 'Scotch Yoke'},
      {'id': 'SYC', 'name': 'Scotch Yoke-Canted'},
      {'id': 'SYCDA', 'name': 'Scotch Yoke-Canted Double Acting'},
      ]

fail_action_dict = [
      {'id': 'DA', 'name': 'Stay Put'},
      {'id': 'AFO', 'name': 'Fail Open'},
      {'id': 'AFC', 'name': 'Fail Close'}
      ]


hand_wheel_dict = [
      {'id': 'None', 'name': 'N/A'},
      {'id': 'Side Mounted', 'name': 'Side Mounted'},
      {'id': 'Top Mounted', 'name': 'Top Mounted'}
      ]


orientaton_dict = [
      {'id': 'None', 'name': 'N/A'},
      {'id': 'Horizontal', 'name': 'Horizontal'},
      {'id': 'Vertical', 'name': 'Vertical'}
      ]

adjustable_travel_stops_dict = [
      {'id': 'None', 'name': 'N/A'},
      {'id': 'Limit Open', 'name': 'Limit Open'},
      {'id': 'Limit Close', 'name': 'Limit Close'}
      ]


actuator_data_dict = {'actType': actuator_type_dict,
                      'failAction': fail_action_dict,
                      'handwheel': hand_wheel_dict, 
                      'orientation': orientaton_dict,
                      'travel': adjustable_travel_stops_dict
                      }



valve_force_dict = [{'key': ('contour', 'unbalanced', 'under', 'shutoff'), 'formula': 1},
                    {'key': ('cage', 'unbalanced', 'under', 'shutoff'), 'formula': 2},
                    {'key': ('cage', 'unbalanced', 'over', 'shutoff'), 'formula': 3},
                    {'key': ('cage', 'balanced', 'under', 'shutoff'), 'formula': 4},
                    {'key': ('cage', 'balanced', 'over', 'shutoff'), 'formula': 5},
                    {'key': ('contour', 'unbalanced', 'under', 'shutoff+'), 'formula': 6},
                    {'key': ('cage', 'unbalanced', 'under', 'shutoff+'), 'formula': 7},
                    {'key': ('cage', 'unbalanced', 'over', 'shutoff+'), 'formula': 8},
                    {'key': ('cage', 'balanced', 'under', 'shutoff+'), 'formula': 9},
                    {'key': ('cage', 'balanced', 'over', 'shutoff+'), 'formula': 10},
                    {'key': ('contour', 'unbalanced', 'under', 'close'), 'formula': 11},
                    {'key': ('cage', 'unbalanced', 'under', 'close'), 'formula': 12},
                    {'key': ('cage', 'unbalanced', 'over', 'close'), 'formula': 13},
                    {'key': ('cage', 'balanced', 'under', 'close'), 'formula': 14},
                    {'key': ('cage', 'balanced', 'over', 'close'), 'formula': 15},
                    {'key': ('contour', 'unbalanced', 'under', 'open'), 'formula': 16},
                    {'key': ('cage', 'unbalanced', 'under', 'open'), 'formula': 17},
                    {'key': ('cage', 'unbalanced', 'over', 'open'), 'formula': 18},
                    {'key': ('cage', 'balanced', 'under', 'open'), 'formula': 19},
                    {'key': ('cage', 'balanced', 'over', 'open'), 'formula': 20},
                    ]

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