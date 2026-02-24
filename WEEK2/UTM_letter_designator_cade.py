import numpy as np
import sys

def _UTMLetterDesignator(Lat):
    # This routine determines the correct UTM letter designator
    # for the given latitude
    # returns 'Z' if latitude is outside the UTM limits of 84N to 80S
    # Written by Chuck Gantz- chuck.gantz@globalstar.com

    if 84 >= Lat >= 72:
        return 'X'
    elif 72 > Lat >= 64:
        return 'W'
    elif 64 > Lat >= 56:
        return 'V'
    elif 56 > Lat >= 48:
        return 'U'
    elif 48 > Lat >= 40:
        return 'T'
    elif 40 > Lat >= 32:
        return 'S'
    elif 32 > Lat >= 24:
        return 'R'
    elif 24 > Lat >= 16:
        return 'Q'
    elif 16 > Lat >= 8:
        return 'P'
    elif 8 > Lat >= 0:
        return 'N'
    elif 0 > Lat >= -8:
        return 'M'
    elif -8 > Lat >= -16:
        return 'L'
    elif -16 > Lat >= -24:
        return 'K'
    elif -24 > Lat >= -32:
        return 'J'
    elif -32 > Lat >= -40:
        return 'H'
    elif -40 > Lat >= -48:
        return 'G'
    elif -48 > Lat >= -56:
        return 'F'
    elif -56 > Lat >= -64:
        return 'E'
    elif -64 > Lat >= -72:
        return 'D'
    elif -72 > Lat >= -80:
        return 'C'
    else:
        return 'Z'  # if the Latitude is outside the UTM limits
import numpy as np
import sys

def UTM_letter_designator(lat):
    """
    Calculates the UTM designation
    Args:
        lat: latitude between -90 and 90 (string)
        
    Returns:
        'UTM letter designator: val'

    Usage: python /path/UTM_letter_designator_cade.py 56
    """
    lat = float(lat) #converts back into
    designators = ['X', 'W', 'V', 'U','T','S','R','Q','P', 'N', 'M', 
                   'L', 'K','J','H','G', 'F','E','D','C'] #UTM letter designators
    upper_bound = np.array([84,72,64,56,48,40,32,24,16,8,0,-8,-16,-24,-32,-40,-48,-56,
                   -64, -72]) #upper bounds for UTM limits
    lower_bound = upper_bound - 8 #lower bounds for UTM limits

    for i in range(len(designators)):
        if lat> np.max(upper_bound) or lat<np.min(lower_bound): #outside the bounds of UTM
            return 'Z' 
        else:
            if upper_bound[i] > lat >= lower_bound[i]: # for all lats in UTM bounds
                return designators[i]

if __name__ == '__main__':
    if len(sys.argv) == 2:
        result = UTM_letter_designator(sys.argv[1])
        print('UTM letter designator:', result)

