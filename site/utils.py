def name_month(month_number):
    """
    To convert month numbers to names.

    Params:
        month_number : integer 1 - 12

    Returns
        Month name
    """
    months = [
        'ENE', 'FEB', 'MAR', 
        'ABR', 'MAY', 'JUN', 
        'JUL', 'AGO', 'SEP',
        'OCT', 'NOV', 'DIC'
    ]
    return months[month_number - 1]

