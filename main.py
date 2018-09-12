
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
import reverse_geocoder as rg
from geopy import distance
from geopy.geocoders import Nominatim
import requests
import time


app = Flask(__name__)

ask = Ask(app, "/space_walk")


def find_ordinals(city, iss):
    ''' 
    Take tuple coordinates (lat, lon) for City and ISS and
    find the cardinal direction of NE, SE, SW, NW
    '''

    if iss[0] - city[0] > 0:
        a = 'North'
    else:
        a = 'South'

    if iss[1] - city[1] > 0:
        b = 'East'
    else:
        b = 'West'
    return ''.join([a, b])


def where_is_the_iss_now():
    iss_now_website = 'http://api.open-notify.org/iss-now.json'
    webby = requests.get(iss_now_website)
    data = webby.json()

    if data['iss_position']:
        longitude = data['iss_position'].get('longitude')
        latitude = data['iss_position'].get('latitude')

    results = rg.search((latitude, longitude), mode=1)

    lat, lon, name, admin1, admin2, cc = results[0].values()

    ordinal = find_ordinals(city=(float(lat), float(lon)), iss=(float(latitude), float(longitude)))

    country_cc = requests.get(
        'https://pkgstore.datahub.io/core/country-list/data_json/data/8c458f2d15d9f2119654b29ede6e45b8/data_json.json')
    country_cc = country_cc.json()

    iss_coordinates = (latitude, longitude)
    k_nearest_coordinates = (lat, lon)
    distance_miles = distance.distance(k_nearest_coordinates, iss_coordinates).miles

    country_name = ''
    for i in filter(lambda d: d.get('Code') == cc, country_cc):
        country_name = i.get('Name')

    location_text = ', '.join([name, admin1, country_name])

    if distance_miles > 150:
        answer = 'The International Space Station is {} miles {} off the coast of {}'.format(int(distance_miles), ordinal,
                                                                                          location_text)
    else:
        answer = 'the International Space Station is {} miles {} near {}'.format(int(distance_miles),ordinal, location_text)
    return answer, latitude, longitude, distance_miles, ordinal, name, admin1, country_name


@app.route('/')
def homepage():
    return ''


@ask.launch
def start_skill():
    # welcome_message = 'Welcome to the Fleet Feet Journal!  What is your name?'

    welcome_message_reprompt = render_template('welcome_message_reprompt')
    welcome_message = render_template('welcome_message')
    return (question(welcome_message).reprompt(welcome_message_reprompt))


@ask.intent('YourLocation')
def pass_over(my_location):

    geolocator = Nominatim(user_agent='my-application')
    print(my_location)
    location = geolocator.geocode(my_location,language='en-US')
    try:
        city = location.address.split(',')[0]
        state = location.address.split(',')[2]
        country = location.address.split(',')[-1]
        location_name = ', '.join([city, state, country])
    except IndexError:
        location_name = location.address.split(',')[-1]

    fly_over = requests.get(
        'http://api.open-notify.org/iss-pass.json?lat={}&lon={}'.format(location.latitude, location.longitude))
    fly_over = fly_over.json()

    if fly_over['message'] == 'success':
        rise = fly_over['response'][0]
        answer = time.strftime('%A, %B %d, %Y at %I:%M %p GMT', time.localtime(rise.get('risetime')))
        a = rise.get('risetime')  # last epoch recorded
        b = time.time()  # current epoch time
        c = a - b  # returns seconds
        hours = c // 3600 % 24
        minutes = c // 60 % 60
        minutes = int(minutes)
        hours = int(hours)

        if minutes == 1:
            minorminutes = 'minute'
        else: minorminutes = 'minutes'

        if hours == 1:
            hour_or_hours = 'hour'
        else: hour_or_hours = 'hours'

        if hours == 0:
            time_til_rise = "{} {}".format(minutes, minorminutes)
        else: time_til_rise = "{} {} and {} {}".format(hours, hour_or_hours,  minutes, minorminutes)

    else:
        answer = "failure"
    return statement('the next flyover for {} will begin in {} on {}'.format(location_name, time_til_rise, answer))


@ask.intent('WhereISS')
def share_location():

    iss_location, latitude, longitude, distance_miles, ordinal, name, admin1, country_name= where_is_the_iss_now()
    latitude, longitude, distance_miles = float(latitude), float(longitude), float(distance_miles)
    return statement(iss_location).standard_card(
        title="Location of the International Space Station",
        text='Latitude {} and Longitude {},\n {} miles {} of {}, {} in {}'.format(round(latitude,2), round(longitude,2), round(distance_miles,0), ordinal, name, admin1, country_name))


@ask.intent('AMAZON.FallbackIntent')
def fallback():
    to_continue = render_template('to_continue')
    return question('Sorry, I am not sure what you asked me...{}'.format(to_continue))


@ask.intent('AMAZON.NavigateHomeIntent')
def go_home():
    return question('et - phone home')


@ask.intent('AMAZON.HelpIntent')
def help_me():
    help_me_text = render_template('help')
    return question(help_me_text)


@ask.intent('Credits')
def speak_credits():
    credits_ = render_template('credits')
    return statement(credits_)


@ask.intent('AMAZON.StopIntent')
def stop():
    bye_text = render_template('bye')
    return statement(bye_text)


@ask.intent('AMAZON.CancelIntent')
def cancel():
    bye_text = render_template('bye')
    return statement(bye_text)


@ask.session_ended
def session_ended():
    return "{}", 200


if __name__ == '__main__':
    app.run(debug=True)





