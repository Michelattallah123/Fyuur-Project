#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import func
from datetime import datetime



#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost:5432/fyuur'
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    venue_id = db.Column(db.Integer, primary_key=True)
    venue_name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(500))
    looking_for_talent = db.Column(db.Boolean, default=False)
    talent_description = db.Column(db.Text)
    genres = db.Column(db.String(120))


class Artist(db.Model):
    __tablename__ = 'Artist'

    artist_id = db.Column(db.Integer, primary_key=True)
    artist_name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    website = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    looking_for_venues = db.Column(db.Boolean, default=False)
    venues_description = db.Column(db.Text)



class Show(db.Model):
    __tablename__ = 'Show'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.venue_id'), nullable=False)
    venue = db.relationship(
        'Venue', backref=db.backref('shows', cascade='all, delete'))
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.artist_id'), nullable=False)
    artist = db.relationship(
        'Artist', backref=db.backref('shows', cascade='all, delete'))
    
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  locations = Venue.query.with_entities(Venue.city,Venue.state).group_by(Venue.city,Venue.state).all()
  data=[]
  for location in locations:
    venues = Venue.query.filter_by(city=location.city).filter_by(state=location.state).all()
    venues_info = []
    for venue in venues:
      venues_info.append({"id":venue.venue_id,"name":venue.venue_name})
    data.append({"city":location.city,"state":location.state,"venues":venues_info})
  return render_template('pages/venues.html',data=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
  response = Venue.query.filter(Venue.venue_name.ilike('%' + request.form.get('search_term','') + '%')).all()
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day,datetime.today().hour,datetime.today().minute,datetime.today().second)
  upcoming_shows = Show.query.join(Venue).join(Artist).with_entities(Show.date,Venue.venue_id, Venue.venue_name,Artist.artist_name,Artist.artist_id,Artist.genres,Artist.image_link).filter(Show.date>todays_datetime,Venue.venue_id==venue_id).all()
  old_shows = Show.query.join(Venue).join(Artist).with_entities(Show.date,Venue.venue_id, Venue.venue_name,Artist.artist_name,Artist.artist_id,Artist.genres,Artist.image_link).filter(Show.date<todays_datetime,Venue.venue_id==venue_id).all()
  data = Venue.query.get(venue_id)
  return render_template('pages/show_venue.html', venue = data , upcoming_shows = upcoming_shows, old_shows = old_shows)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  try:
    error=0
    name = request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    looking_for_talent = request.form.get('talent','')
    talent_description = request.form.get('description','')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link', '')
    image_link = request.form.get('image_link','')
    website = request.form.get('website','')
    if looking_for_talent=="1":
      logic=True
    else:
      logic=False
    venue = Venue(venue_name = name,talent_description=talent_description,looking_for_talent=logic,website = website,image_link = image_link, city = city, state = state, address=address, phone = phone, genres = genres, facebook_link=facebook_link)
    db.session.add(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error=1
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    if error==0:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    db.session.close()
  return redirect(url_for('venues'))

@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id) 
  db.session.delete(venue)
  db.session.commit()
  return redirect(url_for('venues'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  artists = Artist.query.filter(Artist.artist_name.ilike('%' + request.form.get('search_term','') + '%')).all()
  return render_template('pages/search_artists.html', results=artists, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day,datetime.today().hour,datetime.today().minute,datetime.today().second)
  upcoming_shows = Show.query.join(Venue).join(Artist).with_entities(Show.date,Venue.venue_id, Venue.venue_name,Artist.artist_name,Artist.image_link,Artist.artist_id,Artist.genres).filter(Show.date>todays_datetime,Artist.artist_id==artist_id).all()
  old_shows = Show.query.join(Venue).join(Artist).with_entities(Show.date,Venue.venue_id, Venue.venue_name,Artist.artist_name,Artist.image_link,Artist.artist_id,Artist.genres).filter(Show.date<todays_datetime,Artist.artist_id==artist_id).all()
  data = Artist.query.get(artist_id)
  return render_template('pages/show_artist.html', artist=data, upcoming_shows = upcoming_shows, old_shows = old_shows)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist= Artist.query.get(artist_id)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  artist.artist_name = request.form.get('name', '')
  artist.city = request.form.get('city', '')
  artist.state = request.form.get('state', '')
  artist.address = request.form.get('address', '')
  artist.phone = request.form.get('phone', '')
  artist.genres = request.form.getlist('genres')
  if request.form.get('talent','')=="1":
      artist.looking_for_venues=True
  else:
      artist.looking_for_venues=False
  artist.venues_description = request.form.get('description','')
  artist.facebook_link = request.form.get('facebook_link', '')
  artist.image_link = request.form.get('image_link','')
  artist.facebook_link = request.form.get('facebook_link','')
  artist.website = request.form.get('website','')
  db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue =Venue.query.get(venue_id)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  venue = Venue.query.get(venue_id)
  venue.venue_name = request.form.get('name', '')
  venue.city = request.form.get('city', '')
  venue.state = request.form.get('state', '')
  venue.address = request.form.get('address', '')
  looking_for_talent = request.form.get('talent','')
  if looking_for_talent=="1":
    logic=True
  else:
    logic=False
  venue.looking_for_talent=logic
  venue.talent_description = request.form.get('description','')
  venue.phone = request.form.get('phone', '')
  venue.genres = request.form.getlist('genres')
  venue.facebook_link = request.form.get('facebook_link', '')
  venue.image_link = request.form.get('image_link','')
  venue.website = request.form.get('website','')
  db.session.commit()
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
    error=0
    name = request.form.get('name', '')
    city = request.form.get('city', '')
    state = request.form.get('state', '')
    address = request.form.get('address', '')
    phone = request.form.get('phone', '')
    genres = request.form.getlist('genres')
    facebook_link = request.form.get('facebook_link', '')
    looking_for_venues = request.form.get('talent','')
    venues_description = request.form.get('description','')
    image_link = request.form.get('image_link','')
    facebook_link = request.form.get('facebook_link','')
    website = request.form.get('website','')
    if looking_for_venues=="1":
      logic=True
    else:
      logic=False
    artist = Artist(artist_name = name,venues_description=venues_description,looking_for_venues=logic,website = website,image_link = image_link, city = city, state = state, phone = phone, genres = genres, facebook_link=facebook_link)
    db.session.add(artist)
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred. Artist ' + artist.artist_name + ' could not be listed.')
    error=1
  finally:
    db.session.close()
    if error==0:
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    
  return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = Show.query.join(Venue).join(Artist).with_entities(Venue.venue_id, Venue.venue_name, Artist.artist_id, Artist.artist_name,
  Artist.image_link, Show.date).all()
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  try:
    artist_id = request.form.get('artist_id', '')
    venue_id = request.form.get('venue_id', '')
    start_time = request.form.get('start_time', '')
    show = Show(artist_id = artist_id, venue_id = venue_id, date = start_time)
    db.session.add(show)
    db.session.commit()
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
    flash('Show was successfully listed!')
  return redirect(url_for('shows'))

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
