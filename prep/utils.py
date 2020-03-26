import unicodedata

def num_to_code(col, zeros=0):
    col_zfill = lambda value: value.zfill(zeros)
    try:
        ret = col.apply(int).apply(str).apply(col_zfill)
    except:
        ret = col.copy()
    return ret

def set_as_codes(data, cols):
    for col in cols.keys():
        data.loc[col] = num_to_code(data[col], cols[col])

def asciify(s):
    """
    This function is used to convert non-ascii characters
    like accented vowels to ascci.

    Parameter:

        s : string to be converted to ascii

    Return:

        An only-ascii-character string
    """
    return unicodedata.normalize('NFKD', s)\
        .encode('ascii', 'ignore')\
        .decode('utf-8')
