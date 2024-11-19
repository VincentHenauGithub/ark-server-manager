import time

class TimeHandler:
    def __init__(self, weekStartup=0, weekShutdown=0, weekendStartup=0, weekendShutdown=0):
        self.weekStartup = weekStartup
        self.weekShutdown = weekShutdown
        self.weekendStartup = weekendStartup
        self.weekendShutdown = weekendShutdown

    def _minutes_until_we_startup(self):
        return (self.weekendStartup * 60 - time.localtime().tm_hour * 60 - time.localtime().tm_min + 24 * 60) % (24 * 60)
    
    def _minutes_until_we_shutdown(self):
        return (self.weekendShutdown * 60 - time.localtime().tm_hour * 60 - time.localtime().tm_min + 24 * 60) % (24 * 60)
    
    def _minutes_until_wd_startup(self):    
        return (self.weekStartup * 60 - time.localtime().tm_hour * 60 - time.localtime().tm_min + 24 * 60) % (24 * 60)
    
    def _minutes_until_wd_shutdown(self):
        return (self.weekShutdown * 60 - time.localtime().tm_hour * 60 - time.localtime().tm_min + 24 * 60) % (24 * 60)
    
    def _get_current_day(self):
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][time.localtime().tm_wday]
    
    def time_until_next_restart(self):
        current_day = self._get_current_day()  # You might already have a way to determine the current day.
        
        if self.is_weekend():
            # Special case for Sunday: follow weekday schedule
            if current_day == 'Sunday':
                if self._minutes_until_we_startup() < self._minutes_until_wd_shutdown():
                    return self._minutes_until_we_startup()
                else:
                    return self._minutes_until_wd_shutdown()
            # Standard weekend case
            else:
                if self._minutes_until_we_startup() < self._minutes_until_we_shutdown():
                    return self._minutes_until_we_startup()
                else:
                    return self._minutes_until_we_shutdown()
        else:
            # Special case for Friday: follow weekend schedule for shutdown
            if current_day == 'Friday':
                if self._minutes_until_wd_startup() < self._minutes_until_we_shutdown():
                    return self._minutes_until_wd_startup()
                else:
                    return self._minutes_until_we_shutdown()
            # Standard weekday case
            else:
                if self._minutes_until_wd_startup() < self._minutes_until_wd_shutdown():
                    return self._minutes_until_wd_startup()
                else:
                    return self._minutes_until_wd_shutdown()
                        
    def is_next_restart_playable(self):
        current_day = self._get_current_day()  # You might already have a way to determine the current day.
        
        if self.is_weekend():
            # Special case for Sunday: follow weekday schedule
            if current_day == 'Sunday':
                return self._minutes_until_we_startup() < self._minutes_until_wd_shutdown()
            # Standard weekend case
            else:
                return self._minutes_until_we_startup() < self._minutes_until_we_shutdown()
        else:
            # Special case for Friday: follow weekend schedule for shutdown
            if current_day == 'Friday':
                return self._minutes_until_wd_startup() < self._minutes_until_we_shutdown()
            # Standard weekday case
            else:
                return self._minutes_until_wd_startup() < self._minutes_until_wd_shutdown()

    def is_quarter_hour(self):
        return time.localtime().tm_min % 15 == 0

    def is_5_minutes(self):
        return time.localtime().tm_min % 5 == 0

    def is_weekend(self):
        return time.localtime().tm_wday in [5, 6]

    def is_weekday(self):
        return time.localtime().tm_wday in [0, 1, 2, 3, 4]

    def minutes_until_midnight(self):
        return 24*60 - time.localtime().tm_hour*60 - time.localtime().tm_min

    def minutes_until_5_pm(self):
        return 17*60 - time.localtime().tm_hour*60 - time.localtime().tm_min
    
    def get_hr_min_string(self):
        return f"{time.localtime().tm_hour}:{time.localtime().tm_min:02d}"
    
    def is_day(self, day: str):
        return self._get_current_day().lower() == day.lower()
    
    def is_day_of_list(self, days):
        return self._get_current_day().lower() in [d.lower() for d in days]
    
class PreviousDate:
    def __init__(self):
        self.minute = time.localtime().tm_min
        self.hour = time.localtime().tm_hour
        self.date = time.localtime().tm_mday
        self.month = time.localtime().tm_mon
        self.year = time.localtime().tm_year

    def is_new_day(self):
        return self.date != time.localtime().tm_mday or self.month != time.localtime().tm_mon or self.year != time.localtime().tm_year
    
    def is_new_hour(self):
        return self.hour != time.localtime().tm_hour
    
    def is_new_minute(self):
        return self.minute != time.localtime().tm_min
    
    def  minutes_since(self):
        return (time.localtime().tm_hour - self.hour) * 60 + time.localtime().tm_min - self.minute