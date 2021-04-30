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
    try: 
        return months[int(month_number) - 1]
    except:
        return "ND"

