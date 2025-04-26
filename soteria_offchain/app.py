from flask import Flask, render_template, redirect, url_for, flash, session, request
from config import Config
from models import db, User, EcoAction, EcoActionReview
from PIL import Image, ImageDraw, ImageFont
from forms import RegistrationForm, EcoActionForm, LoginForm
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_login import (
    LoginManager,
    current_user,
    login_user,
    logout_user,
    login_required
)
from sqlalchemy import exists
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists
from datetime import datetime
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}


# Initialize LoginManager
login_manager = LoginManager()
login_manager.login_view = 'login'

# Utility function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_current_user():
    return current_user

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

# Create Flask app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Routes
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
                login_user(user)  # Now properly imported
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Invalid email or password.', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()  # Don't forget to import this too
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))

            user = User(
                name=form.name.data,
                email=form.email.data,
                password=generate_password_hash(form.password.data)
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('dashboard'))
        return render_template('register.html', form=form)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html', user=current_user, form=EcoActionForm())

    @app.route('/log', methods=['POST'])
    @login_required
    def log_action():
        form = EcoActionForm()

        if form.validate_on_submit():
            try:
                # Handle file upload for proof photo if present
                proof_photo = None
                if 'proof_photo' in request.files:
                    file = request.files['proof_photo']
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        proof_photo = os.path.join('static/uploads', filename)
                        file.save(proof_photo)

                # Geo-location data (if provided) from the form
                geo_location = form.geo_location.data if form.geo_location.data else None

                # Create the EcoAction object
                action = EcoAction(
                    description=form.description.data,
                    points=form.points.data,
                    user_id=current_user.id,
                    proof_photo=proof_photo,
                    geo_location=geo_location
                )

                # Update the user's planet credits
                current_user.planet_credits += form.points.data

                # Commit the transaction
                db.session.add(action)
                db.session.commit()

                flash('Eco-action recorded successfully!', 'success')
            except Exception as e:
                # Rollback if something goes wrong
                db.session.rollback()
                flash(f'Error: {str(e)}. Please try again later.', 'danger')
                app.logger.error(f"Error logging eco-action: {str(e)}")

        else:
            flash('Invalid input. Please check your form data.', 'danger')

        return redirect(url_for('dashboard'))

    @app.route('/apply', methods=['GET', 'POST'])
    @login_required
    def apply_citizenship():
        if current_user.is_citizen:
            return redirect(url_for('certificate'))

        current_user.is_citizen = True
        current_user.soteria_id = f"SOT-{current_user.id:04d}"
        current_user.position = 'Steward & Founding Architect of Soteria' \
            if current_user.email == 'sydneywamalwa@gmail.com' else assign_tier(current_user)

        generate_certificate(current_user)
        db.session.commit()
        flash('Citizenship granted!', 'success')
        return redirect(url_for('certificate'))

    @app.route('/certificate')
    @login_required
    def certificate():
        if not current_user.is_citizen:
            flash('Complete citizenship application first', 'warning')
            return redirect(url_for('apply_citizenship'))

        cert_path = current_user.certificate_path
        if not cert_path or not os.path.exists(f'static/{cert_path}'):
            cert_path = generate_certificate(current_user)

        details = position_details.get(current_user.position, position_details['Citizen'])
        return render_template('certificate.html',
                            user=current_user,
                            details=details,
                            cert_path=cert_path)

    @app.route('/review_actions')
    @login_required
    def review_actions():
        page = request.args.get('page', 1, type=int)
        per_page = 10

        # Query for actions needing review
        reviewed_subquery = exists().where(
            EcoActionReview.eco_action_id == EcoAction.id,
            EcoActionReview.reviewer_id == current_user.id
        )

        actions = EcoAction.query.filter(
            EcoAction.status == 'Pending',
            ~reviewed_subquery
        ).paginate(page=page, per_page=per_page, error_out=False)

        return render_template('review_actions.html',
                            actions=actions.items,
                            pagination=actions)

    @app.route('/review/<int:action_id>/<decision>')
    @login_required
    def review_action(action_id, decision):
        action = EcoAction.query.get_or_404(action_id)

        if action.status != 'Pending' or current_user in action.reviewers:
            flash('Invalid review action', 'danger')
            return redirect(url_for('review_actions'))

        # Create review record
        review = EcoActionReview(
            eco_action_id=action_id,
            reviewer_id=current_user.id,
            decision=decision
        )
        db.session.add(review)

        # Update counts
        action.reviewer_count += 1
        if decision == 'approve':
            action.approved_count += 1
        else:
            action.rejected_count += 1

        # Check consensus
        if action.reviewer_count >= 3:
            action.status = 'Approved' if action.approved_count >= 2 else 'Rejected'
            if action.status == 'Approved':
                action.user.planet_credits += action.points

        db.session.commit()
        return redirect(url_for('review_actions'))

    @app.route("/info")
    def info():
        return render_template("info.html")

    # Database initialization
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

