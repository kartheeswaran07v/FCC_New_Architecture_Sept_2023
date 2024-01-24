import math

service_cond_1 = {'flowrate': 55.556, 'fl_unit': 'kg/s', 'iPres': 1000000, 'iPresUnit': 'pa', 'oPres': 600000,
                  'oPresUnit': 'pa',
                  'specificHeatRatio_gamma': 1.09, 'MW': 58.12, 'mw_unit': 'kg/Kmol', 'inletTemp': 303.15,
                  'iTempUnit': 'K',
                  'R': 8314, 'R_unit': 'J/Kmol-K', 'valveDia': 0.3048, 'valveDiaUnit': 'm', 'iPipeDia': 0.610,
                  'iPipeDiaUnit': 'm',
                  'oPipeDia': 0.610, 'oPipeDiaUnit': 'm'}


# pressure in pa, temp in K, length in m, fl in kg/s


def inletDensity(iPres, MW, R, iTemp):
    a_ = iPres * MW / (R * iTemp)
    return round(a_, 2)


#
# print(inletDensity(service_cond_1['iPres'], service_cond_1['MW'], service_cond_1['R'], service_cond_1['inletTemp']))


# outlet Density
def outletDensity(iPres, oPres, MW, R, iTemp):
    Pi = inletDensity(iPres, MW, R, iTemp)
    a = Pi * (oPres / iPres)
    return round(a, 2)


#
# print(outletDensity(service_cond_1['iPres'], service_cond_1['oPres'], service_cond_1['MW'], service_cond_1['R'],
#                     service_cond_1['inletTemp']))


def sonicVelocity(gamma, MW, R, iTemp):
    a__ = gamma * R * iTemp / MW
    a_ = math.sqrt(a__)
    return round(a_, 3)


#
# print(sonicVelocity(service_cond_1['specificHeatRatio_gamma'], service_cond_1['MW'], service_cond_1['R'],
#                     service_cond_1['inletTemp']))


# mach no for valve outlet and downstream pipe and upstream
def MO(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia, p_factor):
    p2 = outletDensity(iPres, oPres, MW, R, iTemp)
    p1 = inletDensity(iPres, MW, R, iTemp)
    c2 = sonicVelocity(gamma, MW, R, iTemp)
    # print(p2, c2)
    if p_factor == 'up':
        a_ = math.pi * iPipeDia * iPipeDia * p1 * c2
    elif p_factor == 'down':
        a_ = math.pi * oPipeDia * oPipeDia * p2 * c2
    else:
        a_ = math.pi * valveDia * valveDia * p2 * c2

    a = 4 * massflowrate / a_
    print(f"p1: {p1}, P2: {p2}, c2: {c2}, iPipeDia: {iPipeDia}, {oPipeDia}, massflowrate: {massflowrate}")
    if a > 1:
        a = 1
    return round(a, 4)


# print(
#     MO(service_cond_1['specificHeatRatio_gamma'], service_cond_1['iPres'], service_cond_1['oPres'], service_cond_1['R'],
#        service_cond_1['inletTemp'], service_cond_1['MW'], service_cond_1['flowrate'], service_cond_1['valveDia'],
#        service_cond_1['iPipeDia'], service_cond_1['oPipeDia'], 'down'))


def getGasVelocities(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia):
    up_sonic = sonicVelocity(gamma, MW, R, iTemp)
    down_sonic = sonicVelocity(gamma, MW, R, iTemp)
    v_sonic = sonicVelocity(gamma, MW, R, iTemp)
    up_mach = MO(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia, 'up')
    down_mach = MO(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia, 'down')
    v_mach = MO(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia, 'valve')
    up_velocity = up_mach * up_sonic
    down_velocity = down_mach * down_sonic
    v_velocity = v_mach * v_sonic
    p2 = outletDensity(iPres, oPres, MW, R, iTemp)
    output_list = [up_mach, down_mach, v_mach, up_sonic, down_sonic, v_sonic, round(up_velocity, 3),
                   round(down_velocity, 3), round(v_velocity, 3), p2]
    # print(gamma, iPres, oPres, R, iTemp, MW, massflowrate, valveDia, iPipeDia, oPipeDia)
    return output_list


#
#
# print(getGasVelocities(service_cond_1['specificHeatRatio_gamma'], service_cond_1['iPres'], service_cond_1['oPres'],
#                        service_cond_1['R'],
#                        service_cond_1['inletTemp'], service_cond_1['MW'], service_cond_1['flowrate'],
#                        service_cond_1['valveDia'],
#                        service_cond_1['iPipeDia'], service_cond_1['oPipeDia']))

# print(getGasVelocities(1.09, 1000000, 900000,
#                        8314,
#                        403.15, 58.12, 0.694,
#                        0.1016,
#                        0.1016, 0.1016))
