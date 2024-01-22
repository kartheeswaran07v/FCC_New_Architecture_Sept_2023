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
length_unit_list = [{'id': 'inch', 'name': 'inch'}, {'id': 'm', 'name': 'm'}, {'id': 'mm', 'name': 'mm'},
                    {'id': 'cm', 'name': 'cm'}]

flowrate_unit_list = [{'id': 'm3/hr', 'name': 'm3/hr'}, {'id': 'scfh', 'name': 'scfh'},
                        {'id': 'gpm', 'name': 'gpm'},
                        {'id': 'lb/hr', 'name': 'lb/hr'}, {'id': 'kg/hr', 'name': 'kg/hr'}]

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
                        {'id': 'psia', 'name': 'psi (g)'}, {'id': 'psia', 'name': 'psi (a)'}]

temp_unit_list = [{'id': 'C', 'name': '°C'}, {'id': 'F', 'name': '°F'}, {'id': 'K', 'name': 'K'},
                    {'id': 'R', 'name': 'R'}]


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
length_unit_list = [{'id': 'inch', 'name': 'inch'}, {'id': 'm', 'name': 'm'}, {'id': 'mm', 'name': 'mm'},
                        {'id': 'cm', 'name': 'cm'}]
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

units_dict = {"pressure": pressure_unit_list, "temperature": temp_unit_list, "flowrate": flowrate_unit_list, "length": length_unit_list, "delPressure": del_p_unit_list}