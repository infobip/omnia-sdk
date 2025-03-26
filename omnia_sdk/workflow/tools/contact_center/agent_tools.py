from datetime import datetime

from holidays import country_holidays

# TODO: this module is not yet implemented

def is_holiday(country_code: str, date: datetime):
    return _get_holiday(country_code=country_code, date=date) is not None


def transfer_to_agent():
    print('you have been transferred to agent')


def time_aware_agent_transfer(country_code: str):
    if not _is_working_hours():
        raise Exception('please contact us within working hours...')
    if is_holiday(date=datetime.now(), country_code=country_code):
        raise Exception('We are not working due to Holidays...')
    transfer_to_agent()


# API
def _is_working_hours() -> bool:
    return True

def _get_holiday(country_code: str, date: datetime) -> bool:
    iso_holiday = country_holidays(country=country_code, expand=True, years=2024)
    return iso_holiday.get(date)
