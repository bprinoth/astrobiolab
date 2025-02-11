import radvel
import batman
import numpy as np





def lightcurve(input_values):

    params = batman.TransitParams()
    params.t0 = 0.                                  #time of inferior conjunction
    params.per = float(input_values['period'])      #orbital period in days
    params.rp = float(input_values['RpRs'])         #RpRs
    params.a = float(input_values['aRs'])           #scaled semi-major axis
    params.inc = float(input_values['orbinc'])      #orbital inclination in degrees
    params.ecc = float(input_values['ecc'])         #orbital eccentricity
    params.limb_dark = "nonlinear"                  #limb darkening model
    params.u = [0.5, 0.1, 0.1, -0.1]                #limb darkening coefficients [u1, u2, u3, u4]

    #argument of periastron
    if params.ecc == 0.:
        params.w = 90. #argument of periastron, catches weird database errors
    else:
        params.w = float(input_values['omega'])     

    T14 = (float(input_values['T14']) + 0.5) / 24 # making sure this is in days
    t = np.linspace(-T14/2, T14/2, 1000) # this needs to be in units of days. roughly 30 min baseline

    m = batman.TransitModel(params, t)
    flux = m.light_curve(params)

    
    yerr_trans = float(input_values['yerr_lc']) #assuming we know the Gaussian uncertainty
    y_trans = flux + yerr_trans * np.random.randn(len(flux))

    return t * 24, flux, y_trans # return in hours



def rvcurve(input_values):
    
    t = np.linspace(-float(input_values['period'])/2, float(input_values['period'])/2, 1000)

    synth_params = radvel.Parameters(1,basis='per tc e w k')
    synth_params['per1'] = radvel.Parameter(value = float(input_values['period']))
    synth_params['tc1'] = radvel.Parameter(value = 0.)
    synth_params['e1'] = radvel.Parameter(value = float(input_values['ecc'])) # eccentricity

    if synth_params['e1'] == 0.:
        synth_params['w1'] = radvel.Parameter(value = 90.0)
    else:
        synth_params['w1'] = radvel.Parameter(value = float(input_values['omega']))
    
    synth_params['k1'] = radvel.Parameter(value = float(input_values['K']) * 1000)

    synth_params['dvdt'] = radvel.Parameter(value=0)
    synth_params['curv'] = radvel.Parameter(value=0)

    synth_model = radvel.RVModel(params=synth_params)
    
    yerr_rv = float(input_values['yerr_rv'])
    y_rv = synth_model(t)
    y_rv += yerr_rv * np.random.randn(len(y_rv))       
    y_rv += (float(input_values['vsys']) * 1000)  

    return t, (synth_model(t) + float(input_values['vsys']) * 1000) / 1000, y_rv / 1000
