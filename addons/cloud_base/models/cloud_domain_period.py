#coding: utf-8

from dateutil.relativedelta import relativedelta
from datetime import date

from odoo import  _, api, fields, models

def return_start_and_end(interval, ttype, inclusive, period_direction):
    """
    The method to return start and end date based on interval

    1. If inclusive, it means we consider the current period as independant one. E.g. Today is 25/08.
       One last month inclusive means, we consider 01/08 - 31/08. Exclusive would be 01/07-31/07
       One next month inclusive means, we consider 01/08 - 31/08. Exclusive would be 01/09-30/09
    2. We take time_delta for start point (end point for the 'next).
    3. We take time_delta for the opposite point
    4. We calculate start and end based on time_deltas

    Args:
     * interval - int
     * ttype - 'days', 'weeks', 'months', 'years'
     * inclusive - boolean
     * period_direction - either 'last' or 'next'

    Returns:
     * date.date, date.date
    """
    today = date.today()
    # 1
    the_next_interval = 0
    if period_direction == 'next':
        if not inclusive:
            the_next_interval = 1
            interval += 1
    elif inclusive:
        the_next_interval = 1
        interval -= 1
    # 2
    days = ttype == 'days' and interval or 0
    weeks = ttype == 'weeks' and interval or 0
    months = ttype == 'months' and interval or 0
    years = ttype == 'years' and interval or 0
    period_delta = relativedelta(days=days, weeks=weeks, months=months, years=years)
    # 3
    days = ttype == 'days' and the_next_interval or 0
    weeks = ttype == 'weeks' and the_next_interval or 0
    months = ttype == 'months' and the_next_interval or 0
    years = ttype == 'years' and the_next_interval or 0
    period_delta_2 = relativedelta(days=days, weeks=weeks, months=months, years=years)
    # 4
    calculated_start = calculated_end = today
    if period_direction == 'next':
        calculated_start = today + period_delta_2
        calculated_end  = today + period_delta
    else:
        calculated_start = today - period_delta
        calculated_end = today + period_delta_2
    return calculated_start, calculated_end

def return_the_first_month_or_year_date(calc_date, year=False):
    """
    The method to return first date of the month or year

    Args:
     * calc_date - date.date
     * year - in case it should be the first day of year

    Returns:
     * date.date
    """
    month = year and 1 or calc_date.month
    return date(year=calc_date.year, month=month, day=1,)


class cloud_domain_period(models.Model):
    """
    The model to construct relative day domains
    """
    _name = "cloud.domain.period"
    _description = 'Relative Period'

    @api.depends("field_id", "period_value", "period_type", "inclusive_this", "period_direction")
    def _compute_domain(self):
        """
        Compute method for domain
        It is not stored, since the date depends on today

        1. For days: we just take calculated dates
        2. Foe weeks: we take the first week date for both start and. Note (!): from Monday to Sunday
        3. For months: we take the first month day for both start and end
        4. For years: we take the first year day for both start and end
        5. Date end is 1 day deducted to show the period inclusive, not exlusive last date

        Methods:
         * return_start_and_end
         * return_the_first_month_or_year_date
         * _return_translation_for_field_label
        """
        for period in self:
            domain = "[]"
            title = False
            field = period.field_id
            interval = period.period_value
            interval_type = period.period_type
            inclusive = period.inclusive_this
            period_direction = period.period_direction
            if field and interval > 0 and interval_type and period_direction:
                calculated_start, calculated_end = return_start_and_end(
                    interval=interval,
                    ttype=interval_type,
                    inclusive=inclusive,
                    period_direction=period_direction,
                )
                # 1
                if interval_type == 'weeks':
                    # 2
                    calculated_start = calculated_start - relativedelta(days=calculated_start.weekday())
                    calculated_end = calculated_end - relativedelta(days=calculated_end.weekday())
                elif interval_type == 'months':
                    # 3
                    calculated_start = return_the_first_month_or_year_date(calculated_start)
                    calculated_end = return_the_first_month_or_year_date(calculated_end)
                elif interval_type == 'years':
                    # 4
                    calculated_start = return_the_first_month_or_year_date(calculated_start, year=True)
                    calculated_end = return_the_first_month_or_year_date(calculated_end, year=True)

                domain = "['&', ['{a}', '<', '{b}'], ['{a}', '>=', '{c}']]".format(
                    a=field.name,
                    b=calculated_end,
                    c=calculated_start,
                )
                # 5
                title = "{} - {}".format(calculated_start, calculated_end-relativedelta(days=1))
            period.domain = domain
            period.title = title


    sync_model_id = fields.Many2one("sync.model", string="Sync Model")
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Date",
        required=True,
        ondelete="cascade",
    )
    period_direction = fields.Selection(
        [
            ("last", "the last"),
            ("next", "the next"),
        ],
        string="In",
        default="last",
        required=True,
    )
    period_value = fields.Integer(
        "Interval",
        required=True,
        default=1,
    )
    period_type = fields.Selection(
        [
            ("days", "days"),
            ("weeks", "weeks"),
            ("months", "months"),
            ("years", "years"),
        ],
        string="Interval Type",
        required=True,
        default="months",
    )
    inclusive_this = fields.Boolean(
        string="Including current",
        help="""
            If checked, it means that the current period is also included.
            E.g. today is 25/09/2018. We selected 'the last 2 months'. If not checked,
            Odoo would consider July and August. If checked, August and September
        """,
    )
    domain = fields.Text(string="Domain", compute=_compute_domain)
    title = fields.Char(string="Title", compute=_compute_domain)

    _sql_constraints = [('period_value_check', 'check (period_value>0)', _('Interval should be positive!'))]

    _order = "field_id, id"
