import time
from datetime import datetime

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
            if current_day == 'Sunday' and self._minutes_until_we_shutdown() > 120:
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
            if current_day == 'Sunday' and self._minutes_until_we_shutdown() > 120:
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

    # def is_quarter_hour(self):
    #     return time.localtime().tm_min % 15 == 0

    # def is_5_minutes(self):
    #     return time.localtime().tm_min % 5 == 0

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
    
    # def is_hour(self, hour: int = None):
    #     if hour is None:
    #         return time.localtime().tm_min == 0
    #     return time.localtime().tm_hour == hour and time.localtime().tm_min == 0
    
    # def is_half_hour(self):
    #     return time.localtime().tm_min == 30
    
    def is_day_of_list(self, days):
        return self._get_current_day().lower() in [d.lower() for d in days]
    
class PreviousDate:
    def __init__(self, tz=None):
        # tz can be something like zoneinfo.ZoneInfo("Europe/Brussels"); default is local time
        self.tz = tz
        self._dt = datetime.now(tz)

    def _now(self):
        return datetime.now(self.tz)

    # ---- “new” boundaries (since the moment this object was created/reset) ----
    def is_new_day(self):
        now = self._now()
        return self._dt.date() != now.date()

    def is_new_hour(self):
        now = self._now()
        return self._dt.replace(minute=0, second=0, microsecond=0) != now.replace(minute=0, second=0, microsecond=0)

    def is_new_minute(self):
        now = self._now()
        return self._dt.replace(second=0, microsecond=0) != now.replace(second=0, microsecond=0)

    # ---- elapsed time helpers (robust across midnight) ----
    def minutes_since(self):
        delta = self._now() - self._dt
        return int(delta.total_seconds() // 60)

    def more_than_ago(self, minutes: int = 0, hours: int = 0, days: int = 0):
        total_minutes = minutes + hours * 60 + days * 24 * 60
        return self.minutes_since() > total_minutes

    def has_been_quarter_hour(self):
        return self.minutes_since() >= 15

    def has_been_half_hour(self):
        return self.minutes_since() >= 30

    def has_been_hour(self):
        return self.minutes_since() >= 60