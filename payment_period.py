from datetime import datetime, timedelta

class PaymentPeriod:
    def __init__(self, date):
        self.date = date

    def get_current_period(self):
        day = self.date.day
        if day <= 15:
            start_date = self.date.replace(day=1)
            end_date = self.date.replace(day=15)
        else:
            start_date = self.date.replace(day=16)
            next_month = self.date.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        return start_date, end_date

    def is_last_day_of_period(self):
        _, end_date = self.get_current_period()
        return self.date == end_date
