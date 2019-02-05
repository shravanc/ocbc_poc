class Ocbc:
    def __init__(self, name="", date="", gaurantors=[]):
        self.name = name
        self.date = date
        self.gaurantors = gaurantors
       

    def to_json(self):
        return {'registration_name': self.name, 'date_of_incorporation': self.date, 'gaurantors': self.gaurantors} 
