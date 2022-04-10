#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from models import  app, moment, db, Booking, Venue, Artist
from flask import render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate


#----------------------------------------------------------------------------#
# DB Migrate.
#----------------------------------------------------------------------------#

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  #Select all the venues
  venues = Venue.query.all()

  # Initialize the data
  data = []

  #Iterate over all the venues returned
  for venue in venues:
    notFound = True
    #Iterate over previously returned venues and added in response, then check if the city and state is already present
    for dt in data:
      # Convert City in upper case for comparison
      if (dt["city"].upper() == venue.city.upper() and dt["state"] == venue.state):
        notFound = False
        #City, State found append venue to the already added city, state
        dt["venues"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(venue.artists) # Upcoming shows are count of the artist who have booked the venue
      })
    
    #If the city, state not found add a fresh entry in the response
    if notFound:
      item = {
        "city": venue.city, 
        "state": venue.state,
        "venues": [{
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(venue.artists)  
        }]
      }
      data.append(item)
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  #Get the search term
  searchTerm=request.form.get('search_term', '')

  #Create the query term to be used in SQLAlchemy ORM query
  queryTerm = '%' + searchTerm + '%'
  
  #Use ilike for case insenstive search
  venues = Venue.query.filter(Venue.name.ilike(queryTerm)).all()

  # Initialize data
  data = []

  #Iterate through all the venues and found to massage the output in given format
  for venue in venues:
    for dt in venue.artists:
      upcoming_shows_count = 0
      if (dt.start_time >= datetime.now()):
          upcoming_shows_count = upcoming_shows_count + 1

    dt = {
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': len(venue.artists)
    }
    print(dt)
    data.append(dt)
  
  # Create the response to send back
  response={
    "count": len(venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=searchTerm)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  
  #Get the venue by passed venue_id
  venue = Venue.query.get(venue_id)

  #Initialization
  upcoming_shows = []
  upcoming_shows_count = 0
  past_shows = []
  past_shows_count = 0

  #Iterate over all the artist who have booked the venue
  for dt in venue.artists:
    artist = {
        'artist_id': dt.artist.id,
        'artist_name': dt.artist.name,
        'artist_image_link': dt.artist.image_link,
        'start_time': str(dt.start_time)
      }
    # Check if the start time is greater than current time or less
    if (dt.start_time >= datetime.now()):
      
      upcoming_shows.append(artist)
      upcoming_shows_count = upcoming_shows_count + 1
    else:
      past_shows.append(artist)
      past_shows_count = past_shows_count + 1

  #Create the response to be returned back
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count,
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  try:
    
    # As seeking_talent is only returned if it is explicitly set by the user, hence checking that if it found or not and set the seeking_talent value accordingly.
    seeking_talent = True if 'seeking_talent' in request.form else False

    

    venue = Venue(name=request.form['name'], 
                  city=request.form['city'],
                  state=request.form['state'],
                  address=request.form['address'],
                  phone=request.form['phone'],
                  genres=request.form.getlist('genres'),
                  image_link=request.form['image_link'],
                  facebook_link=request.form['facebook_link'],
                  website_link=request.form['website_link'],
                  seeking_talent=seeking_talent,
                  seeking_description=request.form['seeking_description']
                  )
                  
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    # on error while doing db insert, flash failure
    flash('There was a error while listing Venue ' + request.form['name'] + '!')
    db.session.rollback()
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  
  try:
    # Get venue by venue_id
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # Get all the artists
  artists = Artist.query.all()

  # Initialize
  data = []

  #Iterate over all the artist and massage the input to create the response
  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    })
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # Get the search term
  searchTerm = request.form.get('search_term', '')

  #Create the query term to be used in SQLAlchemy ORM query
  queryTerm = '%' + searchTerm + '%'
  
  #Use ilike for case insenstive search
  artists = Artist.query.filter(Artist.name.ilike(queryTerm)).all()
  data = []
  for artist in artists:
    upcoming_shows_count = 0
    for dt in artist.venues:
      if (dt.start_time >= datetime.now()):
          upcoming_shows_count = upcoming_shows_count + 1

    data.append({ 
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': 1
    })
  
  # Create the response to be send back
  response={
    "count": len(artists),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=searchTerm)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  
  # Get the artist from artist_id
  artist = Artist.query.get(artist_id)

  #Initializations
  upcoming_shows = []
  upcoming_shows_count = 0
  past_shows = []
  past_shows_count = 0

  #Iterate over all the venue which are booked by an artist
  for dt in artist.venues:
    venue = {
        'venue_id': dt.venue.id,
        'venue_name': dt.venue.name,
        'venue_image_link': dt.venue.image_link,
        'start_time': str(dt.start_time)
      }

    if (dt.start_time >= datetime.now()):
      
      upcoming_shows.append(venue)
      upcoming_shows_count = upcoming_shows_count + 1
    else:
      past_shows.append(venue)
      past_shows_count = past_shows_count + 1
  
  #Create the response for the artist
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": past_shows_count,
    "upcoming_shows_count": upcoming_shows_count,
  }
  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  # Get the artist from the artist_id
  artist = Artist.query.get(artist_id)

  #Create the data to be send and used by Jinja Template
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
  }
  
  #Set the artist genres to what has been retrieved from DB
  form.genres.default = artist.genres

  #Set the seeking_venue flag to what has been retrieved from DB
  if artist.seeking_venue:
    form.seeking_venue.default = True
  else:
    form.seeking_venue.default = False
  
  form.process()
  
  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  
  try:
    
    #Get the artist from artist_id
    artist = Artist.query.get(artist_id)

    #Set the fields retreived from the form
    artist.name = request.form['name']
    artist.genres = request.form.getlist('genres')
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.website_link = request.form['website_link']
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    
    if 'seeking_venue' in request.form:
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False
    
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  
  # Get the venue from venue_id
  venue = Venue.query.get(venue_id)
  form = VenueForm()
  
  # Creating data to be used by Jinja Template
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
  }
  
  # Setting the form defaults for genres and seeking_talent
  form.genres.default = venue.genres

  if venue.seeking_talent:
    form.seeking_talent.default = True
  else:
    form.seeking_talent.default = False
  
  form.process()
  
  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  
  try:
    #Get the venue from Venue_ID
    venue = Venue.query.get(venue_id)

    # Set the values as per the values returned from the form
    venue.name = request.form['name']
    venue.genres = request.form.getlist('genres')
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.website_link = request.form['website_link']
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    
    if 'seeking_talent' in request.form:
      venue.seeking_talent = True
      venue.seeking_description = request.form['seeking_description']
    else:
      venue.seeking_talent = False
      # If the seeking_talent is False, then intialize this field as well
      venue.seeking_description = ''

    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()



  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  
  try:
    # As seeking_talent is only returned if it is explicitly set by the user, hence checking that if it found and if not using that in the object to avoid key error.
    seeking_venue = True if 'seeking_venue' in request.form else False

    artist = Artist(name=request.form['name'], 
                  city=request.form['city'],
                  state=request.form['state'],
                  phone=request.form['phone'],
                  genres=request.form.getlist('genres'),
                  image_link=request.form['image_link'],
                  facebook_link=request.form['facebook_link'],
                  website_link=request.form['website_link'],
                  seeking_venue=seeking_venue,
                  seeking_description=request.form['seeking_description']
                  )

    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except:
    # on error while doing db insert, flash failure
    flash('There was a error while listing Artist ' + request.form['name'] + '!')
    db.session.rollback()

  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  
  # Get all the bookings
  bookings = Booking.query.all()

  #Initialize
  data = []

  #Iterate over all the bookings and massage the data in the required format
  for booking in bookings:
    data.append({
      'venue_id': booking.venue.id,
      'venue_name': booking.venue.name,
      'artist_id': booking.artist.id,
      'artist_name': booking.artist.name,
      'artist_image_link': booking.artist.image_link,
      'start_time': str(booking.start_time)
    })
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  try:
    # Create a booking object to insert row into Booking table
    booking = Booking(venue_id=request.form['venue_id'], 
                  artist_id=request.form['artist_id'],
                  start_time=request.form['start_time']
                  )

    db.session.add(booking)
    db.session.commit()
     # on successful db insert, flash success
    flash('Show was successfully listed!')

  except:
    # on error while doing db insert, flash failure
    flash('There was a error while listing Show!')
    db.session.rollback()

  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
