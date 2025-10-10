

class PayCode:
    def __init__(self, id: int, name: str):
        self.id = id;
        self.name = name;



class Shift:
    def __init__(self, employee_name: str, date: str, shift_string: str):
        self.employee_name = employee_name;
        self.date = date;
        self.shift_string = shift_string;



class PayCodeShift:
    def __init__(self, employee_name: str, date: str, paycode: PayCode, hours: float):
        self.employee_name = employee_name;
        self.date = date;
        self.paycode = paycode;
        self.hours = hours;


