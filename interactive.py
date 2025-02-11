from flask import Flask, render_template, request, jsonify, send_file, Response
from astroquery.ipac.nexsci.nasa_exoplanet_archive import NasaExoplanetArchive
import numpy as np
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import simulations as simulations

app = Flask(__name__)

def retrieve_system_parameters(system_id):
    # Query the database and retrieve system parameters based on system ID
    parameters = NasaExoplanetArchive.query_criteria(table='pscomppars', where=f"pl_name='{str(system_id)}'")

    # Define a function to retrieve individual parameters or return default if not found
    def get_parameter(parameter_name, default_value):
        try:
            if len(parameters) == 1:
                try:
                    value = float(parameters[parameter_name][0].value)
                    if np.isnan(value):
                        return default_value
                    else: 
                        return value
                except:
                    value = float(parameters[parameter_name][0])
                    if np.isnan(value):
                        return default_value
                    else: 
                        return value
            else:
                raise ValueError("Multiple parameters found")
        except (KeyError, ValueError, TypeError):
            print(f"[INFO] Error occurred while retrieving parameter '{parameter_name}'. Defaulting to default value.")
            return default_value


    planet_name = system_id
    planet_mass = get_parameter('pl_bmassj', default_value=0.0)
    RpRs = get_parameter('pl_ratror', default_value=0.0)
    orbital_period = get_parameter('pl_orbper', default_value=0.0)
    semi_a = get_parameter('pl_orbsmax', default_value=0.0)
    star_mass = get_parameter('st_mass', default_value=0.0)
    orbital_inclination = get_parameter('pl_orbincl', default_value=0.0)
    eccentricity = get_parameter('pl_orbeccen', default_value=0.0)
    omega = get_parameter('pl_orblper', default_value=90.0)
    K = get_parameter('pl_rvamp', default_value=0.0) / 1000
    vsys = get_parameter('st_radv', default_value=0.0) 
    aRs = get_parameter('pl_ratdor', default_value=0.0)
    T14 = get_parameter('pl_trandur', default_value=0.0)

    # transitC = get_parameter('pl_tranmid', default_value=0.0)
    # period = get_parameter('pl_orbper', default_value=0.0)
    # ecc = get_parameter('pl_orbeccen', default_value=0.0)
    # omega = get_parameter('pl_orblper', default_value=0.0)
    # a = get_parameter('pl_orbsmax', default_value=0.0)
    # aRs = get_parameter('pl_ratdor', default_value=0.0)
    # orbinc = get_parameter('pl_orbincl', default_value=0.0)
    # vsini = get_parameter('st_vsin', default_value=0.0)
    # pob = get_parameter('pl_projobliq', default_value=0.0)
    # Ms = get_parameter('st_mass', default_value=0.0)
    
    # RpRs = get_parameter('pl_ratror', default_value=0.0)
    
    # #T14 = get_parameter('pl_trandur', default_value=0.0)
    # RA = get_parameter('ra', default_value=0.0)
    # DEC = get_parameter('dec', default_value=0.0)
    # n_exp = 100

    # Return the extracted values as a dictionary
    return {
        'planet_name': planet_name,
        #'planet_mass': planet_mass,
        'period': orbital_period,
        'ecc': eccentricity,
        'omega': omega,
        #'a': semi_a,
        'aRs': aRs,
        'orbinc': orbital_inclination,
        #'vsini': vsini,
        #'pob': pob,
        #'Ms': star_mass,
        #'Mp': planet_mass,
        'RpRs': RpRs,
        'K': K,
        'vsys': vsys,
        'T14': T14,
        'yerr_lc': 4e-3,
        'yerr_rv': 10
        # 'RA': RA,
        # 'DEC': DEC,
        # 'n_exp': n_exp,
        # 'obs': obs,
        # 'RF': RF
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_parameters', methods=['POST'])
def get_parameters():
    system_id = request.form['system_id']
    system_parameters = retrieve_system_parameters(system_id)

    #print(f"Raw system_parameters: {system_parameters}")  # Debugging step

    #try:
    # Manually serialize with full precision
    response_data = json.dumps(system_parameters, indent=2, ensure_ascii=False, allow_nan=True)

    # Return response as JSON with correct content type
    return Response(response_data, mimetype='application/json')



@app.route('/plot', methods=['POST'])
def plot():
    input_values = request.json['input_values']

    input_values = {key: value for key, value in input_values.items()}

    times, lc, lc_sim = simulations.lightcurve(input_values) # note that this is a dictionary 
    times_rv, rv, rv_sim = simulations.rvcurve(input_values)

    fig = make_subplots(
        rows=1, cols=2,  # 1 row, 2 columns
        subplot_titles=("Transit lightcurve", "Radial velocity curve")  # Titles for each panel
    )

    # Add traces to each subplot
    fig.add_trace(
        go.Scatter(x=list(times), y=list(lc), mode='lines', name='Transit model'),
        row=1, col=1  # Add to the first subplot
    )

    fig.add_trace(
        go.Scatter(x=list(times_rv), y=list(rv), mode='lines', name='RV model'),
        row=1, col=2  # Add to the first subplot
    )

    fig.add_trace(
        go.Scatter(
            x=list(times),
            y=list(lc_sim),
            mode='markers',
            name='Simulated transit observation',
            marker=dict(
                color='rgba(0, 0, 0, 0.5)',  # Example color with alpha (RGBA)
                size=3  # Optional: adjust marker size
            )
        ),
        row=1, col=1  # Add to the second subplot
    )

    fig.add_trace(
        go.Scatter(
            x=list(times_rv),
            y=list(rv_sim),
            mode='markers',
            name='Simulated RV observation',
            marker=dict(
                color='rgba(0, 0, 0, 0.8)',  # Example color with alpha (RGBA)
                size=3  # Optional: adjust marker size
            )
        ),
        row=1, col=2  # Add to the second subplot
    )

    fig.update_layout(
        xaxis=dict(
            title="Time [h]",  # X-axis title for the left plot
        ),
        yaxis=dict(
            title="Relative Flux",  # Y-axis title for the left plot
        ),
        xaxis2=dict(
            title="Orbital phase",  # X-axis title for the right plot (can be different if needed)
        ),
        yaxis2=dict(
            title="RV [km/s]",  # Y-axis title for the right plot (can be different if needed)
        ),
        )


    # phases = rv.true_phases.tolist()
    # RVs_RM = rv.RVs_RM.tolist()
    # transit_sorted = rv.transit_sorted.tolist()
    # RVs_planet = rv.RVs_planet.value.tolist()
    # RVs_star = rv.RVs_star.tolist()
    # RVs_tel = rv.RVs_tel.tolist()
    times = times.tolist()
    lc = lc.tolist()

    return jsonify({
        'plot': fig.to_dict(),
        'times': times,
        'lightcurve': lc
        # 'phases': phases,
        # 'RVs_RM': RVs_RM,
        # 'transit_sorted': transit_sorted,
        # 'RVs_planet': RVs_planet,
        # 'RVs_star': RVs_star,
        # 'RVs_tel': RVs_tel
    })


if __name__ == '__main__':
    app.run(debug=True, port=5022)