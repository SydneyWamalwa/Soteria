from flask import Flask, render_template, redirect, url_for, flash, session
from config import Config
from models import db, User, EcoAction
from PIL import Image, ImageDraw, ImageFont
from forms import RegistrationForm, EcoActionForm, LoginForm
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os


# Tier assignment based on Planet Credits

def assign_tier(user):
    pc = user.planet_credits
    if pc < 500:
        return 'Nomad'
    elif pc < 10000:
        return 'Citizen'
    elif pc < 50000:
        return 'Steward'
    else:
        return 'Elder'

# Details for each position
position_details = {
    'Nomad': {
        'requirements': 'Email verification + basic identity',
        'privileges': 'Limited identity services, trial missions',
        'responsibilities': 'Adherence to community standards'
    },
    'Citizen': {
        'requirements': 'Verified DID + earn minimum 500 PCs',
        'privileges': 'DAO voting rights, SS stipend, full mission access',
        'responsibilities': 'Regular participation, validation duties'
    },
    'Steward': {
        'requirements': '≥10,000 PCs + community approval + knowledge assessment',
        'privileges': 'Propose new mission types, council eligibility, advanced governance weight',
        'responsibilities': 'Mentorship of new citizens, development of mission frameworks'
    },
    'Elder': {
        'requirements': '≥50,000 PCs + 3 years active citizenship + significant contributions',
        'privileges': 'Emergency council eligibility, diplomatic representation, strategy consultation',
        'responsibilities': 'Knowledge preservation, dispute resolution, external relationship management'
    },
    'Steward & Founding Architect of Soteria': {
        'requirements': 'Founding member and chief architect',
        'privileges': 'System-level governance authority, Protocol design rights',
        'responsibilities': 'Network stewardship, Core protocol maintenance'
    }
}

def generate_certificate(user):
    try:
        # Define consistent certificate dimensions
        cert_width = 1200  # Changed to match actual image size
        cert_height = 900

        # Create certificate directory if it doesn't exist
        os.makedirs('static/certificates', exist_ok=True)

        # Load parchment texture with proper dimensions
        try:
            texture = Image.open('static/images/parchment_texture.jpg').convert('RGB')
            texture = texture.resize((cert_width, cert_height))  # Use variables
        except Exception as e:
            print(f"Error loading texture: {e}")
            texture = Image.new('RGB', (cert_width, cert_height), color=(245, 230, 200))

        # Create main certificate image with texture background
        cert = texture.copy()
        draw = ImageDraw.Draw(cert)

        # Add vintage overlay with proper dimensions
        overlay = Image.new('RGBA', (cert_width, cert_height), (245, 220, 180, 15))
        cert.paste(overlay, (0, 0), overlay)

        # Load fonts with fallbacks
        try:
            title_font = ImageFont.truetype('static/fonts/GreatVibes-Regular.ttf', 90)
            name_font = ImageFont.truetype('static/fonts/PlayfairDisplay-Bold.ttf', 60)
            subtitle_font = ImageFont.truetype('static/fonts/Roboto-Regular.ttf', 35)
            body_font = ImageFont.truetype('static/fonts/Roboto-Regular.ttf', 40)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            body_font = ImageFont.load_default()

        # Draw decorative border using variables
        border_width = 15
        draw.rectangle([border_width, border_width, cert_width-border_width, cert_height-border_width],
                      outline=(150, 110, 90), width=border_width)

        # Handle court of arms positioning
        try:
            court_size = 300
            court_of_arms = Image.open('static/images/Court_of_Arms.png').convert('RGBA').resize((court_size, court_size))
            cert.paste(court_of_arms, (cert_width//2 - court_size//2, 50), court_of_arms)
        except Exception as e:
            print(f"Error loading court of arms: {e}")
            coa_text = "Soteria Collective"
            text_width = draw.textlength(coa_text, font=title_font)
            draw.text((cert_width//2 - text_width//2, 100), coa_text,
                     font=title_font, fill=(150, 110, 90))

        # Center title text
        title_text = "Certificate of Citizenship"
        text_width = draw.textlength(title_text, font=title_font)
        draw.text((cert_width//2 - text_width//2, 350), title_text,
                 font=title_font, fill=(100, 70, 50))

        # Main content container with dynamic positioning
        content_y = 450
        line_height = 60

        # This certifies that
        certify_text = "This certifies that"
        text_width = draw.textlength(certify_text, font=subtitle_font)
        draw.text((cert_width//2 - text_width//2, content_y), certify_text,
                 font=subtitle_font, fill=(120, 90, 70))
        content_y += line_height + 20

        # User name
        name_text = user.name
        text_width = draw.textlength(name_text, font=name_font)
        draw.text((cert_width//2 - text_width//2, content_y), name_text,
                 font=name_font, fill=(80, 50, 30))
        content_y += line_height + 30

        # Position text with wrapping
        position_text = f"Has been admitted as a {user.position} of Soteria"
        max_width = cert_width - 200  # 100px margins on both sides
        lines = []
        current_line = []

        for word in position_text.split():
            test_line = ' '.join(current_line + [word])
            test_width = draw.textlength(test_line, font=body_font)
            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))

        # Draw wrapped lines
        line_height = 50
        current_y = content_y
        for line in lines:
            text_width = draw.textlength(line, font=body_font)
            draw.text((cert_width//2 - text_width//2, current_y),
                     line, font=body_font, fill=(100, 70, 50))
            current_y += line_height

        # Soteria ID
        id_y = current_y + 40
        id_text = f"Soteria ID: {user.soteria_id}"
        text_width = draw.textlength(id_text, font=subtitle_font)
        draw.text((cert_width//2 - text_width//2, id_y), id_text,
                 font=subtitle_font, fill=(120, 90, 70))

        # Adjust decorative line position (move down 50px)
        line_y = id_y + 60  # 60px below ID
        draw.line([(cert_width//2 - 200, line_y),
                 (cert_width//2 + 200, line_y)],
                 fill=(150, 110, 90), width=3)

        # Founder section (signature + text)
        signature_y = line_y + 40  # 40px below line
        try:
            signature_width = 250
            signature_height = 120
            signature = Image.open('static/images/signature.png').convert('RGBA')
            signature = signature.resize((signature_width, signature_height))
            cert.paste(signature, (cert_width//2 - signature_width//2, signature_y), signature)
        except Exception as e:
            print(f"Error loading signature: {e}")
            draw.text((cert_width//2 - 100, signature_y), "Authorized Signature",
                     font=subtitle_font, fill=(150, 110, 90))

        # Save certificate
        certificate_filename = f'user_certificate_{user.id}.png'
        certificate_path = f'static/certificates/{certificate_filename}'
        cert.save(certificate_path)

        # Update user record
        user.certificate_path = certificate_filename
        db.session.commit()

        return certificate_path

    except Exception as e:
        print(f"Error generating certificate: {e}")
        return None

def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

# Create Flask app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()

        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password, form.password.data):
                session['user_id'] = user.id
                flash('Logged in successfully!', 'success')
                return redirect(url_for('info'))
            else:
                flash('Invalid email or password.', 'danger')
                return redirect(url_for('login'))

        return render_template('login.html', form=form)


    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()

        if form.validate_on_submit():
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered. Please login or use a different email.', 'danger')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(form.password.data)
            user = User(name=form.name.data, email=form.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
            flash('Registered successfully!', 'success')
            session['user_id'] = user.id
            return redirect(url_for('info'))

        return render_template('register.html', form=form)



    @app.route('/info')
    def info():
        return render_template('info.html')

    # Open citizenship application for all registered users
    @app.route('/apply', methods=['GET', 'POST'])
    def apply_citizenship():
        if 'user_id' not in session:
            return redirect(url_for('register'))

        user = User.query.get(session['user_id'])
        if user is None:
            flash('User not found. Please register again.', 'danger')
            return redirect(url_for('register'))

        # Rest of your logic
        user.is_citizen = True
        user.soteria_id = f"SOT-{user.id:04d}"
        user.position = 'Steward & Founding Architect of Soteria' if user.email == 'sydneywamalwa@gmail.com' else assign_tier(user)
        user.image_url = url_for('static', filename='images/Sydney.jpg')
        generate_certificate(user)
        db.session.commit()
        flash('Congratulations! You are now a citizen of Soteria.', 'success')
        return redirect(url_for('certificate'))


    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('register'))
        user = User.query.get(session['user_id'])
        form = EcoActionForm()
        return render_template('dashboard.html', user=user, form=form)

    @app.route('/log', methods=['POST'])
    def log_action():
        if 'user_id' not in session:
            return redirect(url_for('register'))
        user = User.query.get(session['user_id'])
        form = EcoActionForm()
        if form.validate_on_submit():
            action = EcoAction(description=form.description.data, points=form.points.data, user=user)
            user.planet_credits += form.points.data
            db.session.add(action)
            db.session.commit()
            flash('Eco-action recorded!', 'success')
        else:
            flash('Invalid input', 'danger')
        return redirect(url_for('dashboard'))

    @app.route('/certificate')
    def certificate():
        if 'user_id' not in session:
            return redirect(url_for('register'))

        user = User.query.get(session['user_id'])
        if not user.is_citizen:
            return redirect(url_for('apply_citizenship'))

        # Generate or get existing certificate
        if not user.certificate_path or not os.path.exists(f'static/{user.certificate_path}'):
            cert_path = generate_certificate(user)
        else:
            cert_path = user.certificate_path

        if not cert_path:
            flash('Error generating certificate', 'danger')
            return redirect(url_for('dashboard'))

        details = position_details.get(user.position, position_details['Citizen'])
        return render_template('certificate.html',
                            user=user,
                            details=details,
                            cert_path=cert_path)


    with app.app_context():
        db.create_all()
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
